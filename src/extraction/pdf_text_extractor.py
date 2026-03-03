import pdfplumber
from pathlib import Path

def split_text_into_chunks(text: str, chunk_size: int = 3000) -> list:
    """
    Splits long PDF text into smaller chunks.

    Args:
        text (str): Full PDF text
        chunk_size (int): Approximate characters per chunk

    Returns:
        list[str]: List of text chunks
    """

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end

    return chunks
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract full text from a PDF using pdfplumber.

    Args:
        pdf_path (str): Path to PDF file

    Returns:
        str: Extracted text (empty string if failed)
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return ""

    full_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text()
                    if text:
                        full_text.append(text.strip())
                except Exception as page_error:
                    print(f"Error extracting page {page_number}: {page_error}")

    except Exception as e:
        print(f"Failed to open PDF: {e}")
        return ""

    return "\n\n".join(full_text)


if __name__ == "__main__":
    # Example manual test
    pdf_file = "../../test_download.pdf"

    text = extract_text_from_pdf(pdf_file)

    print("---- FIRST 1000 CHARACTERS ----\n")
    print(text[:1000])
