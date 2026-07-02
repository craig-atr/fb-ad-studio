#!/usr/bin/env python3
"""fal.ai balance + per-campaign cost tracking.

fal doesn't report per-call cost, so campaign cost is measured as the drop in
account balance across the campaign's generation work: snapshot the balance
before the first generation and after the last; the delta is the spend.

  # current account balance
  uv run tools/fal_cost.py balance

  # record a balance snapshot into the campaign's cost log (do this at the
  # START of stage 004, before any generation, and again after stage 005)
  uv run tools/fal_cost.py snapshot --campaign atomic-mothers-day --label start
  uv run tools/fal_cost.py snapshot --campaign atomic-mothers-day --label end

  # report spend for the campaign + current balance
  uv run tools/fal_cost.py report --campaign atomic-mothers-day

Auth: FAL_KEY env var, else a .fal_key file at the repo root (same as the other
tools). The billing endpoint may require a key with account/billing scope; if it
returns 403, check the balance on the fal dashboard instead.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BILLING_URL = "https://api.fal.ai/v1/account/billing?expand=credits"
KEY_FILE_NAME = ".fal_key"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


ADMIN_KEY_FILE_NAME = ".fal_admin_key"


def load_api_key() -> str:
    """Billing needs an admin-scoped key. Prefer FAL_ADMIN_KEY / .fal_admin_key,
    then fall back to the normal generation key (which usually lacks billing
    scope and will 403 — with a helpful message)."""
    for env in ("FAL_ADMIN_KEY", "FAL_KEY"):
        key = os.environ.get(env, "").strip()
        if key:
            return key
    for name in (ADMIN_KEY_FILE_NAME, KEY_FILE_NAME):
        key_path = repo_root() / name
        if key_path.is_file():
            key = key_path.read_text(encoding="utf-8-sig").strip()
            if key and not key.startswith("PASTE_YOUR_FAL"):
                return key
    raise SystemExit(
        "No fal.ai key found. For billing/balance, create an admin key with "
        "billing scope at https://fal.ai/dashboard/keys and save it to "
        f"{repo_root() / ADMIN_KEY_FILE_NAME} (or set FAL_ADMIN_KEY)."
    )


def fetch_balance() -> tuple[float, str]:
    request = urllib.request.Request(
        BILLING_URL,
        method="GET",
        headers={"Authorization": f"Key {load_api_key()}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(
            f"fal billing request failed ({exc.code}): {detail}\n"
            "A 401/403 means this key lacks billing scope. Create an admin key "
            "with billing access at https://fal.ai/dashboard/keys and save it to "
            f"{repo_root() / ADMIN_KEY_FILE_NAME} (or set FAL_ADMIN_KEY). "
            "Otherwise check the balance on https://fal.ai/dashboard."
        )
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach fal.ai: {exc.reason}")

    credits = data.get("credits") or {}
    balance = credits.get("current_balance")
    currency = credits.get("currency", "USD")
    if balance is None:
        raise SystemExit("No balance in response:\n" + json.dumps(data, indent=2)[:1000])
    return float(balance), currency


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def log_path(campaign: str) -> Path:
    return repo_root() / "work" / campaign / "cost-log.jsonl"


def read_log(campaign: str) -> list[dict]:
    path = log_path(campaign)
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def money(v: float, cur: str) -> str:
    sym = "$" if cur == "USD" else ""
    return f"{sym}{v:.2f} {cur}"


def cmd_balance(_args) -> None:
    balance, currency = fetch_balance()
    print(f"fal.ai balance: {money(balance, currency)}")


def cmd_snapshot(args) -> None:
    balance, currency = fetch_balance()
    entry = {"ts": now_iso(), "label": args.label, "balance": balance, "currency": currency}
    path = log_path(args.campaign)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"Snapshot [{args.label}] {money(balance, currency)} -> {path}")


def cmd_report(args) -> None:
    entries = read_log(args.campaign)
    current, currency = fetch_balance()
    print(f"Campaign: {args.campaign}")
    print(f"fal.ai balance:   {money(current, currency)}")

    if not entries:
        print("Spent on this ad: unknown — no snapshots recorded.")
        print("Record one at the start of generation next time: "
              f"fal_cost.py snapshot --campaign {args.campaign} --label start")
        return

    first = entries[0]
    start_balance = first["balance"]
    # Use the current live balance as the end point (most accurate).
    spent = start_balance - current
    print(f"                  (started {money(start_balance, currency)} at {first['ts']})")
    print(f"Spent on this ad: {money(spent, currency)}")
    print(f"Snapshots: {len(entries)}")
    if spent < 0:
        print("Note: balance went UP since the baseline (a top-up?) — spend figure unreliable.")
    print("Note: reflects ALL fal usage since the baseline snapshot; keep other "
          "fal work out of the window for an exact per-ad figure.")


def main() -> None:
    parser = argparse.ArgumentParser(description="fal.ai balance and per-campaign cost.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("balance", help="Print current fal.ai balance.")

    p_snap = sub.add_parser("snapshot", help="Record a balance snapshot for a campaign.")
    p_snap.add_argument("--campaign", required=True)
    p_snap.add_argument("--label", default="snapshot", help="e.g. start, end.")

    p_report = sub.add_parser("report", help="Show campaign spend + current balance.")
    p_report.add_argument("--campaign", required=True)

    args = parser.parse_args()
    {"balance": cmd_balance, "snapshot": cmd_snapshot, "report": cmd_report}[args.command](args)


if __name__ == "__main__":
    main()
