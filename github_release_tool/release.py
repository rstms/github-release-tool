#!/usr/bin/env python3

# vi: ft=python

import json
import os
import re
from pathlib import Path
from subprocess import check_output

import github3

VERSION_PATTERN = r"^([0-9]+)\.([0-9]+)\.([0-9]+)(-.*){0,1}$"
WHEEL_PATTERN = r"^([a-z][a-z0-9_]+)-([0-9]+\.[0-9]+\.[0-9]+)-.+\.whl$"
JSON_PATTERN = r"^([a-z][a-z0-9_]+)-([0-9]+\.[0-9]+\.[0-9]+)-release\.json$"


class Release:
    def __init__(
        self,
        *,
        organization=None,
        repository=None,
        token=None,
        module_dir=None,
        wheel_dir=None,
        version=None,
        local=False,
    ):
        organization = organization or os.environ["GITHUB_ORGANIZATION"]
        repository = repository or os.environ.get(
            "GITHUB_REPO", Path(".").resolve().stem
        )
        token = token or os.environ["GITHUB_TOKEN"]
        self.version_pattern = re.compile(VERSION_PATTERN)
        self.wheel_pattern = re.compile(WHEEL_PATTERN)
        self.json_pattern = re.compile(JSON_PATTERN)
        self.gh = github3.GitHub(token=token)
        if not isinstance(self.gh, github3.GitHub):
            raise RuntimeError("token login failed")
        self.repo = self.gh.repository(organization, repository)
        if not isinstance(self.repo, github3.repos.repo.Repository):
            raise RuntimeError(
                f"repo lookup failed: {organization}/{repository}"
            )
        if module_dir:
            self.module_dir = Path(module_dir).resolve()
            if not (self.module_dir / "__init__.py").is_file():
                raise RuntimeError(
                    f"module_dir '{str(module_dir)}'"
                    " does not appear to be a python module"
                )
        else:
            self.module_dir = None
        self.wheel_dir = wheel_dir or Path("./dist").resolve()
        self.local = local
        if version in [None, "latest"]:
            self.version = self.latest_release_version()
        else:
            self.version = self._check_version(version)

    def _check_version(self, v, return_none=False):
        if v is not None:
            if v.startswith("v"):
                v = v[1:]
            if not self.version_pattern.match(v):
                if return_none:
                    return None
                raise SyntaxError(f"unrecognized version format '{v}'")
        if not isinstance(v, str):
            if return_none:
                return None
            raise TypeError(f"expected string-type, got '{v}'")
        return v

    def local_release_files(self, wheel=False):
        """return dict of json or wheel files from ./dist"""
        if wheel:
            pattern = self.wheel_pattern
        else:
            pattern = self.json_pattern

        self.wheel_dir = self.wheel_dir or Path("./dist").resolve()

        if not self.wheel_dir.is_dir():
            raise RuntimeError(
                f"WHEEL_DIR {str(self.wheel_dir)} is not a directory"
            )

        ret = {}
        for _file in [e for e in self.wheel_dir.iterdir() if e.is_file()]:
            match = pattern.match(_file.name)
            if match:
                module, version = match.groups()[:2]
                if module == self.module_dir.name:
                    ret[self._check_version(version)] = _file
        return ret

    def _sort_versions(self, versions):
        """sort a list of semver strings"""
        key = {}
        for v in versions:
            code = "".join([f"{int(s):08x}" for s in v.split(".")])
            key[code] = v
        ret = [key[code] for code in sorted(key.keys())]
        return list(ret)

    def latest_release_version(self, local=False):
        ret = None
        if self.local or local:
            versions = self.local_release_versions()
            if len(versions) > 0:
                versions = self._sort_versions(versions)
                ret = versions[-1]
        else:
            releases = self._validated_releases(self.repo.releases())
            if len(list(releases)):
                versions = self._sort_versions(
                    [self._check_version(r.tag_name) for r in releases]
                )
                if len(versions):
                    ret = versions[-1]
        if ret:
            ret = self._check_version(ret)
        return ret

    def _validated_releases(self, releases):
        ret = []
        for r in list(releases):
            if self._check_version(r.tag_name, return_none=True):
                ret.append(r)
        return ret

    def get_release_data(self):
        v = self.version
        if self.local:
            releases = self.local_release_files()
            if v in releases:
                _file = releases[v]
                return json.loads(Path(_file).read_text())
        else:
            return self._get_repo_release().as_dict()
        return None

    def local_release_versions(self):
        """return list of versions of local wheel files"""
        wheels = self.local_release_files(wheel=True)
        versions = list(wheels.keys())
        return versions

    def list_release_versions(self, sorted=True):
        if self.local:
            ret = self.local_release_versions()
        else:
            ret = [
                self._check_version(r.tag_name)
                for r in self._validated_releases(self.repo.releases())
            ]

        if sorted:
            ret = self._sort_versions(ret)

        return ret

    def get_current_branch(self):
        out = check_output("git branch | awk '/^\\*/{print $2}'", shell=True)
        branch = out.decode().strip()
        return branch

    def create_release(self, **kwargs):
        """create a new release"""

        ret = None

        if "tag_name" in kwargs:
            version = self._check_version(kwargs["tag_name"])
            kwargs.pop("version", None)
        else:
            version = kwargs.pop(
                "version", self.latest_release_version(local=True)
            )

        kwargs.setdefault("tag_name", f"v{version}")
        kwargs.setdefault("target_commitish", self.get_current_branch())
        kwargs.setdefault("name", f"v{version}")
        kwargs.setdefault("body", f"Release of version v{version}")
        kwargs.setdefault("draft", False)
        kwargs.setdefault("prerelease", False)

        verify = kwargs.pop("verify", None)
        if not verify or verify(kwargs):
            release = self.repo.create_release(**kwargs)
            if release:
                ret = release.as_dict()
        return ret

    def _get_wheel(self):
        wheel = self.local_release_files(wheel=True)[self.version]
        wheel = wheel.resolve()
        return wheel

    def _get_repo_release(self):
        """return current remote release"""
        release = self.repo.release_from_tag(f"v{self.version}")
        if not release:
            RuntimeError(f"unknown release: {self.version}")
        return release

    def upload_asset(
        self, asset=None, content_type=None, label=None, verify=None
    ):
        """upload a binary asset to release"""
        release = self._get_repo_release()

        if not asset:
            asset = self._get_wheel()
        asset = asset.resolve()

        content_type = content_type or "application/binary"
        name = asset.name

        if verify:
            verify(
                dict(
                    release=release.tag_name,
                    content_type=content_type,
                    label=label,
                    name=name,
                    local_file=str(asset),
                )
            )

        with asset.open("rb") as ifp:
            response = release.upload_asset(
                content_type=content_type,
                name=name,
                asset=ifp,
                label=label,
            )
            if response:
                return response.as_dict()

        return None

    def get_assets(self):
        """return the assets from the selected remote release"""
        release = self._get_repo_release()
        return [asset.as_dict() for asset in release.assets()]

    def download_assets(
        self, _id=None, regex=None, path=Path("."), dry_run=False
    ):
        """download the assets from the selected remote release"""
        ret = []
        path = path.resolve()
        release = self._get_repo_release()
        for asset in release.assets():
            if _id and asset.id != _id:
                continue
            elif regex and not re.match(regex, asset.name):
                continue
            asset_path = path / asset.name
            if dry_run:
                result = asset_path
            else:
                result = asset.download(asset_path)
            ret.append(str(result))

        return ret

    def download_file(self, repo_path, output_file):
        """download the contents of a repo file and write to output_file"""
        release = self._get_repo_release()
        ref = release.tag_name
        output_file.write(self.repo.file_contents(repo_path, ref).decoded)
        output_file.close()
        return 0

    def wheel(self):
        """return the filename of the selected wheel"""
        return str(self._get_wheel())
