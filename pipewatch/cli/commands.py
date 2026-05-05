"""CLI entry-point commands for pipewatch."""
from __future__ import annotations

import argparse
import sys

from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.metrics.collector import MetricCollector
from pipewatch.alerts.dispatcher import AlertDispatcher
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.exporter import export_to_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor and alert on data pipeline health metrics.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Fetch metrics and evaluate alerts once.")
    run_p.add_argument("--source", required=True, help="Registered source key (e.g. http, db, file).")
    run_p.add_argument("--config", required=True, help="Path to pipeline JSON config file.")
    run_p.add_argument("--export", default=None, help="Optional path to export results (json/csv).")
    run_p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output.")

    sub.add_parser("version", help="Print pipewatch version.")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    import json

    with open(args.config) as fh:
        raw = json.load(fh)

    config = PipelineConfig(
        source_key=args.source,
        source_params=raw.get("source_params", {}),
        alert_rules=raw.get("alert_rules", []),
    )

    collector = MetricCollector()
    dispatcher = AlertDispatcher()
    runner = PipelineRunner(config, collector, dispatcher)

    runner.run()

    metrics = collector.get_all()
    report = build_summary(metrics)
    fired = dispatcher.get_fired()  # type: ignore[attr-defined]

    print(format_summary(report, use_colour=not args.no_color))
    if fired:
        print(format_alerts(fired, use_colour=not args.no_color))

    if args.export:
        export_to_file(report, args.export)
        print(f"Results exported to {args.export}")

    return 0 if report.critical_count == 0 else 1


def cmd_version() -> int:
    from pipewatch import __version__  # type: ignore[attr-defined]
    print(f"pipewatch {__version__}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "version":
        sys.exit(cmd_version())
    else:
        parser.print_help()
        sys.exit(1)
