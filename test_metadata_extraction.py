from src.acquisition.sci_judgement_date_client import SCIJudgementDateClient

client = SCIJudgementDateClient()

try:
    rows = client.search_with_metadata_by_date_range(
        "01-01-2021",
        "31-01-2021"
    )

    print("Total rows extracted:", len(rows))

    if rows:
        print("\nFirst row sample:\n")
        for key, value in rows[0].items():
            print(f"{key}: {value}")

finally:
    client.close()