import argparse
import sys

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="pepe-tools CLI")
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s 0.1.0"
    )
    # Add your subcommands and arguments here
    parser.add_argument("command", nargs="?", help="Command to run")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    print(f"Executing command: {args.command}")
    # Delegate to command handler

if __name__ == "__main__":
    main()
