import json
from pathlib import Path

PRICING = {
    "gemini": {"input": 0.000075, "output": 0.0003},
    "openai": {"input": 0.00015, "output": 0.0006},
}

RAW_OUTPUTS_DIR = Path("results/raw_outputs")


def compute_cost(model, input_tokens, output_tokens):
    rates = PRICING.get(model)
    if not rates or input_tokens is None or output_tokens is None:
        return None
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])


def main():
    lines = ["\n# Estimated cost per model (from logged token usage where available)\n"]
    lines.append("| Model | Bills w/ real usage | Avg cost/bill | Cost/100 bills | Total for dataset |")
    lines.append("|---|---|---|---|---|")

    for model_dir in RAW_OUTPUTS_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        costs = []
        real_count = 0

        for bill_file in model_dir.glob("*.json"):
            data = json.loads(bill_file.read_text())
            it, ot = data.get("input_tokens"), data.get("output_tokens")
            cost = compute_cost(model, it, ot)
            if cost is not None:
                costs.append(cost)
                real_count += 1

        print(f"\n{model}: {real_count} bills with logged token usage")
        if costs:
            avg = sum(costs) / len(costs)
            print(f"  avg cost/bill: ${avg:.6f}")
            print(f"  cost/100 bills: ${avg*100:.4f}")
            lines.append(f"| {model} | {real_count} | ${avg:.6f} | ${avg*100:.4f} | ${sum(costs):.4f} |")
        else:
            print("  no logged usage found — rerun extraction to populate input_tokens/output_tokens")
            lines.append(f"| {model} | 0 | N/A | N/A | N/A |")

    with open("results/report.md", "a") as f:
        f.write("\n".join(lines))
    print("\nAppended to results/report.md")


if __name__ == "__main__":
    main()