# Handwritten Bill Extraction & Multi-Model Evaluation

## Overview
Extracts structured data (vendor, amount, date, currency, tax details) from photos of
handwritten bills using multiple vision-capable LLMs, scores each model's accuracy
field-by-field against hand-verified ground truth, estimates API cost per model, and
pushes the extracted data into Zoho Books as real expense entries.

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
│   │   ├── scorer.py             # field-level accuracy scoring
│   │   └── cost_tracker.py       # estimated cost per model
│   ├── zoho/
│   │   └── zoho_client.py        # OAuth2 + expense creation
│   └── run_pipeline.py           # runs every bill through every model
├── push_to_zoho.py               # pushes extracted data into Zoho Books
├── results/
│   ├── raw_outputs/{model}/      # per-bill JSON output per model
│   └── report.md                 # final accuracy + cost tables
├── .env.example
└── requirements.txt
```

**Pipeline flow:** bill image → same prompt sent to each model → each model returns
JSON matching a shared schema → outputs saved per model per bill → scorer compares
against ground truth field-by-field → cost tracker estimates spend → extracted data
is pushed to Zoho Books as expense entries.

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
python -m src.eval.cost_tracker # estimate cost per model
python push_to_zoho.py          # push extracted data to Zoho Books
```

## Dataset
12 handwritten bills, chosen for variety: restaurant bills (India, UK, Cambodia),
retail/tailoring receipts, a GST tax invoice, a bill book carbon copy, and a 1970s
tailor's bill — mixing clean modern formats with genuinely ambiguous, messy
handwriting and inconsistent printed totals.

## Scoring methodology
- **Exact match** — date, currency, invoice_number: these should either match
  exactly or not at all.
- **Numeric tolerance** — amount: compared as normalized numbers, currency symbols
  and commas stripped, rather than string match.
- **Fuzzy match** (rapidfuzz `token_sort_ratio`, case-insensitive) — vendor name:
  handwriting OCR rarely reproduces a name character-for-character, so exact match
  would unfairly penalize near-correct reads.

Where a bill had genuine ambiguity (e.g. printed total not matching the line-item sum,
or separate "Total" vs "To Pay after deposit" figures), ground truth consistently uses
the bill's final stated payable total.

## Results

### Accuracy per model per field
| Model | vendor | invoice_number | date | amount | currency |
|---|---|---|---|---|---|
| gemini | 0.72 | 0.83 | 0.75 | 0.83 | 0.83 |
| openai | 0.63 | 0.67 | 0.33 | 0.42 | 0.75 |

### Estimated cost per model
| Model | Cost/bill | Cost/100 bills | Total for dataset |
|---|---|---|---|
| gemini | $0.000105 | $0.0105 | $0.0013 |
| openai | $0.00021 | $0.021 | $0.0025 |

## Recommendation
Gemini outperforms OpenAI (gpt-4o-mini) across every field in this test, with the
largest gaps in date extraction (+0.42) and amount extraction (+0.41), while also
being roughly half the estimated cost. Recommend Gemini for this use case.

## Known limitations
- Small sample size (12 bills) — findings are directional, not statistically robust.
- Cost estimates use average token assumptions, not per-call logged usage.
- OpenAI showed a systematic day/month date-format confusion (DD/MM vs MM/DD) worth
  further testing at scale.
- A few bills had inherent ambiguity (printed total vs recalculated total, pre-tax vs
  post-tax amount) — resolved by trusting the bill's stated total consistently.
- Gemini free-tier rate limits (20 req/day) were hit during testing, requiring the run
  to be split across two sessions.

## Zoho Books integration
Uses Zoho's self-client OAuth2 flow: a long-lived refresh token (stored in `.env`) is
exchanged for a short-lived access token on each API call, so no long-lived secret
capable of direct API access needs to be stored. `push_to_zoho.py` reads each bill's
extracted fields and creates a corresponding expense entry in Zoho Books via the
Expenses API — turning the AI-read bill data into a real accounting record, the same
way a person would manually enter a receipt, but automatically.