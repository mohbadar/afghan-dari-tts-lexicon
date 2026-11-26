import json, re, sys, unicodedata
from pathlib import Path
SRC = Path(__file__).resolve().parent.parent / "source"
from collections import Counter, OrderedDict

ZWNJ = "‌"
MI = "می" + ZWNJ
NAMI = "نمی" + ZWNJ

def norm(w):
    w = w.replace("ك", "ک").replace("ي", "ی").replace("ى", "ی").replace("ة", "ه")
    w = re.sub(r"\s+", " ", w.strip())
    return unicodedata.normalize("NFC", w)

def key(w):
    return norm(w).replace(ZWNJ, "").replace(" ", "").replace("ُ", "").replace("ً", "")

entries = []
index = {}
stats = Counter()

def review_block():
    return {
        "reviewed_pronunciation": None,
        "reviewer_alternative_pronunciations": [],
        "reviewer_regional_variety": None,
        "reviewer_notes": None,
        "reviewer_id": None,
        "review_date": None,
        "audio_reference": None,
        "decision": None,
    }

def add(word, pron, domain, cat, sub, colloq=None, alts=None, note=None, region=None,
        priority=False, verb_info=None, ptype=None):
    word = norm(word)
    if colloq == pron:
        colloq = None
    alts = list(dict.fromkeys(a for a in (alts or []) if a and a != pron and a != colloq))
    k = key(word)
    if k in index:
        e = index[k]
        if pron != e["pronunciation"] and pron not in e["alternative_pronunciations"]:
            e["alternative_pronunciations"].append(pron)
            e["homograph"] = True
            extra = "homograph/variant: '%s' (%s/%s)" % (pron, cat, sub)
            e["notes"] = (e["notes"] + "; " if e["notes"] else "") + extra
            e["review_priority"] = "high"
            stats["merged_homographs"] += 1
        else:
            stats["duplicates_skipped"] += 1
        return
    etype = "verb_form" if verb_info else ("phrase" if " " in word else "word")
    if ptype is None:
        ptype = "standard_spoken"
    regs = []
    if region:
        m = re.match(r"\s*([^:]+):\s*([^()]+?)\s*(\(.*\))?$", region)
        if m:
            regs.append({"variety": m.group(1).strip(), "pronunciation": m.group(2).strip(),
                         "verification_status": "unverified"})
    e = OrderedDict()
    e["id"] = None
    e["word"] = word
    e["pronunciation"] = pron
    e["colloquial_pronunciation"] = colloq
    e["alternative_pronunciations"] = alts
    e["domain"] = domain
    e["category"] = cat
    e["subcategory"] = sub
    e["entry_type"] = etype
    e["pronunciation_type"] = ptype
    e["homograph"] = False
    e["regional_variations"] = regs
    e["verb_info"] = verb_info
    e["verification_status"] = "unverified"
    e["review_priority"] = "high" if priority else "normal"
    e["source"] = "model_generated_draft"
    e["notes"] = note
    e["review"] = review_block()
    index[k] = e
    entries.append(e)

def parse_file(path, domain):
    cat = sub = None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            cat, sub = [x.strip() for x in line[1:].split("/")]
            continue
        parts = line.split("|")
        word, pron = parts[0].strip(), parts[1].strip()
        colloq = note = region = None
        alts = []
        pr = False
        for t in parts[2:]:
            t = t.strip()
            if t == "p":
                pr = True
            elif t.startswith("c="):
                cs = [x.strip() for x in t[2:].split(";")]
                colloq = cs[0]
                alts += cs[1:]
            elif t.startswith("a="):
                alts += [x.strip() for x in t[2:].split(";")]
            elif t.startswith("n="):
                note = t[2:]
            elif t.startswith("r="):
                region = t[2:]
        add(word, pron, domain, cat, sub, colloq, alts, note, region, pr)

PERSONS = ["1sg", "2sg", "3sg", "1pl", "2pl", "3pl"]
PRES_S = ["م", "ی", "د", "یم", "ید", "ند"]
PRES_P = ["om", "i", "at", "ēm", "ēd", "and"]
PRES_ALT = [None, None, "ad", None, "ēn", "an"]
PRES_C = ["om", "i", "a", "ēm", "ēn", "an"]
PAST_S = ["م", "ی", "", "یم", "ید", "ند"]
PAST_P = ["om", "i", "", "ēm", "ēd", "and"]
PAST_ALT = [None, None, None, None, "ēn", "an"]
PAST_C = ["om", "i", "", "ēm", "ēn", "an"]

def gen_verbs(path):
    for raw in open(path, encoding="utf-8"):
        if not raw.strip():
            continue
        f = [x.strip() for x in raw.rstrip("\n").split("|")]
        inf, infp, ps, pp, pc, pa, pap, pac, im, imp, imc, flags = f
        flags = set(flags.split(",")) if flags else set()
        pri = "p" in flags
        pc = pc or pp
        pac = pac or pap
        base = {"infinitive": inf, "infinitive_pronunciation": infp}
        gen_note = "generated from verb-stem table; check irregular colloquial form"
        add(inf, infp, "everyday", "verbs", "infinitive", note=None, priority=pri,
            verb_info=dict(base, tense="infinitive", person=None, polarity="positive"))
        polarities = [("positive", MI, "mē", "mē")]
        if "neg" in flags:
            polarities.append(("negative", NAMI, "namē", "namē"))
        for pol, sprefix, pprefix, cprefix in polarities:
            for i, per in enumerate(PERSONS):
                w = sprefix + ps + PRES_S[i]
                pr = pprefix + pp + PRES_P[i]
                alts = [pprefix + pp + PRES_ALT[i]] if PRES_ALT[i] else []
                co = cprefix + pc + PRES_C[i]
                add(w, pr, "everyday", "verbs", "present_" + pol, colloq=co, alts=alts,
                    note=gen_note + ("; stress on na-" if pol == "negative" else "; stress on mē-"),
                    priority=pri, verb_info=dict(base, tense="present", person=per, polarity=pol))
        for i, per in enumerate(PERSONS):
            w = pa + PAST_S[i]
            pr = pap + PAST_P[i]
            alts = [pap + PAST_ALT[i]] if PAST_ALT[i] else []
            co = pac + PAST_C[i]
            add(w, pr, "everyday", "verbs", "past_simple", colloq=co, alts=alts, note=gen_note,
                priority=pri, verb_info=dict(base, tense="past", person=per, polarity="positive"))
        if "neg" in flags and not pa.startswith(("آ", "ا")):
            for i, per in enumerate(PERSONS[:3]):
                w = "ن" + pa + PAST_S[i]
                add(w, "na" + pap + PAST_P[i], "everyday", "verbs", "past_negative",
                    colloq="na" + pac + PAST_C[i], note=gen_note + "; stress on na-", priority=pri,
                    verb_info=dict(base, tense="past", person=per, polarity="negative"))
        if im:
            add(im, imp, "everyday", "verbs", "imperative", colloq=imc or None, priority=pri,
                verb_info=dict(base, tense="imperative", person="2sg", polarity="positive"))

for f in ["e1.txt", "e2.txt", "e3.txt", "e4.txt", "e5.txt"]:
    parse_file(SRC / f, "everyday")
gen_verbs(SRC / "verbs.txt")
parse_file(SRC / "poultry.txt", "poultry")

ci = cp = 0
for e in entries:
    if e["domain"] == "everyday":
        ci += 1
        e["id"] = "common_%04d" % ci
    else:
        cp += 1
        e["id"] = "poultry_%04d" % cp

ALLOWED = re.compile(r"^[a-zāēō' \-]+$")
bad = []
for e in entries:
    for p in [e["pronunciation"], e["colloquial_pronunciation"], *e["alternative_pronunciations"]]:
        if p and not ALLOWED.match(p):
            bad.append((e["word"], p))

dst = sys.argv[1] if len(sys.argv) > 1 else str(SRC.parent / "afghan_dari_tts_lexicon.json")
if Path(dst).exists():
    previous = {key(e["word"]): e for e in json.load(open(dst, encoding="utf-8"))["entries"]}
    for e in entries:
        old = previous.get(key(e["word"]))
        if old and old["verification_status"] != "unverified":
            e["review"] = old["review"]
            e["verification_status"] = old["verification_status"]
            stats["reviews_preserved"] += 1

guide = json.load(open(SRC / "guidelines.json", encoding="utf-8"))
counts = Counter(e["verification_status"] for e in entries)
meta = OrderedDict(guide["metadata"])
meta.update({
    "total_entries": len(entries),
    "everyday_entries": ci,
    "poultry_entries": cp,
    "verified_entries": sum(n for s_, n in counts.items() if s_.startswith("verified") or s_ == "corrected"),
    "unverified_entries": counts.get("unverified", 0),
    "high_priority_review_entries": sum(1 for e in entries if e["review_priority"] == "high"),
    "entries_with_colloquial_form": sum(1 for e in entries if e["colloquial_pronunciation"]),
    "homograph_entries": sum(1 for e in entries if e["homograph"]),
    "verb_form_entries": sum(1 for e in entries if e["entry_type"] == "verb_form"),
    "phrase_entries": sum(1 for e in entries if e["entry_type"] == "phrase"),
})
out = OrderedDict()
out["metadata"] = meta
out["pronunciation_guidelines"] = guide["pronunciation_guidelines"]
out["tts_integration"] = guide["tts_integration"]
out["review_workflow"] = guide["review_workflow"]
out["entries"] = entries
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("total", len(entries), "everyday", ci, "poultry", cp, dict(stats))
print("bad chars", len(bad), bad[:40])
print(Counter(e["category"] for e in entries).most_common())
