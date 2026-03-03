"""
ACQUISITION - SCI Judgement Date Client (Selenium-based)

Automated browser-based PDF discovery from official SCI website.
Includes structured logging and comprehensive error handling.

Usage:
    client = SCIJudgementDateClient()
    links = client.search_by_date_range("01-01-2021", "31-01-2021")
    client.close()
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.utils import pipeline_logger


class SCIJudgementDateClient:
    """
    Selenium-based client for SCI judgement date discovery.

    Handles:
    - Browser automation for date range search
    - Manual CAPTCHA solution with user input
    - Automatic PDF link extraction from results
    - Graceful error handling and structured logging
    """

    def __init__(self):
        """Initialize Chrome browser with anti-detection options."""
        pipeline_logger.info("=" * 70)
        pipeline_logger.info("INITIALIZING SELENIUM CHROME BROWSER")
        pipeline_logger.info("=" * 70)

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, 30)
            pipeline_logger.info("✓ Chrome browser launched successfully")
        except Exception as e:
            pipeline_logger.error(f"Failed to launch Chrome: {e}")
            raise

    def open_page(self):
        """Navigate to SCI judgement date search page."""
        pipeline_logger.info("Opening official SCI judgement date page...")
        pipeline_logger.info("URL: https://www.sci.gov.in/judgements-judgement-date/")

        try:
            self.driver.get("https://www.sci.gov.in/judgements-judgement-date/")

            # Wait for from_date field to be present
            self.wait.until(EC.presence_of_element_located((By.ID, "from_date")))
            pipeline_logger.info("✓ Page loaded, date fields found")

        except Exception as e:
            pipeline_logger.error(f"Failed to open SCI page: {e}")
            raise

    def fill_dates(self, from_date: str, to_date: str) -> bool:
        """
        Fill date fields using JavaScript (bypasses UI interaction).

        Args:
            from_date: Start date in dd-mm-yyyy format
            to_date: End date in dd-mm-yyyy format

        Returns:
            True if successful, False otherwise
        """
        pipeline_logger.debug(f"Filling dates: {from_date} → {to_date}")

        try:
            # Set from_date using JavaScript
            self.driver.execute_script(
                "document.getElementById('from_date').value = arguments[0];",
                from_date,
            )
            pipeline_logger.debug(f"✓ Set from_date = {from_date}")

            # Set to_date using JavaScript (FIX: use arguments[1], not arguments[0])
            self.driver.execute_script(
                "document.getElementById('to_date').value = arguments[0];",
                to_date,
            )
            pipeline_logger.debug(f"✓ Set to_date = {to_date}")

            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to fill dates: {e}")
            return False

    def click_search(self) -> bool:
        """
        Manually solve CAPTCHA, then automatically click search.

        This method:
        1. Pauses execution
        2. Prompts user to solve CAPTCHA manually in browser
        3. Waits for user confirmation
        4. Automatically clicks search button
        5. Waits for results to load

        Returns:
            True if search succeeded, False otherwise
        """
        pipeline_logger.warning("=" * 70)
        pipeline_logger.warning("⚠️  MANUAL CAPTCHA SOLUTION REQUIRED")
        pipeline_logger.warning("=" * 70)
        pipeline_logger.warning("")
        pipeline_logger.warning("ACTION REQUIRED:")
        pipeline_logger.warning("  1. Look at the Chrome browser")
        pipeline_logger.warning("  2. Solve the CAPTCHA if present")
        pipeline_logger.warning("  3. Return to this terminal")
        pipeline_logger.warning("  4. Press ENTER to continue")
        pipeline_logger.warning("")

        try:
            # Wait for user to manually solve CAPTCHA
            input("Press ENTER after solving CAPTCHA: ")
            pipeline_logger.info("✓ User confirmed CAPTCHA solved")

        except KeyboardInterrupt:
            pipeline_logger.error("User interrupted CAPTCHA solving")
            return False

        try:
            # Find and click search button
            pipeline_logger.debug("Locating search button...")
            search_button = self.driver.find_element(
                By.XPATH, "//input[@type='submit' and @value='Search']"
            )
            pipeline_logger.debug("✓ Search button found")

            # Click search button
            search_button.click()
            pipeline_logger.info("✓ Search button clicked automatically")

            # Wait for results table to appear
            pipeline_logger.debug("Waiting for results table...")
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
            pipeline_logger.info("✓ Results table loaded")

            # Small delay to ensure all results are rendered
            time.sleep(2)

            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to click search or wait for results: {e}")
            return False

    def extract_pdf_links(self) -> list:
        """
        Extract all PDF links from search results page.

        Filters for:
        - Links containing 'pdf' or 'pdfdate' or 'supremecourt'
        - Valid href attributes
        - Removes duplicates

        Returns:
            List of PDF URLs (deduplicated)
        """
        pipeline_logger.debug("Extracting PDF links from results...")

        try:
            # Find all <a> tags on page
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            pipeline_logger.debug(f"Found {len(all_links)} total links on page")

            pdf_links = []

            for link in all_links:
                try:
                    href = link.get_attribute("href")

                    # Skip empty hrefs
                    if not href:
                        continue

                    # Filter for PDF-related links
                    href_lower = href.lower()
                    if (
                        "pdf" in href_lower
                        or "pdfdate" in href_lower
                        or "supremecourt" in href_lower
                    ):
                        pdf_links.append(href)
                        pipeline_logger.debug(f"Found PDF link: {href[:80]}...")

                except Exception as e:
                    pipeline_logger.debug(f"Error processing link: {e}")
                    continue

            # Remove duplicates while preserving order
            unique_links = []
            seen = set()
            for link in pdf_links:
                if link not in seen:
                    unique_links.append(link)
                    seen.add(link)

            pipeline_logger.info(
                f"✓ Extracted {len(unique_links)} unique PDF links "
                f"(from {len(pdf_links)} total)"
            )

            return unique_links

        except Exception as e:
            pipeline_logger.error(f"Failed to extract PDF links: {e}")
            return []
    def extract_rows_with_metadata(self) -> list:
        """
        Extract structured metadata from results table.

        Returns:
            List of dictionaries containing row-level metadata
        """
        pipeline_logger.debug("Extracting structured row metadata...")

        try:
            rows = self.driver.find_elements(By.XPATH, "//table//tbody/tr")

            pipeline_logger.info(f"Found {len(rows)} result rows")

            records = []

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")

                if len(cols) < 8:
                    continue

                judgment_cell = cols[7]
                links = judgment_cell.find_elements(By.TAG_NAME, "a")

                pdf_url = None
                for link in links:
                    href = link.get_attribute("href")
                    if href and href.endswith(".pdf"):
                        pdf_url = href
                        break

                record = {
                    "serial_number": cols[0].text.strip(),
                    "diary_number": cols[1].text.strip(),
                    "case_number": cols[2].text.strip(),
                    "parties": cols[3].text.strip(),
                    "advocate": cols[4].text.strip(),
                    "bench": cols[5].text.strip(),
                    "judgment_by": cols[6].text.strip(),
                    "judgment_raw": judgment_cell.text.strip(),
                    "pdf_url": pdf_url,
                }

                records.append(record)

            pipeline_logger.info(
                f"✓ Extracted structured metadata for {len(records)} rows"
            )

            return records

        except Exception as e:
            pipeline_logger.error(f"Failed to extract structured metadata: {e}")
            return []
            
    def search_by_date_range(self, from_date: str, to_date: str) -> list:
        """
        Complete search workflow for a date range.

        Orchestrates:
        1. Open page
        2. Fill dates
        3. Manual CAPTCHA solution
        4. Automatic search
        5. Extract links

        Args:
            from_date: Start date in dd-mm-yyyy format
            to_date: End date in dd-mm-yyyy format

        Returns:
            List of PDF URLs found in this date range
        """
        pipeline_logger.info("=" * 70)
        pipeline_logger.info(f"SEARCHING DATE RANGE: {from_date} → {to_date}")
        pipeline_logger.info("=" * 70)

        try:
            # Step 1: Open page
            self.open_page()

            # Step 2: Fill dates
            if not self.fill_dates(from_date, to_date):
                pipeline_logger.error(f"Failed to fill dates for {from_date} → {to_date}")
                return []

            # Step 3 & 4: Manual CAPTCHA + automatic search
            if not self.click_search():
                pipeline_logger.error(f"Failed to complete search for {from_date} → {to_date}")
                return []

            # Step 5: Extract PDF links
            links = self.extract_pdf_links()

            pipeline_logger.info(
                f"✓ Date range {from_date} → {to_date}: {len(links)} PDFs found"
            )

            return links

        except Exception as e:
            pipeline_logger.error(f"Error during date range search: {e}")
            return []
    def search_with_metadata_by_date_range(self, from_date: str, to_date: str) -> list:
        """
        Same as search_by_date_range, but returns structured row metadata.
        """

        pipeline_logger.info("=" * 70)
        pipeline_logger.info(f"SEARCHING WITH METADATA: {from_date} → {to_date}")
        pipeline_logger.info("=" * 70)

        try:
            self.open_page()

            if not self.fill_dates(from_date, to_date):
                return []

            if not self.click_search():
                return []

            return self.extract_rows_with_metadata()

        except Exception as e:
            pipeline_logger.error(f"Error during metadata search: {e}")
            return []
        
    def close(self):
        """Close browser and cleanup."""
        try:
            pipeline_logger.info("Closing browser...")
            self.driver.quit()
            pipeline_logger.info("✓ Browser closed")
        except Exception as e:
            pipeline_logger.error(f"Error closing browser: {e}")


# ==================== MANUAL TESTING ====================

if __name__ == "__main__":
    """Manual testing - not part of automated pipeline."""
    client = SCIJudgementDateClient()

    try:
        # Test single date range
        from_date = input("Enter FROM date (dd-mm-yyyy): ")
        to_date = input("Enter TO date (dd-mm-yyyy): ")

        links = client.search_by_date_range(from_date, to_date)

        if links:
            print(f"\nFound {len(links)} PDF links:")
            for i, link in enumerate(links, 1):
                print(f"  {i}. {link}")
        else:
            print("\nNo PDF links found")

    finally:
        client.close()
