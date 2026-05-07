"""CLI entry-points for pipewatch."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from pipewatch import __version__  # type: ignore[attr-defined]
from pipewatch.cli.config_loader import ConfigError, load_config
from pipewatch.metrics.collector import MetricCollector
from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.formatter import format_summary
from pipewatch.reporting.ranking import rank_metrics
from pipewatch.sources import get_source


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor and alert on data pipeline health metrics.",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Fetch metrics and evaluate alerts.")
    run_p.add_argument("--source", required=True, help="Source type key (http/db/file).")
    run_p.add_argument("--config", required=True, help="Path to YAML config file.")
    run_p.add_argument("--output", choices=["text", "json"], default="text")
    run_p.add_argument(
        "--rank", action="store_true", help="Show metrics ranked by health score."
    )

    sub.add_parser("version", help="Print version and exit.")
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"[pipewatch] config error: {exc}", file=sys.stderr)
        return 1

    source_cls = get_source(args.source)
    if source_cls is None:
        print(f"[pipewatch] unknown source: {args.source!r}", file=sys.stderr)
        return 1

    source = source_cls(config)
    collector = MetricCollector()
    runner = PipelineRunner(PipelineConfig(source=source, collector=collector))
    runner.run()

    metrics = collector.get_all()
    summary = build_summary(metrics)

    if args.output == "json":
        data = summary.to_dict()
        if args.rank:
            ranked = rank_metrics(metrics)
            data["ranking"] = [r.to_dict() for r in ranked]
        print(json.dumps(data, indent=2))
    else:
        print(format_summary(summary))
        if args.rank:
            ranked = rank_metrics(metrics)
            print("\n--- Metric Ranking (worst first) ---")
            for r in ranked:
                print(f"  #{r.rank:>3}  [{r.metric.status.value.upper():>8}]  {r.metric.name}  score={r.score:.2f}")

    return 0 if summary.critical_count == 0 else 2


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"pipewatch {__version__}")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "version":
        sys.exit(cmd_version(args))
    else:
        parser.print_help()
        sys.exit(0)
