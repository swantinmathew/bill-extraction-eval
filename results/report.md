# Accuracy per model per field

| Model | vendor | invoice_number | date | amount | currency |
|---|---|---|---|---|---|
| gemini | 0.90 | 0.92 | 0.92 | 0.83 | 1.00 |
| openai | 0.92 | 0.75 | 0.25 | 0.42 | 1.00 |

# Date extraction breakdown (year / month / day)

| Model | year | month | day |
|---|---|---|---|
| gemini | 0.92 | 1.00 | 1.00 |
| openai | 0.75 | 0.42 | 0.50 |

# Amount mismatches: mean vs median vs worst case

| Model | Bills wrong | Avg error | Median error | Max error |
|---|---|---|---|---|
| gemini | 2 | 7.7% | 7.7% | 12.2% |
| openai | 7 | 61.9% | 15.3% | 233.3% |
# Estimated cost per model

| Model | Cost/bill | Cost/100 bills | Total for dataset |
|---|---|---|---|
| gemini | $0.000105 | $0.0105 | $0.0013 |
| openai | $0.00021 | $0.021 | $0.0025 |