import json
from pathlib import Path

from src.extraction.pdf_text_extractor import extract_text_from_pdf
from src.extraction.scr_metadata_extractor import extract_metadata


PDF_DIR = Path("data/raw_pdfs/2021")
OUTPUT_FILE = Path("data/output/sample_50_metadata_2021.json")


def main():
    print("\n=== SAMPLE EXTRACTION: FIRST 50 PDFs (2021) ===\n")

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))[:50]

    if not pdf_files:
        print("No PDFs found in 2021 folder.")
        return

    results = []

    for idx, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{idx}/50] Processing: {pdf_path.name}")

        try:
            text = extract_text_from_pdf(str(pdf_path))
            metadata = extract_metadata(text)

            # metadata is already a dictionary
            results.append(metadata)

        except Exception as e:
            print(f"❌ Failed: {pdf_path.name} -> {e}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n=== DONE ===")
    print(f"Saved to: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
