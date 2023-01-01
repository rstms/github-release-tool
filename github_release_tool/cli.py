"""Console script for github_release_tool."""

import json
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


class CustomGroup(click.Group):
    def get_help(self, *args, **kwargs):
        help_str = super().get_help(*args, **kwargs)
        help_list = help_str.split("\n")
        help_list[2] += f" v{__version__}"
        return "\n".join(help_list)


@click.group(name="release", cls=CustomGroup)
@click.option("-d", "--debug", is_flag=True, help="debug mode")
@click.option(
    "-j/-J",
    "--json/--no-json",
    is_flag=True,
    default=True,
    help="format output as json",
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
    "-t", "--token", type=str, envvar="GITHUB_TOKEN", show_envvar=True
)
@click.option(
    "-o",
    "--organization",
    type=str,
    envvar="GITHUB_ORG",
    show_envvar=True,
    help="github organization name",
)
@click.option(
    "-r",
    "--repository",
    type=str,
    envvar="GITHUB_REPO",
    show_envvar=True,
    help="github repository name",
)
@click.option(
    "-m",
    "--module-dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    envvar="MODULE_DIR",
    show_envvar=True,
    help="python module directory",
)
@click.option(
    "-w",
    "--wheel-dir",
    type=click.Path(
        dir_okay=True, file_okay=False, writable=True, path_type=Path
    ),
    envvar="WHEEL_DIR",
    default="./dist",
    show_envvar=True,
    help="wheel directory (usually ./dist)",
)
@click.option(
    "-l",
    "--local",
    is_flag=True,
    help="select local release data",
)
@click.pass_context
def cli(ctx, debug, json, compact, **kwargs):
    """github release tool"""

    if kwargs["local"]:
        if kwargs["module_dir"] is None or not kwargs["module_dir"].is_dir():
            ctx.fail("MODULE_DIR is not a directory")

    def exception_handler(
        exception_type, exception, traceback, debug_hook=sys.excepthook
    ):
        if debug:
            debug_hook(exception_type, exception, traceback)
        else:
            click.echo(f"{exception_type.__name__}: {exception}", err=True)
            sys.exit(-1)

    sys.excepthook = exception_handler

    ctx.obj = Release(**kwargs)
    ctx.obj.output = output_setup(json, compact, click.echo)


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
    """list asset data for selected version or latest release"""
    r = ctx.obj
    return r.output(r.get_assets())


@cli.command()
@click.pass_context
@click.option("-i", "--id", "_id", type=int)
@click.option("-r", "--regex", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=False, writable=True, path_type=Path
    ),
)
def download_asset(ctx, _id, regex, path, dry_run):
    """download asset with id to path"""
    r = ctx.obj
    return r.output(r.download_assets(_id, regex, path, dry_run))


@cli.command()
@click.argument("repo-path", type=str)
@click.argument("output", type=click.File("wb"), default="-")
@click.pass_context
def download_file(ctx, repo_path, output):
    """output the contents of a repo file"""
    r = ctx.obj
    return r.download_file(repo_path, output)


@cli.command()
@click.pass_context
def wheel(ctx):
    """output wheel pathname"""
    r = ctx.obj
    return r.output(r.wheel())


def verify_upload(args):
    click.echo("Upload asset file:", err=True)
    for k, v in args.items():
        click.echo(f"{k}={v}")
    click.confirm("confirm", abort=True, err=True)
    return True


@cli.command()
@click.option(
    "-c",
    "--content-type",
    type=str,
    help="content-type",
)
@click.option("-l", "--label", type=str, help="short description")
@click.option("-f", "--force", is_flag=True, help="bypass confirmation prompt")
@click.argument(
    "asset",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    required=False,
)
@click.pass_context
def upload(ctx, content_type, label, force, asset):
    """upload asset file to release"""
    r = ctx.obj
    if force:
        verify = None
    else:
        verify = verify_upload
    return r.output(r.upload_asset(asset, content_type, label, verify))


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


def verify_create(args):
    click.echo("create release:", err=True)
    for k, v in args.items():
        click.echo(f"{k}={v}", err=True)
    click.confirm("confirm", abort=True, err=True)
    return True


@cli.command()
@click.option("-t", "--tag-name", type=str, help="tag name")
@click.option(
    "-c",
    "--target-commitish",
    type=str,
    help="target commitish (branch or commit)",
)
@click.option("-n", "--name", type=str, help="release name")
@click.option("-b", "--body", type=str, help="body text for release")
@click.option("-d", "--draft", is_flag=True, help="draft mode switch")
@click.option(
    "-p", "--prerelease", is_flag=True, help="prerelease mode switch"
)
@click.option("-f", "--force", is_flag=True, help="bypass confirmation prompt")
@click.pass_context
def create(ctx, **kwargs):
    """create a new release"""
    r = ctx.obj
    if not kwargs.pop("force", False):
        kwargs["verify"] = verify_create
    kwargs = {k: v for k, v in kwargs.items() if v}
    return r.output(r.create_release(**kwargs))


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
