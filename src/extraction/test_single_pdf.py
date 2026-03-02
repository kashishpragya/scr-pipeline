import sys
from pathlib import Path
from pprint import pprint

from src.extraction.pdf_text_extractor import extract_text_from_pdf
from src.extraction.scr_metadata_extractor import extract_metadata


def main():
    # Change this to any PDF you want to test
    pdf_path = Path(
        "data/raw_pdfs/2021/70_2020_36_1503_26554_Judgement_01-Mar-2021.pdf"
    )

    if not pdf_path.exists():
        print("❌ PDF not found:", pdf_path)
        sys.exit(1)

    print("\n==============================")
    print("Reading PDF...")
    print("==============================\n")

    text = extract_text_from_pdf(str(pdf_path))

    if not text.strip():
        print("❌ No text extracted from PDF.")
        sys.exit(1)

    print("Text extraction successful.")
    print("Total characters extracted:", len(text))

    print("\n==============================")
    print("Extracting metadata...")
    print("==============================\n")

    metadata = extract_metadata(text)

    print("\n==== METADATA OUTPUT ====\n")
    pprint(metadata)


if __name__ == "__main__":
    main()
