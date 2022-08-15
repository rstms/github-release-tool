import os

import pytest

from github_release_tool import Release


@pytest.fixture
def args():
    return dict(
        org="rstms",
        project="github-release-tool",
        token=os.environ["GITHUB_TOKEN"],
    )


@pytest.fixture
def test_release(args):
    def _test_release(**kwargs):
        args.update(kwargs)
        release = Release(**args)
        assert release
        assert release.repo
        return release

    return _test_release


def test_latest(test_release):
    release = test_release()
    ret = release.latest_release_version()
    assert ret in [None, str]


def test_remote_latest(test_release):
    release = test_release(remote=True)
    ret = release.latest_release_version()
    assert ret in [None, str]
