import json
from pathlib import Path
from rapidfuzz import fuzz

GROUND_TRUTH_PATH = Path("data/ground_truth.json")
RAW_OUTPUTS_DIR = Path("results/raw_outputs")


def score_field(field, truth_val, pred_val):
    if truth_val is None and pred_val is None:
        return 1.0
    if pred_val is None or truth_val is None:
        return 0.0
    if field == "vendor":
        return fuzz.partial_ratio(str(truth_val).lower(), str(pred_val).lower()) / 100
    if field == "amount":
        try:
            return 1.0 if abs(float(truth_val) - float(pred_val)) < 0.01 else 0.0
        except (ValueError, TypeError):
            return 0.0
    # exact match, case-insensitive — covers date, currency, invoice_number
    return 1.0 if str(truth_val).strip().lower() == str(pred_val).strip().lower() else 0.0


def score_date_components(truth_date, pred_date):
    """Diagnostic breakdown of date accuracy by year/month/day, separate from
    the strict exact-match 'date' field score above."""
    if truth_date is None and pred_date is None:
        return {"year": 1.0, "month": 1.0, "day": 1.0}
    if truth_date is None or pred_date is None:
        return {"year": 0.0, "month": 0.0, "day": 0.0}
    try:
        ty, tm, td = truth_date.split("-")
        py, pm, pd = pred_date.split("-")
        return {
            "year": 1.0 if ty == py else 0.0,
            "month": 1.0 if tm == pm else 0.0,
            "day": 1.0 if td == pd else 0.0,
        }
    except (ValueError, AttributeError):
        return {"year": 0.0, "month": 0.0, "day": 0.0}


def amount_error_pct(truth_val, pred_val):
    """Diagnostic: when amount is wrong, how far off was it (%)? None if either
    value is missing/unparseable, or if the amount was actually correct."""
    if truth_val is None or pred_val is None:
        return None
    try:
        truth_val, pred_val = float(truth_val), float(pred_val)
    except (ValueError, TypeError):
        return None
    if truth_val == 0:
        return None
    if abs(truth_val - pred_val) < 0.01:
        return None  # was correct, no error to report
    return abs(truth_val - pred_val) / truth_val * 100


def summarize_errors(error_pcts):
    """Mean alone is misleading with a small sample and a severe outlier —
    report median and max alongside it so one bad bill doesn't dominate
    the headline number without context."""
    if not error_pcts:
        return {"count_wrong": 0, "avg_error_pct": None, "median_error_pct": None, "max_error_pct": None}
    sorted_errs = sorted(error_pcts)
    n = len(sorted_errs)
    median = sorted_errs[n // 2] if n % 2 else (sorted_errs[n // 2 - 1] + sorted_errs[n // 2]) / 2
    return {
        "count_wrong": n,
        "avg_error_pct": sum(error_pcts) / n,
        "median_error_pct": median,
        "max_error_pct": max(error_pcts),
    }


def main():
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    fields = ["vendor", "invoice_number", "date", "amount", "currency"]
    results = {}
    date_breakdown = {}
    amount_summaries = {}

    for model_dir in RAW_OUTPUTS_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        field_scores = {f: [] for f in fields}
        date_components = {"year": [], "month": [], "day": []}
        error_pcts = []

        for bill_file in model_dir.glob("*.json"):
            bill_id = bill_file.stem
            if bill_id not in ground_truth:
                continue
            pred = json.loads(bill_file.read_text())
            truth = ground_truth[bill_id]

            for f in fields:
                field_scores[f].append(score_field(f, truth.get(f), pred.get(f)))

            components = score_date_components(truth.get("date"), pred.get("date"))
            for comp in ["year", "month", "day"]:
                date_components[comp].append(components[comp])

            err = amount_error_pct(truth.get("amount"), pred.get("amount"))
            if err is not None:
                error_pcts.append(err)

        results[model] = {f: sum(v) / len(v) if v else 0 for f, v in field_scores.items()}
        date_breakdown[model] = {
            comp: sum(v) / len(v) if v else 0 for comp, v in date_components.items()
        }
        amount_summaries[model] = summarize_errors(error_pcts)

    # ---- print to terminal ----
    for model, scores in results.items():
        print(f"\n{model}:")
        for f, s in scores.items():
            print(f"  {f}: {s:.2f}")
        print(f"  date breakdown -> year: {date_breakdown[model]['year']:.2f}, "
              f"month: {date_breakdown[model]['month']:.2f}, "
              f"day: {date_breakdown[model]['day']:.2f}")
        ae = amount_summaries[model]
        if ae["avg_error_pct"] is not None:
            print(f"  amount mismatches: {ae['count_wrong']} bills | "
                  f"avg {ae['avg_error_pct']:.1f}% | "
                  f"median {ae['median_error_pct']:.1f}% | "
                  f"max {ae['max_error_pct']:.1f}%")
        else:
            print("  amount mismatches: none")

    # ---- write results/report.md ----
    lines = ["# Accuracy per model per field\n"]
    lines.append("| Model | " + " | ".join(fields) + " |")
    lines.append("|---" * (len(fields) + 1) + "|")
    for model, scores in results.items():
        row = f"| {model} | " + " | ".join(f"{scores[f]:.2f}" for f in fields) + " |"
        lines.append(row)

    lines.append("\n# Date extraction breakdown (year / month / day)\n")
    lines.append("| Model | year | month | day |")
    lines.append("|---|---|---|---|")
    for model, comp in date_breakdown.items():
        row = f"| {model} | {comp['year']:.2f} | {comp['month']:.2f} | {comp['day']:.2f} |"
        lines.append(row)

    lines.append("\n# Amount mismatches: mean vs median vs worst case\n")
    lines.append("| Model | Bills wrong | Avg error | Median error | Max error |")
    lines.append("|---|---|---|---|---|")
    for model, ae in amount_summaries.items():
        if ae["avg_error_pct"] is not None:
            row = (f"| {model} | {ae['count_wrong']} | {ae['avg_error_pct']:.1f}% | "
                   f"{ae['median_error_pct']:.1f}% | {ae['max_error_pct']:.1f}% |")
        else:
            row = f"| {model} | 0 | N/A | N/A | N/A |"
        lines.append(row)

    Path("results/report.md").write_text("\n".join(lines))
    print("\nSaved to results/report.md")


if __name__ == "__main__":
    main()