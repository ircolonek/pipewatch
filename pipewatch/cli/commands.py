"""CLI entry-points for pipewatch."""
from __future__ import annotations

import argparse
import sys

from pipewatch import __version__  # type: ignore[attr-defined]
from pipewatch.cli.config_loader import load_config, ConfigError
from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.metrics.collector import MetricCollector
from pipewatch.alerts.dispatcher import AlertDispatcher
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.dashboard import render_dashboard


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor and alert on data pipeline health metrics.",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Fetch metrics and evaluate alerts.")
    run_p.add_argument("--source", required=True, help="Source key (http/db/file).")
    run_p.add_argument("--config", required=True, help="Path to YAML config file.")
    run_p.add_argument(
        "--dashboard",
        action="store_true",
        default=False,
        help="Render terminal dashboard instead of plain summary.",
    )
    run_p.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Export report to JSON or CSV file.",
    )

    sub.add_parser("version", help="Print version and exit.")
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"[pipewatch] config error: {exc}", file=sys.stderr)
        return 1

    collector = MetricCollector()
    dispatcher = AlertDispatcher()
    for rule_cfg in cfg.get("alert_rules", []):
        from pipewatch.alerts.rules import AlertRule
        dispatcher.add_rule(AlertRule(**rule_cfg))

    pipeline_cfg = PipelineConfig(
        source_key=args.source,
        source_options=cfg.get("source_options", {}),
    )
    runner = PipelineRunner(pipeline_cfg, collector, dispatcher)
    runner.run()

    metrics = collector.get_all()
    report = build_summary(metrics)
    fired = dispatcher.evaluate(metrics)

    if getattr(args, "dashboard", False):
        print(render_dashboard(report))
    else:
        print(format_summary(report))

    if fired:
        print(format_alerts(fired))

    if getattr(args, "export", None):
        from pipewatch.reporting.exporter import export_to_file
        export_to_file(report, args.export)
        print(f"[pipewatch] report exported to {args.export}")

    return 1 if report.critical_count > 0 else 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"pipewatch {__version__}")
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "version":
        sys.exit(cmd_version(args))
    else:
        parser.print_help()
        sys.exit(0)
