import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

from src.utils import pipeline_logger
from src.acquisition.sci_judgement_date_client import SCIJudgementDateClient
from src.acquisition.sci_pdf_downloader import SCIPDFDownloader


# ============================================================
# DATE RANGE GENERATOR WITH STRICT VALIDATION + DEBUG PREVIEW
# ============================================================

class DateRangeGenerator:
    """
    Generates strict 30-day batches with validation.

    Guarantees:
    • No overlaps
    • No missing days
    • No batch > 30 days
    • Full Jan 1 → Dec 31 coverage
    """

    @staticmethod
    def generate_batches(year: int, validate: bool = True) -> List[Tuple[str, str]]:
        batches = []

        current = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)

        previous_end = None

        while current <= year_end:

            batch_end = min(current + timedelta(days=29), year_end)

            # ---------- VALIDATION ----------
            if validate:
                window_size = (batch_end - current).days + 1

                if window_size > 30:
                    raise ValueError(
                        f"Invalid batch size >30 days: {current} → {batch_end}"
                    )

                if previous_end:
                    if current != previous_end + timedelta(days=1):
                        raise ValueError(
                            f"Gap or overlap detected between "
                            f"{previous_end} and {current}"
                        )
            # --------------------------------

            batches.append(
                (
                    current.strftime("%d-%m-%Y"),
                    batch_end.strftime("%d-%m-%Y"),
                )
            )

            previous_end = batch_end
            current = batch_end + timedelta(days=1)

        # Final coverage check
        if validate:
            first_start = datetime.strptime(batches[0][0], "%d-%m-%Y")
            last_end = datetime.strptime(batches[-1][1], "%d-%m-%Y")

            if first_start != datetime(year, 1, 1):
                raise ValueError("Year does not start at Jan 1")

            if last_end != datetime(year, 12, 31):
                raise ValueError("Year does not end at Dec 31")

        return batches


# ============================================================
# MAIN PIPELINE
# ============================================================

class SCIPipeline2021to2026:

    YEARS = [2024]
    #YEARS = [2021]


    def __init__(self):
        self.downloader = SCIPDFDownloader()
        self.client = None
        self.total_links_found = 0
        self.total_pdfs_downloaded = 0
        self.total_failures = 0
        self.year_results = {}

    # ========================================================
    # PROCESS SINGLE YEAR
    # ========================================================

    def process_year(self, year: int) -> dict:

        pipeline_logger.info("\n" + "=" * 70)
        pipeline_logger.info(f"PROCESSING YEAR: {year}")
        pipeline_logger.info("=" * 70)

        year_stats = {
            "year": year,
            "batches_processed": 0,
            "total_links_found": 0,
            "total_downloaded": 0,
            "total_failed": 0,
            "batch_results": [],
        }

        try:
            batches = DateRangeGenerator.generate_batches(year)

            pipeline_logger.info(f"Generated {len(batches)} date batches")

            # ---------- DEBUG PREVIEW ----------
            pipeline_logger.info("First 3 date windows:")
            for preview in batches[:3]:
                pipeline_logger.info(f"  {preview[0]} → {preview[1]}")

            pipeline_logger.info("Last 3 date windows:")
            for preview in batches[-3:]:
                pipeline_logger.info(f"  {preview[0]} → {preview[1]}")
            # -----------------------------------

            for batch_num, (from_date, to_date) in enumerate(batches, 1):

                pipeline_logger.info("")
                pipeline_logger.info(
                    f"[Batch {batch_num}/{len(batches)}] "
                    f"{from_date} → {to_date}"
                )

                batch_result = self.process_date_range(
                    from_date, to_date, year
                )

                year_stats["batches_processed"] += 1
                year_stats["total_links_found"] += batch_result.get("links_found", 0)
                year_stats["total_downloaded"] += batch_result.get("downloaded", 0)
                year_stats["total_failed"] += batch_result.get("failed", 0)
                year_stats["batch_results"].append(batch_result)

        except Exception as e:
            pipeline_logger.error(f"Error processing year {year}: {e}")
            year_stats["error"] = str(e)

        return year_stats

    # ========================================================
    # PROCESS SINGLE DATE RANGE
    # ========================================================

    def process_date_range(self, from_date: str, to_date: str, year: int) -> dict:

        batch_result = {
            "from_date": from_date,
            "to_date": to_date,
            "links_found": 0,
            "downloaded": 0,
            "failed": 0,
        }

        try:
            self.client = SCIJudgementDateClient()

            pipeline_logger.info(f"Searching: {from_date} → {to_date}")

            pdf_links = self.client.search_by_date_range(
                from_date, to_date
            )

            batch_result["links_found"] = len(pdf_links)
            self.total_links_found += len(pdf_links)

            if pdf_links:

                download_result = self.downloader.download_multiple(
                    pdf_links, year=year
                )

                batch_result["downloaded"] = download_result.successful_downloads
                batch_result["failed"] = download_result.failed_downloads

                self.total_pdfs_downloaded += download_result.successful_downloads
                self.total_failures += download_result.failed_downloads

            else:
                pipeline_logger.info("No PDFs found for this window.")

        except Exception as e:
            pipeline_logger.error(
                f"Error in batch {from_date} → {to_date}: {e}"
            )
            batch_result["error"] = str(e)

        finally:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None

        return batch_result

    # ========================================================
    # RUN FULL PIPELINE
    # ========================================================

    def run(self):

        pipeline_logger.info("\nSCI 2021-2026 ACQUISITION PIPELINE STARTED\n")

        start_time = datetime.now()

        try:
            for year in self.YEARS:
                year_result = self.process_year(year)
                self.year_results[year] = year_result

        except KeyboardInterrupt:
            pipeline_logger.warning("Pipeline interrupted by user")

        self.print_final_summary(start_time)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    def print_final_summary(self, start_time: datetime):

        end_time = datetime.now()
        duration = end_time - start_time

        pipeline_logger.info("\n" + "=" * 70)
        pipeline_logger.info("FINAL PIPELINE SUMMARY")
        pipeline_logger.info("=" * 70)

        pipeline_logger.info(
            f"Duration: {int(duration.total_seconds())} seconds"
        )

        pipeline_logger.info(f"Total links found: {self.total_links_found}")
        pipeline_logger.info(f"Total downloaded: {self.total_pdfs_downloaded}")

        if self.total_failures:
            pipeline_logger.warning(f"Total failures: {self.total_failures}")

        pipeline_logger.info("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    try:
        pipeline = SCIPipeline2021to2026()
        pipeline.run()
        return 0
    except Exception as e:
        pipeline_logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
