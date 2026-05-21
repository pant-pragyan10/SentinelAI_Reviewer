import json
import csv
from io import StringIO
from typing import Dict


def export_json(reviews: Dict) -> str:
    return json.dumps(reviews, indent=2)


def export_csv(reviews: Dict) -> str:
    # Flatten issues into CSV
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(["file_path", "issue_id", "category", "severity", "confidence", "title", "description"])
    for fpath, flist in reviews.items():
        for it in flist:
            writer.writerow([fpath, it.get("issue_id"), it.get("category"), it.get("severity"), it.get("confidence"), it.get("title"), it.get("description")])
    return out.getvalue()
