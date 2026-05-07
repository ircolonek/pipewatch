"""CLI entry-point for pipewatch."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from pipewatch import __version__
from pipewatch.cli.config_loader import ConfigError, load_config
from pipewatch.metrics.collector import MetricCollector
from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.formatter import format_summary
from pipewatch.reporting.tagging import tag_metrics, filter_by_tag, group_by_tag


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor and alert on data pipeline health metrics.",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Fetch metrics and evaluate alerts.")
    run_p.add_argument("--source", required=True, help="Source key (http/db/file).")
    run_p.add_argument("--config", required=True, help="Path to YAML config file.")
    run_p.add_argument("--output", choices=["text", "json"], default="text")
    run_p.add_argument("--rank", action="store_true", help="Sort output by severity.")
    run_p.add_argument(
        "--tag",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Filter results to metrics carrying this tag (repeatable).",
    )
    run_p.add_argument(
        "--group-by",
        metavar="TAG_KEY",
        dest="group_by",
        default=None,
        help="Group output by the value of a tag key.",
    )

    sub.add_parser("version", help="Print version and exit.")
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    collector = MetricCollector()
    runner = PipelineRunner(
        config=PipelineConfig(source_key=args.source, params=cfg.get("source_params", {})),
        collector=collector,
        alert_rules=cfg.get("alert_rules", []),
    )
    runner.run()

    metrics = collector.get_all()

    # Apply tag filters if supplied
    tag_pairs: dict = {}
    for item in args.tag:
        if "=" in item:
            k, v = item.split("=", 1)
            tag_pairs[k] = v

    tagged = tag_metrics(metrics, tag_pairs)
    for k, v in tag_pairs.items():
        tagged = filter_by_tag(tagged, k, v)

    filtered_metrics = [tm.metric for tm in tagged]

    if args.group_by:
        groups = group_by_tag(tagged, args.group_by)
        for bucket, tms in sorted(groups.items()):
            label = bucket or "(untagged)"
            report = build_summary([tm.metric for tm in tms])
            print(f"\n=== {args.group_by}={label} ===")
            print(format_summary(report))
        return 0

    report = build_summary(filtered_metrics)
    if args.output == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_summary(report))
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"pipewatch {__version__}")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "version":
        sys.exit(cmd_version(args))
    else:
        parser.print_help()
        sys.exit(0)
