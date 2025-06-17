from playwright.sync_api import sync_playwright
import csv
import time
import random
import os
from datetime import datetime

def load_existing_data(filename="screener_companies.csv"):
    """Load existing CSV data to resume scraping"""
    results = []
    last_count = 0
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 3:
                        results.append(row)
                        last_count = int(row[0])
            
            print(f"📂 Loaded {len(results)} existing companies from {filename}")
            print(f"🔢 Last company number: {last_count}")
            return results, last_count
        except Exception as e:
            print(f"⚠️ Error loading existing data: {e}")
            return [], 0
    else:
        print(f"📄 No existing file found, starting fresh")
        return [], 0

def calculate_start_page(last_count, limit=25):
    """Calculate which page to start from based on last scraped count"""
    if last_count == 0:
        return 1
    # Add 1 because we want to start from the next page
    start_page = (last_count // limit) + 1
    print(f"🎯 Calculated start page: {start_page} (based on {last_count} companies with limit {limit})")
    return start_page

def scrape_screener_resume(filename="screener_companies.csv", limit=25, delay_range=(5, 15), 
                          max_retries=3, backoff_delay=60, max_pages_per_session=10):
    """Resume scraping from where we left off"""
    
    # Load existing data
    existing_results, last_count = load_existing_data(filename)
    
    # Calculate starting page
    start_page = calculate_start_page(last_count, limit)
    
    base_url = "https://www.screener.in/screens/357649/all-listed-companies/"
    results = existing_results.copy()  # Copy existing results
    count = last_count + 1  # Continue counting from where we left off
    page_num = start_page
    pages_scraped_this_session = 0
    
    print(f"🚀 Resuming scraping from page {start_page}, company #{count}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Set up page with better settings to mimic real user
        page = browser.new_page()
        page.set_default_timeout(45000)  # Increased timeout
        
        # Set realistic user agent and headers
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Visit homepage first to establish session
        try:
            print("🏠 Visiting homepage to establish session...")
            page.goto("https://www.screener.in/", timeout=30000)
            time.sleep(random.uniform(3, 6))
        except:
            print("⚠️ Could not visit homepage, continuing anyway...")
        
        while pages_scraped_this_session < max_pages_per_session:
            url = f"{base_url}?page={page_num}&limit={limit}"
            print(f"\nScraping page {page_num}: {url}")
            
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    # Navigate to page
                    response = page.goto(url, timeout=60000, wait_until='networkidle')
                    
                    if response.status == 429:
                        print(f"🚫 Rate limited (HTTP 429) on page {page_num}")
                        backoff_time = backoff_delay * (2 ** retry_count)  # Exponential backoff
                        print(f"⏳ Backing off for {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        retry_count += 1
                        continue
                    elif response.status != 200:
                        print(f"⚠️ HTTP {response.status} on page {page_num}")
                        retry_count += 1
                        time.sleep(10)
                        continue
                    
                    # Wait for the table to load
                    try:
                        page.wait_for_selector('table.data-table', timeout=20000)
                        print(f"✅ Table loaded on page {page_num}")
                    except:
                        print(f"⚠️ Table not found on page {page_num}")
                    
                    # Wait for company links
                    try:
                        page.wait_for_selector('a[href^="/company/"]', timeout=15000)
                    except:
                        print(f"⚠️ No company links found on page {page_num}")
                        if page.locator("text=No companies found").count() > 0:
                            print("✅ Reached end of results")
                            success = True
                            break
                        retry_count += 1
                        continue
                    
                    # Find all company rows
                    rows = page.locator("tr[data-row-company-id]")
                    row_count = rows.count()
                    
                    if row_count == 0:
                        print(f"✅ No more companies found on page {page_num}")
                        success = True
                        break
                    
                    print(f"📊 Found {row_count} companies on page {page_num}")
                    
                    # Extract company data
                    new_companies_this_page = 0
                    for i in range(row_count):
                        try:
                            row = rows.nth(i)
                            link_tag = row.locator("td.text a").first
                            
                            link_tag.wait_for(state='visible', timeout=5000)
                            
                            company_name = link_tag.text_content().strip()
                            href = link_tag.get_attribute("href")
                            
                            if company_name and href:
                                company_url = f"https://www.screener.in{href}"
                                results.append([count, company_name, company_url])
                                print(f"  {count}. {company_name}")
                                count += 1
                                new_companies_this_page += 1
                            
                        except Exception as e:
                            print(f"⚠️ Error extracting company {i+1} on page {page_num}: {e}")
                            continue
                    
                    if new_companies_this_page > 0:
                        # Save progress after each successful page
                        save_progress(results, filename)
                        print(f"💾 Progress saved: {len(results)} companies total")
                    
                    success = True
                    pages_scraped_this_session += 1
                    
                except Exception as e:
                    retry_count += 1
                    print(f"⚠️ Error on page {page_num} (attempt {retry_count}): {e}")
                    
                    if retry_count < max_retries:
                        wait_time = 10 * (2 ** retry_count)  # Exponential backoff
                        print(f"🔄 Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ Failed to scrape page {page_num} after {max_retries} attempts")
            
            if not success:
                print(f"❌ Stopping scraper due to repeated failures on page {page_num}")
                break
            
            # Check if we should continue
            if row_count == 0:
                print("✅ Reached end of all results")
                break
                
            page_num += 1
            
            # Longer delay between pages
            delay = random.uniform(delay_range[0], delay_range[1])
            print(f"⏳ Waiting {delay:.1f} seconds before next page...")
            time.sleep(delay)
        
        if pages_scraped_this_session >= max_pages_per_session:
            print(f"📋 Session limit reached ({max_pages_per_session} pages). Run again to continue.")
        
        browser.close()
    
    # Final save
    save_progress(results, filename)
    print(f"\n✅ Session complete! Total companies: {len(results)}")
    print(f"📊 Next run will start from page {page_num}")
    
    return results

def save_progress(results, filename):
    """Save current progress to CSV"""
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Number", "Company Name", "Company URL"])
        writer.writerows(results)

def get_completion_status(filename="screener_companies.csv"):
    """Check how many companies we have and estimate completion"""
    if not os.path.exists(filename):
        print("No data file found")
        return
    
    results, last_count = load_existing_data(filename)
    
    print(f"\n📊 COMPLETION STATUS:")
    print(f"Total companies scraped: {len(results)}")
    print(f"Last company number: {last_count}")
    
    if len(results) > 0:
        last_company = results[-1]
        print(f"Last company: {last_company[1]}")
        
        # Estimate pages scraped (assuming 25 per page)
        pages_scraped = len(results) // 25
        print(f"Estimated pages completed: {pages_scraped}")

if __name__ == "__main__":
    print("🔍 Checking current status...")
    get_completion_status()
    
    print("\n" + "="*50)
    print("🚀 Starting resume scraper...")
    print("Will scrape 10 pages per session to avoid rate limiting")
    print("="*50)
    
    # Conservative settings for resuming
    companies = scrape_screener_resume(
        filename="screener_companies.csv",
        limit=25,
        delay_range=(10, 20),    # Longer delays
        max_retries=2,           # Fewer retries
        backoff_delay=90,        # Longer backoff
        max_pages_per_session=5  # Even fewer pages per session
    )