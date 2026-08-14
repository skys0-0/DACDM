from __future__ import annotations

import argparse

from .protocol import validate_protocol_integrity


def main() -> None:
    parser = argparse.ArgumentParser(prog="dacdm")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-protocol")
    args = parser.parse_args()

    if args.command == "validate-protocol":
        errors = validate_protocol_integrity()
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            raise SystemExit(1)
        print("Protocol integrity: OK")
