"""Console script for github_release_tool."""

import json
import os
import re
import sys
from pathlib import Path

import click

from .release import Release
from .version import __timestamp__, __version__

header = f"{__name__.split('.')[0]} v{__version__} {__timestamp__}"


def output_setup(_json=True, _compact=False, _func=print):
    def _output(data):
        if _json:
            if _compact:
                args = dict(separators=(",", ":"))
            else:
                args = dict(indent=2)
            ret = json.dumps(data, **args)
        else:
            ret = str(data)

        _func(ret)
        return 0

    return _output


@click.group("release")
@click.version_option(message=header)
@click.option("-d", "--debug", is_flag=True, help="debug mode")
@click.option(
    "-j/-t",
    "--json/--text",
    is_flag=True,
    default=True,
    help="output json or text",
)
@click.option(
    "-c",
    "--compact",
    is_flag=True,
    help="compact json output",
)
@click.option(
    "-v",
    "--version",
    type=str,
    help="select release version tag",
)
@click.option(
    "-T", "--token", type=str, envvar="GITHUB_DEPLOY_TOKEN", show_envvar=True
)
@click.option(
    "-o",
    "--org",
    type=str,
    envvar="GITHUB_ORGANIZATION",
    show_envvar=True,
)
@click.option(
    "-p",
    "--project",
    type=str,
    envvar="GITHUB_REPO",
    show_envvar=True,
    help="github repo name",
)
@click.option(
    "-R",
    "--repo_root",
    type=str,
    envvar="REPO_ROOT",
    show_envvar=True,
    help="local repo root dir",
)
@click.option(
    "-r/-l",
    "--remote/--local",
    is_flag=True,
    help="select remote (github) / local releases",
)
@click.pass_context
def cli(ctx, debug, json, compact, **kwargs):
    """github release tool"""

    def exception_handler(
        exception_type, exception, traceback, debug_hook=sys.excepthook
    ):
        if debug:
            debug_hook(exception_type, exception, traceback)
        else:
            click.echo(f"{exception_type.__name__}: {exception}", err=True)

    sys.excepthook = exception_handler

    # support some alternatives for env vars
    kwargs.setdefault("token", os.environ["GITHUB_TOKEN"])
    kwargs.setdefault("project", os.environ["PROJECT"])

    ctx.obj = Release(**kwargs)
    ctx.obj.output = output_setup(json, compact, click.echo)


def _fail(msg):
    click.echo(f"failed: {msg}", err=True)
    sys.exit(1)


@cli.command()
@click.pass_context
def list(ctx):
    """list all released or dist versions"""
    r = ctx.obj
    return r.output(r.list_release_versions())


@cli.command()
@click.pass_context
def latest(ctx):
    """latest release"""
    r = ctx.obj
    return r.output(r.latest_release_version())


@cli.command()
@click.pass_context
def assets(ctx):
    """list assets for selected version or latest release"""
    r = ctx.obj
    for asset in r.get_assets():
        r.output(asset.as_dict())
    return 0


@cli.command()
@click.pass_context
@click.option("-i", "--id", "_id", type=int)
@click.option("-r", "--regex", type=str)
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=False, writable=True, path_type=Path
    ),
)
def download(ctx, _id, regex, path):
    """download asset with id to path"""

    r = ctx.obj
    ret = {}

    release = r.get_release_data()

    for asset in release.assets():
        if _id and asset.id != _id:
            continue
        elif regex and not re.match(regex, asset.name):
            continue
        else:
            path = path / asset.name
            ret[asset.name] = asset.download(path)

    return r.output(ret)


@cli.command()
@click.pass_context
def wheel(ctx):
    """output wheel pathname"""
    r = ctx.obj
    return r.output(r.wheel())


@cli.command()
@click.pass_context
def upload(ctx):
    """upload wheel file to github"""
    r = ctx.obj
    return r.output(r.upload())


@cli.command()
@click.argument("key", type=str, default=None, required=False)
@click.pass_context
def get(ctx, key):
    """output release response data"""
    r = ctx.obj

    data = r.get_release_data()

    if not None and key is not None:
        data = data.get(key, None)

    return r.output(data)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
