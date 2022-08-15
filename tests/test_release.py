import os
from logging import debug, info
from pathlib import Path
from pprint import pformat

import pytest

from github_release_tool import Release


@pytest.fixture
def module_dir():
    return Path(".").resolve() / "github_release_tool"


@pytest.fixture
def wheel_dir():
    return Path(".").resolve() / "dist"


@pytest.fixture
def args(module_dir, wheel_dir):
    return dict(
        organization="rstms",
        repository="github-release-tool",
        token=os.environ["GITHUB_TOKEN"],
        module_dir=module_dir,
        wheel_dir=wheel_dir,
    )


@pytest.fixture
def mkrelease(args):
    def _release(**kwargs):
        args.update(kwargs)
        r = Release(**args)
        assert r
        debug(r)
        assert r.repo
        debug(r.repo)
        return r

    return _release


def test_release_list_local(mkrelease):
    r = mkrelease(local=True)
    ret = r.list_release_versions()
    assert isinstance(ret, list)
    assert len(ret)
    assert isinstance(ret[0], str)
    info(ret)


def test_release_list_remote(mkrelease):
    r = mkrelease()
    ret = r.list_release_versions()
    assert isinstance(ret, list)
    assert len(ret)
    assert isinstance(ret[0], str)
    info(ret)


def test_release_latest_local(mkrelease):
    r = mkrelease(local=True)
    ret = r.latest_release_version()
    assert isinstance(ret, str)
    info(ret)


def test_release_latest_remote(mkrelease):
    r = mkrelease()
    ret = r.latest_release_version()
    assert isinstance(ret, str)
    info(ret)


def test_release_sort(mkrelease):
    r = mkrelease()
    before = [
        "0.2.4",
        "11.3.1",
        "4.22.1",
        "1.2.2",
        "9.1.22",
        "1.4.2",
        "3.2.3",
        "4.2.1",
    ]
    debug(pformat({"before": before}))
    after = r._sort_versions(before)
    debug(pformat({"after": after}))
    assert after[-1] == "11.3.1"


def test_release_get(mkrelease):
    r = mkrelease()
    ret = r.get_release_data()
    assert ret
    assert isinstance(ret, dict)
    info(pformat(ret))


TEST_VERSION = "0.0.6"


def test_release_check_version(mkrelease):
    r = mkrelease()

    ret1 = r._check_version(TEST_VERSION)
    assert ret1

    with pytest.raises(TypeError):
        r._check_version(None)

    with pytest.raises(SyntaxError):
        r._check_version("foo")

    ret4 = r._check_version("0.0.0")
    assert ret4


def test_release_local_release_files_wheel(mkrelease):
    r = mkrelease()
    ret = r.local_release_files(wheel=True)
    assert isinstance(ret, dict)
    info(ret)


def test_release_local_release_files_json(mkrelease):
    r = mkrelease()
    ret = r.local_release_files()
    assert isinstance(ret, dict)
    info(ret)


def test_release_wheel(mkrelease):
    r = mkrelease()
    ret = r.wheel()
    assert isinstance(ret, str)
    info(ret)


def test_release_get_current_branch(mkrelease):
    r = mkrelease()
    ret = r.get_current_branch()
    assert isinstance(ret, str)
    assert ret == "master"


def test_release_get_assets(mkrelease):
    r = mkrelease()
    ret = r.get_assets()
    assert isinstance(ret, list)
    info(ret)


def test_release_local_release_versions(mkrelease):
    r = mkrelease()
    ret = r.local_release_versions()
    assert isinstance(ret, list)
    assert ret
    assert isinstance(ret[0], str)
    info(ret)


"""


    def create_release(self, **kwargs):
    def _get_repo_release(self):
    def upload_asset(
"""
