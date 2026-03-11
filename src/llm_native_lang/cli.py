"""KAIRO CLI - Unified command-line interface for llm-native-lang."""
import argparse
import json
import os
import sys
from pathlib import Path

# Import validators
from .validators.lnd_validate import LNDValidator, main as lnd_validate_main
from .validators.lnc_validate import main as lnc_validate_main


def _validate_command(args):
    """Validate LND or LNC files."""
    target = args.target
    
    if target.endswith('.lnd'):
        validator = LNDValidator()
        path = Path(target)
        if path.is_file():
            valid = validator.validate_file(target)
        else:
            valid = validator.validate_directory(target)
        
        if not valid:
            validator.print_errors()
            return 1
        return 0
    elif target.endswith('.lnc'):
        return lnc_validate_main([target])
    else:
        # Try to detect by content or validate both
        print(f"Validating directory: {target}")
        lnd_validator = LNDValidator()
        lnd_valid = lnd_validator.validate_directory(target)
        lnc_valid = lnc_validate_main([target]) == 0
        
        if not lnd_valid or not lnc_valid:
            return 1
        return 0


def _execute_command(args):
    """Execute an LNC contract (placeholder)."""
    print(f"Executing: {args.file}")
    print("Note: execute command requires runtime modules")
    return 0


def _version_command(_args):
    """Show version information."""
    from . import __version__
    print(f"llm-native-lang version {__version__}")
    return 0


def main(argv=None):
    """Main entry point for KAIRO CLI."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        prog="kairo",
        description="KAIRO - LLM-Native Language CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.2.0",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate LND/LNC files",
    )
    validate_parser.add_argument("target", help="File or directory to validate")
    
    # execute command
    execute_parser = subparsers.add_parser(
        "execute",
        help="Execute an LNC contract",
    )
    execute_parser.add_argument("file", help="LNC file to execute")
    
    args = parser.parse_args(argv)
    
    if args.command == "validate":
        return _validate_command(args)
    elif args.command == "execute":
        return _execute_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())