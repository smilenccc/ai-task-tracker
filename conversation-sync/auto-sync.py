#!/usr/bin/env python3
"""
AI Task Tracker - Auto Sync Script
Pulls latest conversations from all sources and pushes local changes.
Used by both manual trigger ("小八 同步") and Windows Task Scheduler (hourly).
"""

import subprocess
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_DIR / "conversation-sync" / "sync.log"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_git(args, cwd=None):
    """Run a git command and return (success, output)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd or REPO_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def sync():
    """Pull latest, stage conversation changes, commit and push."""
    logging.info("=== Sync started ===")

    # 1. Pull latest
    ok, out = run_git(["pull", "origin", "main"])
    if ok:
        logging.info(f"Pull: {out or 'up to date'}")
    else:
        logging.warning(f"Pull issue: {out}")

    # 2. Stage conversation-sync changes
    run_git(["add", "conversation-sync/conversations/"])

    # 3. Check if there's anything to commit
    ok, out = run_git(["diff", "--cached", "--stat"])
    if not out:
        logging.info("No new changes to push")
        logging.info("=== Sync finished (nothing to push) ===")
        return True

    # 4. Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok, out = run_git(["commit", "-m", f"Auto-sync conversations - {timestamp}"])
    if ok:
        logging.info(f"Commit: {out.splitlines()[-1] if out else 'done'}")
    else:
        logging.warning(f"Commit issue: {out}")
        return False

    # 5. Push
    ok, out = run_git(["push", "origin", "main"])
    if ok:
        logging.info(f"Push: success")
    else:
        logging.warning(f"Push issue: {out}")
        return False

    logging.info("=== Sync finished (pushed) ===")
    return True


if __name__ == "__main__":
    setup_logging()
    try:
        success = sync()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Sync error: {e}")
        sys.exit(1)
