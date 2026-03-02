"""
ACQUISITION MODULE - Implementation Guide

This document provides practical guidance for setting up and using the
PDF acquisition module with your official SCR sources.

"""

# ==================== QUICK START ====================

"""
STEP 1: Install Dependencies
-------------------------------
pip install -r requirements.txt

STEP 2: Register Your Sources
------------------------------
Create a Python script that registers your official SCR sources:

from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

# Register URLs for a specific year
urls_2010 = [
    "https://your-official-source.gov.in/scr_2010_volume_1.pdf",
    "https://your-official-source.gov.in/scr_2010_volume_2.pdf",
]

PDFSourceProvider.register_source(2010, urls_2010)

# Or from a config file, API, etc.

STEP 3: Download PDFs
---------------------
python -m src.acquisition.run_acquisition --year 2010

STEP 4: Extract
---------------
python -m src.pipeline.run_scr_pipeline --year 2010
"""

# ==================== IMPLEMENTATION PATTERNS ====================

"""
PATTERN 1: Hardcoded URLs (Simple)
===================================

from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

# Define sources once
SOURCES = {
    2010: [
        "https://scr-publisher.gov.in/scr_2010_vol_1.pdf",
        "https://scr-publisher.gov.in/scr_2010_vol_2.pdf",
        "https://scr-publisher.gov.in/scr_2010_vol_3.pdf",
    ],
    2011: [
        "https://scr-publisher.gov.in/scr_2011_vol_1.pdf",
        "https://scr-publisher.gov.in/scr_2011_vol_2.pdf",
    ],
}

# Register all sources
for year, urls in SOURCES.items():
    PDFSourceProvider.register_source(year, urls)

Then run:
  python -m src.acquisition.run_acquisition --year 2010
"""

"""
PATTERN 2: CSV Configuration File
==================================

Create data/scr_sources.csv:

year,url,status
2010,https://example.gov.in/scr_2010_vol_1.pdf,active
2010,https://example.gov.in/scr_2010_vol_2.pdf,active
2011,https://example.gov.in/scr_2011_vol_1.pdf,active

Then in your setup code:

import csv
from pathlib import Path
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

csv_path = Path("data/scr_sources.csv")

sources_by_year = {}

with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        year = int(row['year'])
        url = row['url']
        status = row['status']
        
        if status == 'active':
            if year not in sources_by_year:
                sources_by_year[year] = []
            sources_by_year[year].append(url)

for year, urls in sources_by_year.items():
    PDFSourceProvider.register_source(year, urls)
"""

"""
PATTERN 3: Web Scraping (Advanced)
===================================

For sources that don't provide direct PDF links:

from bs4 import BeautifulSoup
import requests
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

def discover_scr_volumes(year):
    '''Scrape official SCR website to find PDF links.'''
    
    url = f"https://main.sci.gov.in/scr/{year}"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all PDF links on the page
        pdf_links = soup.find_all('a', href=re.compile(r'\\.pdf$'))
        
        urls = []
        for link in pdf_links:
            href = link.get('href')
            # Make absolute URLs
            if href.startswith('http'):
                urls.append(href)
            else:
                urls.append(f"https://main.sci.gov.in{href}")
        
        return urls
    
    except Exception as e:
        print(f"Error discovering volumes for {year}: {e}")
        return []

# Use the scraper
for year in range(2010, 2024):
    urls = discover_scr_volumes(year)
    if urls:
        PDFSourceProvider.register_source(year, urls)
        print(f"Found {len(urls)} volumes for {year}")
"""

"""
PATTERN 4: API Integration
===========================

For official APIs that expose PDF metadata:

import requests
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

def discover_from_official_api(year):
    '''Discover PDFs from official API.'''
    
    api_url = "https://api.official.gov.in/scr/volumes"
    
    params = {
        "year": year,
        "format": "json",
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()
        
        urls = []
        for volume in data['volumes']:
            urls.append(volume['pdf_url'])
        
        return urls
    
    except Exception as e:
        print(f"Error querying API: {e}")
        return []

# Use the API
for year in range(2010, 2024):
    urls = discover_from_official_api(year)
    if urls:
        PDFSourceProvider.register_source(year, urls)
"""

"""
PATTERN 5: Browser Automation (Most Complex)
==============================================

For sources requiring JavaScript rendering:

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

def discover_with_browser(year):
    '''Use browser to navigate and discover PDFs.'''
    
    driver = webdriver.Chrome()
    
    try:
        # Navigate to site
        driver.get("https://main.sci.gov.in/supremecourt")
        
        # Select year
        year_select = Select(driver.find_element(By.ID, "year"))
        year_select.select_by_value(str(year))
        
        # Wait for page to load
        import time
        time.sleep(2)
        
        # Find PDF links
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf']")
        
        urls = [link.get_attribute('href') for link in links]
        
        return urls
    
    finally:
        driver.quit()

# Use the browser automation
for year in range(2010, 2020):  # Limit to avoid long waits
    urls = discover_with_browser(year)
    if urls:
        PDFSourceProvider.register_source(year, urls)
"""

# ==================== TESTING YOUR SOURCES ====================

"""
BEFORE PRODUCTION:

1. Test with --dry-run (no downloads):
   python -m src.acquisition.run_acquisition --year 2010 --dry-run

2. Verify sources are registered:
   python -m src.acquisition.run_acquisition --show-sources

3. Check logs for any issues:
   tail -f logs/pipeline.log

4. Test with a small year first:
   python -m src.acquisition.run_acquisition --year 2010

5. Verify PDFs are valid:
   ls -lh data/raw_pdfs/2010/
   file data/raw_pdfs/2010/*.pdf

6. Run extraction to confirm:
   python -m src.pipeline.run_scr_pipeline --year 2010
"""

# ==================== TROUBLESHOOTING ====================

"""
PROBLEM: No sources registered
SOLUTION:
- Make sure you registered sources BEFORE running acquisition
- Check: python -m src.acquisition.run_acquisition --show-sources
- Verify registration code is executed

PROBLEM: Downloads fail with HTTP 404
SOLUTION:
- Verify URLs are correct
- Check if site structure changed
- Try URLs manually in browser
- Update source discovery code

PROBLEM: Downloads timeout
SOLUTION:
- Increase timeout in settings.py:
  PDF_DOWNLOAD_TIMEOUT = 600  # 10 minutes
- Check your internet connection
- Try --dry-run first

PROBLEM: PDF validation fails
SOLUTION:
- Check logs/failures.log for specific error
- Verify file size is reasonable:
  du -h data/raw_pdfs/2010/*.pdf
- Check if files are actually PDFs:
  file data/raw_pdfs/2010/*.pdf

PROBLEM: Partial downloads left behind
SOLUTION:
- CLEANUP_FAILED_DOWNLOADS=True cleans them up automatically
- Or manually remove *.tmp files:
  rm data/raw_pdfs/2010/*.tmp

PROBLEM: Need to re-download specific files
SOLUTION:
- Delete the existing file
- Re-run with --force-redownload:
  python -m src.acquisition.run_acquisition --year 2010 --force-redownload
"""

# ==================== PRODUCTION SETUP ====================

"""
RECOMMENDED SETUP FOR PRODUCTION:

1. Create a dedicated module for your sources:
   
   src/acquisition/sources/sci_official.py:
   
   from src.acquisition.scr_pdf_fetcher import PDFSourceProvider
   
   def register_official_sources():
       '''Register sources from official SCI website.'''
       
       # Your source discovery logic here
       # Could be hardcoded, CSV-based, API-based, etc.
       
       pass
   
   if __name__ == "__main__":
       register_official_sources()

2. Set up a cron job or scheduled task:
   
   # Every month, download new PDFs
   0 0 1 * * cd /path/to/scr_pipeline && \\
       python -m src.acquisition.sources.sci_official && \\
       python -m src.acquisition.run_acquisition --year $(date +%Y)

3. Monitor logs:
   
   # Check for failures
   grep ERROR logs/failures.log
   
   # Check statistics
   tail logs/acquisition_log_*.json

4. Regular validation:
   
   # Verify all downloaded PDFs are valid
   for year in 2010 2011 2012; do
       echo "Validating year $year"
       python -m src.acquisition.run_acquisition --year $year --dry-run
   done
"""

# ==================== LEGAL REQUIREMENTS ====================

"""
IMPORTANT: Source Compliance

Before using any source, ensure:

1. LICENSING
   - You have the right to download PDFs
   - Check the source's terms of service
   - Some sources may require attribution

2. TERMS OF SERVICE
   - Don't violate website ToS
   - Respect rate limits and robots.txt
   - Don't overload the server

3. LEGAL JURISDICTION
   - This tool is for SCR (Supreme Court of India) PDFs
   - Only use for the jurisdiction for which SCR is published
   - Respect copyright notices

4. OFFICIAL SOURCES
   - Prefer official government sources
   - Avoid mirrors unless officially sanctioned
   - Verify source authenticity

RECOMMENDED OFFICIAL SOURCES:
- Supreme Court of India: https://main.sci.gov.in/
- Official SCR Publisher (if any)
- Government digital archives

DO NOT USE:
- Unauthorized mirrors
- Torrents or P2P networks
- Sources without legal clearance
"""

if __name__ == "__main__":
    print(__doc__)
