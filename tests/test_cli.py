#!/usr/bin/env python

"""Tests for `github_release_tool` package."""

import pytest
from click.testing import CliRunner

import github_release_tool 
from github_release_tool import cli

@pytest.fixture
def runner():
    runner = CliRunner()
    def _invoke(*args, **kwargs):
        result = runner.invoke(cli, *args, **kwargs)
        assert result.exit_code==0, result
        return result 

    return _invoke

def test_version():
    """Test reading version and module name"""
    assert github_release_tool.__name__ == "github_release_tool"
    assert isinstance(github_release_tool.__version__, str)


def test_cli():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0, result
    
    result = runner.invoke(cli, ['--bad-option'])
    assert result.exception, result
    assert result.exit_code != 0, result

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result
    assert "Show this message and exit." in result.output, result


def test_runner(runner):
    result = runner('--help')
    assert isinstance(result.output, str)
    assert len(result.output)

def test_local_latest(runner):
    runner('latest')

