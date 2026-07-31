import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.extractors.gemini_extractor import GeminiExtractor
from src.extractors.openai_extractor import OpenAIExtractor

RAW_BILLS_DIR = Path("data/raw_bills")
GROUND_TRUTH_PATH = Path("data/ground_truth.json")
RESULTS_DIR = Path("results/raw_outputs")


def get_extractors():
    extractors = []
    if os.getenv("GEMINI_API_KEY"):
        extractors.append(GeminiExtractor())
    # if os.getenv("GEMINI_API_KEY"):
    #     extractors.append(GeminiExtractor())
    # if os.getenv("OPENAI_API_KEY"):
    #     extractors.append(OpenAIExtractor())
    return extractors


def find_image_path(bill_id: str) -> Path | None:
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = RAW_BILLS_DIR / f"{bill_id}{ext}"
        if candidate.exists():
            return candidate
    return None


def main():
    with open(GROUND_TRUTH_PATH) as f:
        ground_truth = json.load(f)

    extractors = get_extractors()
    if not extractors:
        print("No extractors available. Check .env has valid API key(s).")
        return

    for bill_id in ground_truth:
        image_path = find_image_path(bill_id)
        if not image_path:
            print(f"[skip] no image found for {bill_id}")
            continue

        for extractor in extractors:
            out_dir = RESULTS_DIR / extractor.name
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{bill_id}.json"

            print(f"[run] {extractor.name} -> {bill_id}")
            try:
                result = extractor.extract(str(image_path), bill_id)
                out_path.write_text(result.model_dump_json(indent=2))
                print(f"  saved {out_path}")
            except Exception as e:
                print(f"  [error] {extractor.name} on {bill_id}: {e}")


if __name__ == "__main__":
    main()