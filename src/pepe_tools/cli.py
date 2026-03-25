import argparse
import sys

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="pepe-tools CLI")
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s 0.1.0"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # API subcommand
    api_parser = subparsers.add_parser("api", help="Realiza pruebas de API al estilo Postman")
    api_parser.add_argument("method", choices=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"], help="HTTP Method")
    api_parser.add_argument("url", help="URL to test")
    api_parser.add_argument("-H", "--header", action="append", help="HTTP Headers format 'Key: Value'", default=[])
    api_parser.add_argument("-d", "--data", help="Request body data (JSON, urlencoded, etc.)")

    # Load test subcommand
    load_parser = subparsers.add_parser("load", help="Realiza prueba de carga de API leyendo un archivo JSON")
    load_parser.add_argument("config", help="Ruta al archivo JSON de configuración")
    load_parser.add_argument("--env", help="Ruta al archivo JSON de entorno de Postman para variables")
    load_parser.add_argument("--filter-user", help="Filtra los resultados y estadísticas mostradas por el usuario (credencial) especificado")
    load_parser.add_argument("--token", help="Bearer token para usar en autorización")
    load_parser.add_argument("-H", "--header", action="append", help="Headers HTTP adicionales en formato 'Key: Value'", default=[])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "api":
        from .api_tester import execute_api_test
        execute_api_test(args.method, args.url, args.header, args.data)
    elif args.command == "load":
        from .load_tester import execute_load_test
        execute_load_test(args.config, args.filter_user, args.token, args.header, getattr(args, "env", None))
    else:
        print(f"Executing command: {args.command}")

if __name__ == "__main__":
    main()
