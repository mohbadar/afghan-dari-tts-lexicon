# Afghan Dari TTS Pronunciation Lexicon

Word-level pronunciation overrides for a custom Afghan Dari (Kabul reference variety) text-to-speech engine, with an Afghan-specific Latin romanization (AD-Latin v1) and a built-in native-speaker review workflow.

## Contents

| Path | Purpose |
|---|---|
| `afghan_dari_tts_lexicon.json` | The lexicon (build output, also holds review results) |
| `source/*.txt` | Human-editable source word lists |
| `source/verbs.txt` | Verb stem table used to generate conjugations |
| `source/guidelines.json` | Metadata, romanization rules, TTS integration and review docs |
| `scripts/build.py` | Builds the JSON from `source/`; keeps existing review results |
| `scripts/validate.py` | Syntax, duplicates, counts, character set and status checks |
| `scripts/review_csv.py` | Exports a review spreadsheet and imports reviewer results |
| `review/review_sheet.csv` | Spreadsheet for native-speaker reviewers (opens in Excel / Google Sheets) |

## Numbers (v1.0.0)

| | Count |
|---|---|
| Total unique entries | 3,453 |
| Everyday vocabulary | 2,741 (including 898 generated verb forms) |
| Poultry / egg farming / veterinary | 712 |
| Entries with a separate colloquial Kabuli form | 647 |
| Homographs (same spelling, multiple readings) | 31 |
| Verified / unverified | 0 / 3,453 |
| High review priority | 473 |

## Romanization (AD-Latin v1)

| Symbol | Sound | Example |
|---|---|---|
| a | short a / final silent ه | khāna, bacha |
| ā | long rounded ā | āb, kābol |
| e | short e/i (zēr) | del, ketāb |
| o | short o/u (pēsh) | mēkonom, raftom |
| i / u | long ī / ū | shir (milk), pul |
| ē / ō | Afghan majhul vowels | shēr (lion), rōz, dōst, mē- |
| aw / ay | diphthongs | naw, nawrōz, khayr |
| w | consonant و (not v) | waqt, gāw |
| q / gh | ق / غ, kept distinct | qalam / morgh |
| kh sh ch zh j | خ ش چ ژ ج | |
| ' | audible ع/ء | sā'at |
| - | ezafe / clitic joint (no pause) | morgh-e tokhmi |

The full rules (R1–R16), the IPA mapping hint and verb ending rules are in `pronunciation_guidelines` inside the JSON.

## Entry format

```json
{
  "id": "common_1845",
  "word": "می‌روم",
  "pronunciation": "mērawom",
  "colloquial_pronunciation": "mērom",
  "alternative_pronunciations": [],
  "domain": "everyday",
  "category": "verbs",
  "subcategory": "present_positive",
  "entry_type": "verb_form",
  "pronunciation_type": "standard_spoken",
  "homograph": false,
  "regional_variations": [],
  "verb_info": {"infinitive": "رفتن", "tense": "present", "person": "1sg", "polarity": "positive"},
  "verification_status": "unverified",
  "review_priority": "normal",
  "source": "model_generated_draft",
  "notes": "...",
  "review": {"reviewed_pronunciation": null, "reviewer_id": null, "audio_reference": null, "...": "..."}
}
```

## Using it in a TTS engine

1. Normalize text (ك/ي → ک/ی, NFC, numbers to words).
2. Longest match first: phrases, then single words; also try the key with ZWNJ and spaces removed.
3. Choose the form: `review.reviewed_pronunciation`, else `colloquial_pronunciation` (conversational style), else `pronunciation`.
4. If `homograph` is true, pick between `pronunciation` and `alternative_pronunciations` using context.
5. Map AD-Latin to the engine's phonemes (longest symbols first: `kh gh sh ch zh aw ay`).
6. For unknown words, use G2P with the Afghan rules (final ه → a, و → w, q ≠ gh, mē-, majhul vowels), not Iranian Persian defaults.

A lexicon fixes word pronunciation only. A natural Afghan voice also needs native Kabul Dari recordings and acoustic-model training or adaptation.

## Review workflow

```bash
python3 scripts/review_csv.py export            # writes review/review_sheet.csv
# reviewers fill: verification_status, reviewed_pronunciation, reviewer_*, audio_reference, decision
python3 scripts/review_csv.py import reviewed.csv
python3 scripts/validate.py
```

Statuses: `unverified`, `in_review`, `verified`, `verified_multiple`, `corrected`, `disputed`, `rejected`. Review high-priority entries first (contracted Kabuli verb forms, loanwords, homographs, technical poultry and veterinary terms). Poultry terms should also be checked by an Afghan poultry farmer or veterinarian. Recordings: one WAV per entry, named by `id`.

## Editing and rebuilding

Edit `source/*.txt` (`word|pronunciation|c=colloquial|a=alt1;alt2|n=note|r=Variety: form|p`), then:

```bash
python3 scripts/build.py && python3 scripts/validate.py
```

`build.py` carries existing review results over to the rebuilt file, matched by word, so reviews are not lost.


Thanks!
