from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from . import APP_NAME, APP_VERSION

    # conda lockfiles --version
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
        help=f"Show the {APP_NAME} version number and exit.",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Only report available updates, do not install.",
    )
    parser.add_argument(
        "--force-reinstall",
        action="store_true",
        help="Install latest conda available even "
        "if currently installed is more recent.",
    )
    parser.add_argument(
        "--plugin",
        help="Name of a conda plugin to update",
    )


def execute(args: argparse.Namespace) -> int:
    import sys

    from conda.base.context import context
    from conda.exceptions import CondaError, DryRunExit
    from conda.reporters import get_spinner

    from .query import check_updates
    from .update import install_package_in_protected_env
    from .validate import validate_plugin_name

    if args.plugin:
        if sys.version_info < (3, 12):
            raise CondaError(
                "'--plugin' is only available on installations using Python 3.12+."
            )
        validate_plugin_name(args.plugin)
        package_name = args.plugin
    else:
        package_name = "conda"
    with get_spinner(f"Checking updates for {package_name}"):
        update_available, installed, latest = check_updates(package_name, sys.prefix)

    if not context.quiet:
        print(f"Installed {package_name}: {installed.version}")
        print(f"Latest {package_name}: {latest.version}")

    if not update_available:
        if not args.force_reinstall:
            print(f"{package_name} is already using the latest version available!")
            if args.dry_run:
                raise DryRunExit()
            return 0

    if args.dry_run:
        raise DryRunExit()

    return install_package_in_protected_env(
        package_name=package_name,
        package_version=latest.version,
        channel=installed.channel,
        force_reinstall=args.force_reinstall,
    )
