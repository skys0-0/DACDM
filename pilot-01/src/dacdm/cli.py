from __future__ import annotations

import argparse

from .protocol import validate_protocol_integrity
from .registries import validate_registry_files


def _report(errors: list[str], success: str) -> None:
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(success)


def main() -> None:
    parser = argparse.ArgumentParser(prog="dacdm")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-protocol")
    sub.add_parser("validate-registries")
    args = parser.parse_args()

    if args.command == "validate-protocol":
        _report(validate_protocol_integrity(), "Protocol integrity: OK")
    elif args.command == "validate-registries":
        _report(validate_registry_files(), "Registry integrity: OK")
