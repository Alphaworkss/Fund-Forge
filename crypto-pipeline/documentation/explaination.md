# Crypto News & Exchange Pipeline - Project Explanation

This document provides a comprehensive overview of the `crypto-news-pipeline` project. The project is a unified repository containing both a modern frontend interface structure and a robust, fully automated Python backend data pipeline designed to aggregate, process, and enrich cryptocurrency news and exchange announcements.

## 1. High-Level Architecture

The project is structured into two main components:

1. **Frontend (Next.js Application):** Located in the root directory. It serves as a modern web application scaffolding built with Next.js, React, and Tailwind CSS.
2. **Backend Data Pipeline (Python):** Located in the nested `crypto-news-pipeline/` folder. It is a zero-credential, local Python application that runs on a schedule to scrape, clean, process, and store crypto-related news and exchange announcements.

---

## 2. The Python Data Pipeline (Backend)

The core functionality of the project resides in the Python data pipeline. Its primary responsibility is to act as a data ingestion and enrichment engine that feeds a central prediction engine.

### **Pipeline Workflow**
The pipeline executes a systematic series of steps orchestrated by `pipeline.py`:

1. **Collection (`collectors/`)**:
   - **News Collector:** Gathers data from news sources (CoinDesk, Cointelegraph, Decrypt, Bitcoin Magazine, The Block) primarily using RSS feeds. If a feed only contains summaries, it falls back to extracting full-article text using `newspaper3k` or `trafilatura`. If the RSS feed fails entirely, it can scrape article links directly from the homepage.
   - **Exchange Collector:** Scrapes official announcement pages and blogs from major exchanges (Binance, Coinbase, Kraken, OKX, Bybit). It is configured using CSS selectors to locate relevant announcements.
   
2. **Cleaning (`processing/cleaning.py`)**:
   - Strips HTML boilerplate and irrelevant tags from the collected content.
   - Standardizes timestamps and deduplicates incoming records before further processing.

3. **Normalization (`processing/normalization.py`)**:
   - Maps the heterogeneous scraped data into a single, unified schema.
   - Ensures all fields (like `title`, `url`, `published_at`, `content`) are present and properly formatted.

4. **Feature Extraction (`processing/feature_extraction.py`)**:
   - **`affected_coins`:** Scans the text for specific cryptocurrency names and tickers (e.g., "BTC", "Ethereum") and outputs a comma-separated list of affected assets.
   - **`event_category`:** Uses keyword matching to classify the article into predefined categories (e.g., *Exchange Listing*, *Delisting*, *Exchange Hack*, *Regulatory Announcement*, *ETF News*).
   - **`sentiment_score`:** Uses the **VADER** sentiment analysis tool to calculate a compound sentiment score ranging from -1.0 (highly negative) to 1.0 (highly positive).
   - **`importance_score`:** Computes a composite score (0.0 to 1.0) based on predefined rules. For example, high-impact events like hacks or regulatory news get a +0.3 bonus, official exchange announcements get +0.1, and high absolute sentiment adds +0.1.

5. **Storage & Export (`storage/`)**:
   - **SQLite Database:** Stores the processed and enriched records in a local SQLite database (`data/pipeline.db`). Each record has a deterministic SHA-256 hash ID (based on URL and title) to prevent duplicates.
   - **CSV Export:** After every pipeline run, it automatically exports a full snapshot of the database to a CSV file (`data/pipeline_output.csv`), making it easily ingestible by downstream prediction models.

### **Automation & Historical Data**
- **Scheduler (`scheduler/run_scheduler.py`):** Uses `APScheduler` to run the pipeline automatically every 30 minutes, ensuring continuous, up-to-date data ingestion without manual intervention.
- **Backfilling (`backfill.py`):** A standalone script capable of retrieving up to 24 months of historical news via site XML sitemaps and paginated exchange announcement pages. It includes rate-limiting, progress checkpointing (so it can be resumed), and exponential backoff to handle network issues gracefully.

---

## 3. The Frontend App

The frontend is housed in the root directory and is set up as a modern React web application. 

### **Tech Stack**
- **Framework:** Next.js 16 (App Router)
- **UI Library:** React 19
- **Styling:** Tailwind CSS v4, integrated with PostCSS.
- **Component Library Setup:** Configured to use `shadcn/ui` (via `components.json` and `components/` directory) and `@base-ui/react` for accessible, customizable components.
- **Icons & Animations:** Uses `lucide-react` for iconography and `tw-animate-css` for animations.

### **Current State**
Currently, the frontend acts as a cleanly configured boilerplate. The main entry point (`app/page.tsx`) displays a placeholder component (indicating it may be designed to host a generated user interface, such as from v0). It features a dark/light mode adaptable layout utilizing CSS `colorScheme`. The frontend is primed to consume the CSV or SQLite outputs generated by the Python backend to display real-time analytics, news feeds, and sentiment trends in the future.

---

## 4. Summary

The `crypto-news-pipeline` is a self-contained, highly robust system. Its backend meticulously gathers and enriches unstructured crypto news and exchange data into a structured, highly valuable dataset without requiring any paid APIs. Meanwhile, the root directory prepares a state-of-the-art Next.js environment ready to serve as a dashboard or application to interact with the pipeline's analytical output.
