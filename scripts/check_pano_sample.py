"""Recount Pano Scrobbler version evidence from the shared sample CSV."""
import csv
from collections import defaultdict
from datetime import datetime, timezone
import math
from pathlib import Path
import re


DATA = (Path(__file__).resolve().parents[2]
        / "dataset_listenbrainz" / "sample" / "listens_20260904.csv")
UUID = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
versions = defaultdict(lambda: {"listens": 0, "valid": 0, "absent": 0, "invalid": 0})
accounts = set()
playback_dates = []
source_rows = 0

with DATA.open(newline="", encoding="utf-8") as source:
    for row in csv.DictReader(source):
        source_rows += 1
        try:
            timestamp = float(row.get("timestamp", ""))
            if not math.isfinite(timestamp):
                continue
            played = datetime.fromtimestamp(timestamp, timezone.utc).date()
        except (ValueError, OverflowError, OSError):
            continue

        client = (row.get("ai_submission_client") or "").strip().casefold()
        if client != "pano scrobbler":
            continue

        label = (row.get("ai_submission_client_version") or "").strip()
        label = label or "Unknown version"
        group = versions[label]
        group["listens"] += 1
        playback_dates.append(played)

        account = (row.get("user_id") or "").strip()
        if account.isdigit() and int(account) > 0:
            accounts.add(account)

        mbid = (row.get("ai_recording_mbid") or "").strip()
        status = "absent" if not mbid else "valid" if UUID.fullmatch(mbid) else "invalid"
        group[status] += 1

print(f"Sample source rows: {source_rows}")
print(f"Pano listen rows: {sum(g['listens'] for g in versions.values())}")
print(f"Pano distinct accounts: {len(accounts)}")
print(f"Reported version labels: {len(versions)}")
print(f"Pano playback span: {min(playback_dates)} through {max(playback_dates)} UTC")
for status in ("valid", "absent", "invalid"):
    print(f"{status} recording MBID syntax: {sum(g[status] for g in versions.values())}")
print("Largest version groups:")
for label, group in sorted(versions.items(), key=lambda item: (-item[1]["listens"], item[0]))[:6]:
    print(f"  {label}: {group['listens']}")
other = sorted(versions.items(), key=lambda item: (-item[1]["listens"], item[0]))[6:]
print(f"  Other ({len(other)} reported version labels): {sum(g['listens'] for _, g in other)}")
