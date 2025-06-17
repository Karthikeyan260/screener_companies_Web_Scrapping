import csv
import json
import asyncio
from playwright.async_api import async_playwright, TimeoutError

EXPECTED_RATIOS = [
    "Market Cap", "Current Price", "High / Low", "Stock P/E", "Book Value",
    "Dividend Yield", "ROCE", "ROE", "Face Value"
]

async def scrape_ratios(playwright, company_name, url):
    try:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_selector('div.company-ratios ul#top-ratios', timeout=5000)

        items = await page.query_selector_all('div.company-ratios ul#top-ratios > li')
        ratio_data = {}
        for item in items:
            name_el = await item.query_selector("span.name")
            value_el = await item.query_selector("span.value")
            if name_el and value_el:
                name = (await name_el.inner_text()).strip()
                value = (await value_el.inner_text()).strip().replace('\n', ' ')
                ratio_data[name] = value

        await context.close()
        await browser.close()

        return {
            "company_name": company_name,
            "company_url": url,
            "ratios": {key: ratio_data.get(key, "N/A") for key in EXPECTED_RATIOS}
        }

    except TimeoutError:
        print(f"⚠️ Timeout for {company_name}")
        return {
            "company_name": company_name,
            "company_url": url,
            "ratios": {key: "Timeout" for key in EXPECTED_RATIOS}
        }
    except Exception as e:
        print(f"❌ Error for {company_name}: {e}")
        return {
            "company_name": company_name,
            "company_url": url,
            "ratios": {key: "Error" for key in EXPECTED_RATIOS}
        }

async def main():
    input_file = r"#path-of-that\screener_companies.csv"
    output_json = "Company_Ratios.json"

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        companies = [(row["Company Name"].strip(), row["url"].strip()) for row in reader]

    results = []

    async with async_playwright() as playwright:
        # Limit concurrency (e.g., 5 parallel at once to avoid blocking)
        sem = asyncio.Semaphore(5)

        async def sem_scrape(company_name, url):
            async with sem:
                return await scrape_ratios(playwright, company_name, url)

        tasks = [sem_scrape(name, url) for name, url in companies]
        for i, coro in enumerate(asyncio.as_completed(tasks), start=1):
            result = await coro
            results.append(result)
            print(f"[{i}/{len(companies)}] ✅ {result['company_name']}")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"\n✅ Data saved to '{output_json}'")

if __name__ == "__main__":
    asyncio.run(main())

