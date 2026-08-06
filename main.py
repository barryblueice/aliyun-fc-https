"""Aliyun FC HTTPS certificate renewal daemon and one-shot command."""

import argparse
import time

import pyfiglet
import schedule
from loguru import logger

from update import ConfigurationRequired, updating_main_process


def _run_scheduled_update() -> None:
    try:
        updating_main_process()
    except Exception:
        logger.exception("Scheduled certificate check failed")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Issue and deploy an ACME wildcard certificate through AliDNS"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="check once and exit instead of running as a daemon",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="ignore the renewal window for this run",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    logger.info("Project: https://github.com/barryblueice/aliyun-fc-https")
    logger.info(f"\n{pyfiglet.figlet_format('Aliyun FC HTTPS')}")

    try:
        updating_main_process(force=args.force)
    except ConfigurationRequired:
        return 0
    except Exception:
        logger.exception("Certificate update failed")
        return 1

    if args.once:
        return 0

    schedule.every(12).hours.do(_run_scheduled_update)
    logger.info("Daemon started; certificates will be checked every 12 hours")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
