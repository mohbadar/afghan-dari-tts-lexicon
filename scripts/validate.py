import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = re.compile(r"^[a-zāēō' \-]+$")
STATUSES = {"unverified", "in_review", "verified", "verified_multiple", "corrected", "disputed", "rejected"}


def key(word):
    return word.replace("‌", "").replace(" ", "")


def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data["entries"]
    meta = data["metadata"]
    errors = []

    keys = Counter(key(e["word"]) for e in entries)
    errors += ["duplicate word: %s" % k for k, n in keys.items() if n > 1]
    ids = Counter(e["id"] for e in entries)
    errors += ["duplicate id: %s" % k for k, n in ids.items() if n > 1]

    schema = Counter(tuple(e.keys()) for e in entries)
    if len(schema) != 1:
        errors.append("inconsistent entry schema: %d variants" % len(schema))

    for e in entries:
        if not e["pronunciation"]:
            errors.append("missing pronunciation: %s" % e["id"])
        forms = [e["pronunciation"], e["colloquial_pronunciation"], e["review"]["reviewed_pronunciation"],
                 *e["alternative_pronunciations"], *e["review"]["reviewer_alternative_pronunciations"]]
        errors += ["bad characters in %s: %s" % (e["id"], f) for f in forms if f and not ALLOWED.match(f)]
        if e["verification_status"] not in STATUSES:
            errors.append("unknown status in %s: %s" % (e["id"], e["verification_status"]))
        if e["verification_status"].startswith("verified") and not e["review"]["reviewer_id"]:
            errors.append("verified without reviewer_id: %s" % e["id"])

    everyday = sum(1 for e in entries if e["domain"] == "everyday")
    poultry = sum(1 for e in entries if e["domain"] == "poultry")
    status = Counter(e["verification_status"] for e in entries)

    if len(entries) < 2300:
        errors.append("fewer than 2300 entries")
    if everyday < 2000:
        errors.append("fewer than 2000 everyday entries")
    if poultry < 300:
        errors.append("fewer than 300 poultry entries")
    if meta["total_entries"] != len(entries):
        errors.append("metadata.total_entries mismatch")

    print("entries: %d (everyday %d, poultry %d)" % (len(entries), everyday, poultry))
    print("status: %s" % dict(status))
    print("high review priority: %d" % sum(1 for e in entries if e["review_priority"] == "high"))
    for err in errors:
        print("ERROR", err)
    print("OK" if not errors else "FAILED (%d errors)" % len(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "afghan_dari_tts_lexicon.json"))
