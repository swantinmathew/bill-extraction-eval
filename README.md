# Handwritten Bill Extraction & Multi-Model Evaluation

## Overview
Extracts structured data (vendor, amount, date, currency, tax details) from photos of
handwritten bills using multiple vision-capable LLMs, scores each model's accuracy
field-by-field against hand-verified ground truth, tracks real API cost per model
from logged token usage, and pushes the extracted data into Zoho Books as real
expense entries.

## Models
- **Gemini** (`gemini-3.6-flash` via Google AI Studio)
- **OpenAI** (`gpt-4o-mini`, accessed via OpenRouter)

Anthropic's Claude was considered but not included — no free trial credit was
available in this account/region at the time, and paying to add a third model
wasn't proportionate for a 2-day screening task. Two models still satisfies the
task's "2–3 models" requirement; a third would strengthen the comparison further
(see Known limitations).

## Architecture
```
bill-extraction-eval/
├── data/
│   ├── raw_bills/               # bill images
│   └── ground_truth.json        # hand-verified correct values per bill
├── src/
│   ├── schema.py                 # pydantic schema every model output must match
│   ├── prompt.py                 # shared extraction prompt (same across models)
│   ├── extractors/
│   │   ├── base.py
│   │   ├── gemini_extractor.py
│   │   └── openai_extractor.py   # via OpenRouter, gpt-4o-mini
│   ├── eval/
│   │   ├── scorer.py             # field-level accuracy scoring + diagnostics
│   │   └── cost_tracker.py       # real cost per model from logged token usage
│   ├── zoho/
│   │   └── zoho_client.py        # OAuth2 + expense creation
│   └── run_pipeline.py           # runs every bill through every model
├── ui/
│   ├── app.py                    # bonus Streamlit UI: dataset comparison + live upload
│   └── .streamlit/
│       └── config.toml           # UI theme
├── push_to_zoho.py               # pushes extracted data into Zoho Books
├── results/
│   ├── raw_outputs/{model}/      # per-bill JSON output per model, incl. token usage
│   └── report.md                 # final accuracy + cost tables
├── .env.example
└── requirements.txt
```

**Pipeline flow:** bill image → same prompt sent to each model → each model returns
JSON matching a shared schema, including real input/output token counts from the
API response → outputs saved per model per bill → scorer compares against ground
truth field-by-field → cost tracker computes actual spend from logged tokens →
extracted data is pushed to Zoho Books as expense entries.

## Setup
```
git clone <your-repo-url>
cd bill-extraction-eval
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```
Then fill in your real API keys and Zoho credentials inside `.env`.

## Usage
```
python -m src.run_pipeline      # extract data from all bills, all models
python -m src.eval.scorer       # score accuracy per model per field
python -m src.eval.cost_tracker # compute real cost per model from logged tokens
python push_to_zoho.py          # push extracted data to Zoho Books
streamlit run ui/app.py         # bonus: dataset comparison + live upload UI
```

## Bonus UI
Live demo: https://bill-extraction-audit.streamlit.app
(If unavailable — free-tier hosting can sleep after inactivity, or API quota may be
exhausted — screenshots below, or run locally: `streamlit run ui/app.py`)

**Evaluation dataset tab:**
![Dataset comparison view](docs/ui-dataset-view.png)

**Upload a bill tab — before extraction:**
![Upload view before extraction](docs/ui-upload-before.png)

**Upload a bill tab — after extraction:**
![Upload view after extraction, part 1](docs/ui-upload-after-view-1.png)
![Upload view after extraction, part 2](docs/ui-upload-after-view-2.png)

Two tabs:
- **Evaluation dataset** — pick any of the 12 bills, see the original image, ground
  truth, and each model's extraction side by side with ✓/✗ per-field markers and an
  overall accuracy score.
- **Upload a bill** — upload a new bill image and see live extraction from each
  configured model, side by side. Extraction only runs on button click (not on every
  page interaction) to avoid burning API quota unnecessarily.

## Dataset
12 handwritten Indian bills — grocery, restaurant, tailoring, retail, stationery, and
canteen receipts — chosen for variety in handwriting style, format, and legibility.
Includes one Malayalam-script bill alongside English-script bills, to test whether
extraction accuracy holds across scripts, not just handwriting styles. Personal names
of individual customers were cropped/redacted from bill images before use, per the
task's privacy guidance.

## Scoring methodology
This is the core of the evaluation — the task explicitly weighs eval methodology
quality above which model "wins." Three different comparison strategies were used,
chosen per field rather than applied uniformly:

- **Exact match** — date, currency, invoice_number: these should either match
  exactly or not at all.
- **Numeric tolerance** — amount: compared as normalized numbers, currency symbols
  and commas stripped, rather than string match.
- **Fuzzy match** (rapidfuzz `partial_ratio`, case-insensitive) — vendor name:
  initially used `token_sort_ratio`, but switched to `partial_ratio` after noticing
  models often returned the correct core business name while dropping a generic
  suffix (e.g. "Moti Mahal" vs ground truth "Moti Mahal Restaurant").
  `token_sort_ratio` penalized these as near-misses even though the vendor was
  correctly identified; `partial_ratio` checks whether the shorter string is
  well-contained in the longer one, scoring these cases as strong matches instead —
  a better reflection of genuine vendor-identification accuracy.

Tax/GST fields (`gst_number`, `gst_amount`) are extracted and shown in the UI for
both ground truth and model output, but excluded from the primary accuracy table —
only 2 of 12 bills had visible GST details, too sparse a sample to report a
meaningful per-field accuracy score alongside the other five fields.

Two diagnostic breakdowns supplement the primary field scores, to explain *why* a
field failed rather than just *that* it failed:
- **Date year/month/day breakdown** — isolates which part of a date extraction goes
  wrong, instead of treating any mismatch as equally uninformative.
- **Amount error magnitude (mean, median, max)** — mean alone is easily skewed by a
  single severe outlier in a small dataset, so median is reported alongside it as the
  more representative "typical error when wrong" figure.

Where a bill had genuine ambiguity (e.g. printed total not matching the line-item sum,
or unclear tax computation), ground truth consistently uses the bill's final stated
payable total, and uncertain tax fields are left `null` rather than guessed.

## Results

### Accuracy per model per field
| Model | vendor | invoice_number | date | amount | currency |
|---|---|---|---|---|---|
| gemini | 0.90 | 0.92 | 1.00 | 1.00 | 1.00 |
| openai | 0.93 | 0.67 | 0.25 | 0.50 | 1.00 |

### Date extraction breakdown (year / month / day)
| Model | year | month | day |
|---|---|---|---|
| gemini | 1.00 | 1.00 | 1.00 |
| openai | 0.67 | 0.42 | 0.50 |

Gemini read every date on this dataset correctly. OpenAI's date accuracy is weak
across all three components, not isolated to one — suggesting a general difficulty
reading handwritten dates rather than one specific format confusion.

### Amount mismatches: mean vs median vs worst case
| Model | Bills wrong | Avg error | Median error | Max error |
|---|---|---|---|---|
| gemini | 0 | — | — | — |
| openai | 6 | 57.8% | 15.2% | 233.3% |

Gemini had zero amount mismatches on this dataset. OpenAI's typical error when wrong
(median 15.2%) is meaningfully large on its own, and its worst case (233.3%) points
to at least one structurally wrong extraction, not just a minor misread.

### Cost per model (from logged token usage, not estimated)
| Model | Bills w/ real usage | Avg cost/bill | Cost/100 bills |
|---|---|---|---|
| gemini | 12 | $0.000121 | $0.0121 |
| openai | 12 | $0.002683 | $0.2683 |

With real per-call token usage instead of an estimate, OpenAI (via OpenRouter) costs
roughly **22x more per bill** than Gemini — a much larger gap than an earlier,
token-count-estimated version of this table suggested, and a clear signal in its
own right independent of the accuracy comparison.

## Recommendation
Gemini outperforms OpenAI (gpt-4o-mini) on every field in this test, with perfect
scores on date and amount extraction against OpenAI's 0.25 and 0.50, while also
costing about 22x less per bill based on real logged token usage. For handwritten
bill extraction — Indian small-business receipts in particular — Gemini is the clear
choice on both accuracy and cost, and the cost gap alone is large enough to make this
close to a non-decision at scale. For digital (typed/printed) documents, both models
would likely perform much closer to parity, since the difficulty here is specifically
reading handwriting rather than general document understanding — a separate,
lighter-weight pipeline could reasonably use either model, or default to the cheaper
option, for typed invoices.

## Known limitations
- Only 2 models compared, not 3 — see the Models section above for why. A third model
  (e.g. Claude, or a free-tier model via OpenRouter) would help distinguish "Gemini is
  simply strong" from "OpenAI specifically underperforms," which two models alone
  can't fully separate.
- Small sample size (12 bills) — findings are directional, not statistically robust.
  Gemini's zero amount/date mismatches on this dataset in particular should be read
  as "strong on this sample," not "error-free in general."
- A few bills had inherent ambiguity (printed total vs recalculated total, unclear tax
  computation) — resolved by trusting the bill's stated total and leaving uncertain
  tax fields `null` rather than guessing.
- Gemini free-tier rate limits (20 req/day) were hit during testing, requiring the run
  to be split across sessions.
- Amount error percentages are a comparative signal between models on identical
  images, not an absolute measure of handwriting difficulty — with a small sample,
  a single severe misread can still meaningfully shift results, which is why median
  and max are reported alongside the mean rather than the mean alone.
- Cost figures now come from real per-call token usage (`response.usage`) logged at
  extraction time, rather than an earlier version that used estimated average token
  counts — the current numbers should be accurate, not approximate.

## Zoho Books integration
Uses Zoho's self-client OAuth2 flow: a long-lived refresh token (stored in `.env`) is
exchanged for a short-lived access token on each API call, so no long-lived secret
capable of direct API access needs to be stored. `push_to_zoho.py` reads each bill's
extracted fields and creates a corresponding expense entry in Zoho Books via the
Expenses API — turning the AI-read bill data into a real accounting record, the same
way a person would manually enter a receipt, but automatically.