import requests
import os

TEST_URL = "https://api.sci.gov.in//pdfdate/index1.php?dt=2021-01-29&dno=7462021&filename=supremecourt/2021/746/746_2021_36_21_25733_Judgement_29-Jan-2021.pdf"

OUTPUT_FILE = "test_download.pdf"


def download_pdf(url, output_path):
    print("Downloading:", url)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.sci.gov.in/"
    }

    response = requests.get(url, headers=headers, timeout=30)

    print("Status Code:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))

    if response.status_code != 200:
        print("❌ Failed request.")
        return False

    content = response.content

    # Find actual PDF header
    pdf_start = content.find(b"%PDF")

    if pdf_start == -1:
        print("❌ PDF header not found.")
        return False

    clean_pdf = content[pdf_start:]

    with open(output_path, "wb") as f:
        f.write(clean_pdf)

    print("✅ Cleaned PDF saved as:", output_path)
    print("File size:", os.path.getsize(output_path), "bytes")
    return True


if __name__ == "__main__":
    download_pdf(TEST_URL, OUTPUT_FILE)
