import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEXICON = ROOT / "afghan_dari_tts_lexicon.json"
SHEET = ROOT / "review" / "review_sheet.csv"

READ_ONLY = ["id", "word", "pronunciation", "colloquial_pronunciation", "alternative_pronunciations",
             "domain", "category", "subcategory", "review_priority", "notes"]
EDITABLE = ["verification_status", "reviewed_pronunciation", "reviewer_alternative_pronunciations",
            "reviewer_regional_variety", "reviewer_notes", "reviewer_id", "review_date",
            "audio_reference", "decision"]
REVIEW_KEYS = EDITABLE[1:]


def export():
    data = json.loads(LEXICON.read_text(encoding="utf-8"))
    SHEET.parent.mkdir(exist_ok=True)
    with SHEET.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=READ_ONLY + EDITABLE)
        writer.writeheader()
        for e in data["entries"]:
            review = e["review"]
            writer.writerow({
                **{k: e[k] or "" for k in READ_ONLY if k != "alternative_pronunciations"},
                "alternative_pronunciations": "; ".join(e["alternative_pronunciations"]),
                "verification_status": e["verification_status"],
                **{k: review[k] or "" for k in REVIEW_KEYS if k != "reviewer_alternative_pronunciations"},
                "reviewer_alternative_pronunciations": "; ".join(review["reviewer_alternative_pronunciations"]),
            })
    print("exported %d rows to %s" % (len(data["entries"]), SHEET))


def import_reviews(path):
    data = json.loads(LEXICON.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in data["entries"]}
    updated = 0
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            e = by_id.get(row["id"])
            if e is None or not any(row[k].strip() for k in REVIEW_KEYS):
                continue
            review = e["review"]
            for k in REVIEW_KEYS:
                value = row[k].strip()
                if k == "reviewer_alternative_pronunciations":
                    review[k] = [v.strip() for v in value.split(";") if v.strip()]
                else:
                    review[k] = value or None
            review["review_date"] = review["review_date"] or date.today().isoformat()
            e["verification_status"] = row["verification_status"].strip() or "in_review"
            updated += 1
    statuses = [e["verification_status"] for e in data["entries"]]
    data["metadata"]["verified_entries"] = sum(1 for s in statuses if s.startswith("verified") or s == "corrected")
    data["metadata"]["unverified_entries"] = statuses.count("unverified")
    LEXICON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("imported reviews for %d entries" % updated)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "export":
        export()
    elif len(sys.argv) == 3 and sys.argv[1] == "import":
        import_reviews(sys.argv[2])
    else:
        print("usage: review_csv.py export | import <sheet.csv>")
        sys.exit(2)
