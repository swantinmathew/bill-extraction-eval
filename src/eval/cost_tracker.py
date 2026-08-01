import json
from pathlib import Path

# Rough public pricing per 1K tokens (verify current rates before final report)
PRICING = {
    "gemini": {"input": 0.000075, "output": 0.0003},   # gemini-flash approx
    "openai": {"input": 0.00015, "output": 0.0006},    # gpt-4o-mini approx
}

RAW_OUTPUTS_DIR = Path("results/raw_outputs")

def estimate_cost(model, num_bills, avg_input_tokens=800, avg_output_tokens=150):
    rates = PRICING.get(model)
    if not rates:
        return None
    cost_per_bill = (avg_input_tokens/1000 * rates["input"]) + (avg_output_tokens/1000 * rates["output"])
    return {
        "cost_per_bill": round(cost_per_bill, 6),
        "cost_per_100_bills": round(cost_per_bill * 100, 4),
        "total_for_dataset": round(cost_per_bill * num_bills, 4)
    }

def main():
    lines = ["\n# Estimated cost per model\n"]
    lines.append("| Model | Cost/bill | Cost/100 bills | Total for dataset |")
    lines.append("|---|---|---|---|")

    for model_dir in RAW_OUTPUTS_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        num_bills = len(list(model_dir.glob("*.json")))
        est = estimate_cost(model, num_bills)
        print(f"\n{model} ({num_bills} bills processed):")
        if est:
            for k, v in est.items():
                print(f"  {k}: ${v}")
            lines.append(f"| {model} | ${est['cost_per_bill']} | ${est['cost_per_100_bills']} | ${est['total_for_dataset']} |")
        else:
            print("  no pricing data")

    with open("results/report.md", "a") as f:
        f.write("\n".join(lines))
    print("\nAppended to results/report.md")

if __name__ == "__main__":
    main()