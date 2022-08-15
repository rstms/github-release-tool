#!/usr/bin/env python3

# vi: ft=python

import json
import re
from pathlib import Path
from subprocess import check_output

import github3

VERSION_PATTERN = r"^([0-9]+)\.([0-9]+)\.([0-9]+)(-.*){0,1}$"
WHEEL_PATTERN = r"^([a-z][a-z0-9_]+)-([0-9]+\.[0-9]+\.[0-9]+)-.+\.whl$"
JSON_PATTERN = r"^([a-z][a-z0-9_]+)-([0-9]+\.[0-9]+\.[0-9]+)-release\.json$"


class Release:
    def __init__(
        self, *, org, project, token, version=None, remote=True, repo_root="."
    ):
        self.version_pattern = re.compile(VERSION_PATTERN)
        self.wheel_pattern = re.compile(WHEEL_PATTERN)
        self.json_pattern = re.compile(JSON_PATTERN)
        self.gh = github3.GitHub(token=token)
        if not isinstance(self.gh, github3.GitHub):
            raise RuntimeError("GitHub login failed")
        self.repo = self.gh.repository(org, project)
        if not isinstance(self.repo, github3.repos.repo.Repository):
            raise RuntimeError("GitHub repo lookup")
        self.repo_root = Path(repo_root)
        self.dist_dir = self.repo_root / "dist"
        self.remote = remote
        if version in [None, "latest"]:
            version = self.latest_release_version()
        self.version = self._check_version(version)

    def _check_version(self, v):
        if v is not None:
            if v.startswith("v"):
                v = v[1:]
            if not self.version_pattern.match(v):
                raise SyntaxError(f"unrecognized version format '{v}'")
        return v

    def _dist_files(self):
        return [e for e in self.dist_dir.iterdir() if e.is_file()]

    def _filter_dist_files(self, pattern):
        ret = {}
        for _file in self._dist_files():
            match = pattern.match(_file.name)
            repo, version = match.groups()[:1]
            if repo == self.repo:
                ret[self._check_version(version)] = _file
        return ret

    def _repo_release_versions(self):
        return [self._check_version(r.tag_name) for r in self.repo.releases()]

    def _local_release_versions(self, wheel=False):
        """return dict of json files from ./dist"""
        if wheel:
            pattern = self.wheel_pattern
        else:
            pattern = self.json_pattern

        return self._filter_dist_files(pattern)

    def _sort_versions(self, versions):
        """sort a list of semver strings"""
        key = {}
        for v in versions:
            code = "".join([f"{int(s):08x}" for s in v.split(".")])
            key[code] = v
        return [key[code] for code in sorted(key.keys())]

    def latest_release_version(self):
        if self.remote:
            releases = self.repo.releases()
            if len(list(releases)):
                v = self.repo.latest_release().tag_name
            else:
                v = None
        else:
            releases = self._local_release_versions(wheel=True)
            versions = self._sort_versions(releases.keys())
            if versions:
                v = versions[0]
            else:
                v = None
        return self._check_version(v)

    def get_release_data(self, v):
        v = self._check_version(v)
        if self.remote:
            return self.repo.release_from_tag("v" + v).as_dict()
        else:
            releases = self._local_release_versions()
            _file = releases[v]
            return json.loads(Path(_file).read_text())

    def list_release_versions(self, sorted=True):
        if self.remote:
            ret = self._release_versions()
        else:
            ret = self._dist_versions().keys()

        if sorted:
            ret = self._sort_versions(ret)

        return ret

    def get_current_branch():
        out = check_output("git branch | awk '/^\\*/{print $2}'", shell=True)
        branch = out.decode().strip()
        return branch

    def create_release(self, **kwargs):
        """create a new release"""

        version = kwargs.pop("version", self.latest_release_version())

        kwargs.setdefault("tag_name", f"v{version}")
        kwargs.setdefault("target_commitish", self.get_current_branch)
        kwargs.setdefault("name", f"v{version}")
        kwargs.setdefault("body", f"Release of version v{version}")
        kwargs.setdefault("draft", False)
        kwargs.setdefault("prerelease", False)

        verify = kwargs.pop("verify", None)
        if verify and not verify(kwargs):
            return None
        else:
            return self.repo.create_release(**kwargs)

    def upload_asset(self, asset_file=None, verify=None):
        """upload a binary asset to release"""

        version = self.version

        release = self.repo.release_from_tag(f"v{version}")

        asset_file = (
            asset_file or self.local_release_versions(wheel=True)[version]
        )
        asset_file = asset_file.resolve()

        if verify and not verify(dict(version=version, asset=asset_file)):
            return None
        else:
            with asset_file.open("rb") as ifp:
                return release.upload_asset(
                    content_type="application/binary", name=ifp.name, asset=ifp
                )

    def get_assets(self):
        release = self.repo.release_from_tag(f"v{self.version}")
        return release.assets
