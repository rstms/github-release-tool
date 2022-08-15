import os
import pytest

from github_release_tool import Release

@pytest.fixture
def args():
    return dict(
        org='rstms',
        project='github_release_token',
        token=os.environ['GITHUB_TOKEN']
    )

@pytest.fixture
def release(args):
    def _release(**kwargs):
        args.update(kwargs)
        return Release(**args)

    return _release


def test_latest(release):
    release().latest_version()

def test_remote_latest(release):
    release(remote=True).latest_version()

