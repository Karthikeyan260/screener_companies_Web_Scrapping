# 📊 Screener.in Company Scraper

This project is a professional web scraping toolchain for collecting **company listings** and **financial ratios** from [Screener.in](https://www.screener.in), using both **Playwright Sync** and **Playwright Async** APIs.

---

## 🔧 Features

- ✅ Resume-friendly scraper with session progress saving (`resume_scraper.py`)
- ⚙️ Async scraping of key company ratios with rate-limiting protection
- 💾 Stores data in CSV and JSON
- 🧠 Intelligent retry/backoff and anti-bot behavior (timeouts, headers, delays)
- 📁 Clean modular design for reuse or extension (e.g., scraping more info)

---

## 📂 Project Structure
```
screener-scraper/
│
├── scraper/
│ ├── resume_scraper.py # Synchronous company URL scraper
│ ├── async_ratios_scraper.py # Async top-ratios scraper
│ └── screener_companies.csv # Scraped company list (output)
│
├── data/
│ └── Company_Ratios.json # Scraped financial ratios (output)
├── requirements.txt # Python package dependencies
├── README.md
└── .gitignore
```

---

## 🧪 Requirements

- Python 3.8+
- Dependencies from `requirements.txt`

Install them with:

```bash
pip install -r requirements.txt

```


### 🚀 Usage
1. Scrape Company Listings (Sync - Resumable)
```
cd scraper
python resume_scraper.py
```

####  ✅ Output: scraper/screener_companies.csv

### 2. Scrape Company Ratios (Async)
Edit input_file path in async_ratios_scraper.py if needed.
```
cd scraper
python async_ratios_scraper.py
```
#### ✅ Output: data/Company_Ratios.json

### ⚠️ Notes
-Designed to respect Screener.in limits: randomized delays, max retries, session headers, and concurrency limits.

-To avoid getting blocked, do not increase the concurrency or reduce delay ranges aggressively.

### 📈 Future Enhancements
-Add MongoDB/SQLite persistence

-Add CLI arguments for automation

-Add support for scraping balance sheet, P&L, cash flow, etc.

-Add retry queue for failed items`
