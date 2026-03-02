from acquisition.sci_judgement_date_client import SCIJudgementDateClient


def main():
    client = SCIJudgementDateClient()

    print("Initializing client...")
    client.initialize()

    from_date = input("Enter FROM date (dd-mm-yyyy): ")
    to_date = input("Enter TO date (dd-mm-yyyy): ")
    captcha = input("Enter CAPTCHA value: ")

    print("Fetching results...")
    html = client.fetch_results_html(from_date, to_date, captcha)

    pdf_links = client.extract_pdf_links(html)

    print(f"\nTotal PDF links found: {len(pdf_links)}\n")

    for link in pdf_links:
        print(link)


if __name__ == "__main__":
    main()
