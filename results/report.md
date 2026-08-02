# Accuracy per model per field

| Model | vendor | invoice_number | date | amount | currency |
|---|---|---|---|---|---|
| gemini | 0.90 | 0.92 | 1.00 | 1.00 | 1.00 |
| openai | 0.93 | 0.67 | 0.25 | 0.50 | 1.00 |

# Date extraction breakdown (year / month / day)

| Model | year | month | day |
|---|---|---|---|
| gemini | 1.00 | 1.00 | 1.00 |
| openai | 0.67 | 0.42 | 0.50 |

# Amount mismatches: mean vs median vs worst case

| Model | Bills wrong | Avg error | Median error | Max error |
|---|---|---|---|---|
| gemini | 0 | N/A | N/A | N/A |
| openai | 6 | 57.8% | 15.2% | 233.3% |
# Estimated cost per model (from logged token usage where available)

| Model | Bills w/ real usage | Avg cost/bill | Cost/100 bills | Total for dataset |
|---|---|---|---|---|
| gemini | 12 | $0.000121 | $0.0121 | $0.0014 |
| openai | 12 | $0.002683 | $0.2683 | $0.0322 |