"""Check NOAA for a newer HURDAT2 file and update hurdat2_ingest.py if found.

Exits 0 if nothing changed, 1 if the default URL was updated (signals the
GitHub Actions workflow to open a PR).
"""

import re
import sys
from pathlib import Path

import httpx

NOAA_INDEX = "https://www.nhc.noaa.gov/data/hurdat/"
INGEST_FILE = Path(__file__).parent.parent / "src" / "ingestion" / "hurdat2_ingest.py"


def get_latest_url() -> str | None:
    resp = httpx.get(NOAA_INDEX, timeout=30)
    resp.raise_for_status()
    # NOAA directory listing — find all Atlantic HURDAT2 file links
    links = re.findall(r'href="(hurdat2-1851-\d{4}-\d+\.txt)"', resp.text)
    if not links:
        return None
    # Filenames sort lexicographically by year then release date
    return NOAA_INDEX + sorted(links)[-1]


def get_current_url() -> str | None:
    text = INGEST_FILE.read_text(encoding="utf-8")
    m = re.search(r'"(https://www\.nhc\.noaa\.gov/data/hurdat/hurdat2-1851-[^"]+)"', text)
    return m.group(1) if m else None


def update_url(old: str, new: str) -> None:
    text = INGEST_FILE.read_text(encoding="utf-8")
    updated = text.replace(old, new)
    INGEST_FILE.write_text(updated, encoding="utf-8")
    print(f"Updated default URL:\n  old: {old}\n  new: {new}")


if __name__ == "__main__":
    latest = get_latest_url()
    if not latest:
        print("Could not find any HURDAT2 files on NOAA index page.")
        sys.exit(0)

    current = get_current_url()
    if current == latest:
        print(f"Already up to date: {latest}")
        sys.exit(0)

    update_url(current, latest)
    sys.exit(1)  # non-zero tells the workflow a change was made
