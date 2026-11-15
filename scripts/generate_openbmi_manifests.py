"""Generate OpenBMI download manifest and missing files list."""
import csv
import json
import os
from pathlib import Path

base = Path(r"D:\my lab\LeakCheck\data\OpenBMI")
out_dir = Path(r"D:\my lab\LeakCheck_remote\data\manifests")
out_dir.mkdir(parents=True, exist_ok=True)

with open(base / "manifest.json", encoding="utf-8") as f:
    mf = json.load(f)

full_rows = []
missing_rows = []

for item in mf:
    p = item["path"]
    exp_size = item.get("size", 0)
    lp = base / p.replace("/", os.sep)

    chk = item.get("checksum", "")
    url = item.get("url", "")

    if not lp.exists():
        status = "MISSING"
        act_size = 0
    elif lp.is_dir():
        status = "EMPTY_DIR" if not list(lp.glob("*")) else "DIR"
        act_size = 0
    elif lp.stat().st_size == 0:
        status = "EMPTY_FILE"
        act_size = 0
    elif lp.stat().st_size != exp_size:
        status = "TRUNCATED"
        act_size = lp.stat().st_size
    else:
        status = "VERIFIED_EXACT"
        act_size = lp.stat().st_size

    row = {
        "path": p,
        "expected_size": exp_size,
        "actual_size": act_size,
        "status": status,
        "checksum": chk,
        "url": url,
    }
    full_rows.append(row)
    if status != "VERIFIED_EXACT":
        missing_rows.append(row)

# Write download manifest
with open(out_dir / "openbmi_download_manifest.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["path", "expected_size", "actual_size", "status", "checksum", "url"])
    writer.writeheader()
    writer.writerows(full_rows)

# Write missing files
with open(out_dir / "openbmi_missing_files.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["path", "expected_size", "actual_size", "status", "checksum", "url"])
    writer.writeheader()
    writer.writerows(missing_rows)

print(f"Total manifest items: {len(full_rows)}")
print(f"Verified exact files: {len(full_rows) - len(missing_rows)}")
print(f"Missing or truncated items: {len(missing_rows)}")
