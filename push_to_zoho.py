import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from src.zoho.zoho_client import create_expense

ACCOUNT_ID = "4035565000000000558"
BEST_MODEL = "gemini"
OUTPUTS_DIR = Path(f"results/raw_outputs/{BEST_MODEL}")

def main():
    for bill_file in sorted(OUTPUTS_DIR.glob("*.json")):
        bill_data = json.loads(bill_file.read_text())
        if not bill_data.get("amount"):
            print(f"[skip] {bill_file.stem} - no amount extracted")
            continue
        print(f"[push] {bill_file.stem}")
        result = create_expense(bill_data, ACCOUNT_ID)
        if "expense" in result:
            print(f"  success, expense_id: {result['expense']['expense_id']}")
        else:
            print(f"  [error] {result}")

if __name__ == "__main__":
    main()