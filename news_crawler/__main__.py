from __future__ import annotations

import argparse

from news_crawler.ingest import main as ingest_main
from news_crawler.publish import main as publish_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="news_crawler")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ingest", help="Run ingestion + AI processing")
    sub.add_parser("publish", help="Generate & publish daily reports")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        ingest_main()
    elif args.command == "publish":
        publish_main()
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
