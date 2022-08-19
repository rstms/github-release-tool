#!/usr/bin/env python

"""Tests for `github_release_tool` package."""

from logging import debug

import pytest
import os

from click.testing import CliRunner

import github_release_tool
from github_release_tool import cli


@pytest.fixture
def runner():
    runner = CliRunner()

    def _runner(*args, **kwargs):
        _args = tuple([cli] + list(args))
        debug(f"cli({_args[1:]}, {kwargs})")
        result = runner.invoke(*_args, **kwargs)
        assert result.exit_code == 0, result
        debug(result.output)
        debug(f"{result}")
        return result

    return _runner


def test_version():
    """Test reading version and module name"""
    assert github_release_tool.__name__ == "github_release_tool"
    assert isinstance(github_release_tool.__version__, str)


def test_cli():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0, result

    result = runner.invoke(cli, ["--bad-option"])
    assert result.exception, result
    assert result.exit_code != 0, result

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result
    assert "Show this message and exit." in result.output, result

def test_cli_latest_remote():
    os.environ.pop('MODULE_DIR', None)
    runner = CliRunner()
    result = runner.invoke(cli, ["latest"])
    assert not result.exception
    assert result.exit_code == 0, result

def test_cli_latest_local():
    os.environ.pop('MODULE_DIR', None)
    runner = CliRunner()
    result = runner.invoke(cli, ["-l", "latest"])
    assert result.exception
    assert "MODULE_DIR is not a directory" in result.output
