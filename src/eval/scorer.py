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
        return fuzz.token_sort_ratio(str(truth_val), str(pred_val).lower()) / 100
    if field == "amount":
        try:
            return 1.0 if abs(float(truth_val) - float(pred_val)) < 0.01 else 0.0
        except (ValueError, TypeError):
            return 0.0
    return 1.0 if str(truth_val).strip().lower() == str(pred_val).strip().lower() else 0.0

def main():
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    fields = ["vendor", "invoice_number", "date", "amount", "currency"]
    results = {}

    for model_dir in RAW_OUTPUTS_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        field_scores = {f: [] for f in fields}

        for bill_file in model_dir.glob("*.json"):
            bill_id = bill_file.stem
            if bill_id not in ground_truth:
                continue
            pred = json.loads(bill_file.read_text())
            truth = ground_truth[bill_id]
            for f in fields:
                field_scores[f].append(score_field(f, truth.get(f), pred.get(f)))

        results[model] = {f: sum(v)/len(v) if v else 0 for f, v in field_scores.items()}

    for model, scores in results.items():
        print(f"\n{model}:")
        for f, s in scores.items():
            print(f"  {f}: {s:.2f}")

if __name__ == "__main__":
    main()