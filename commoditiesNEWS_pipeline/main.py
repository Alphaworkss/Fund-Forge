from utils.config import load_sources
from scripts.rss_scraper import run_rss_scraper
from scripts.webpage_scraper import run_webpage_scraper
from utils.logger import logger

def main():

    print("=" * 50)
    print("Commodity News Pipeline Started")
    print("=" * 50)
    logger.info("Commodity News Pipeline Started")
    sources = load_sources()

    for source in sources:

        if source["Source Type"].upper() == "RSS":

            run_rss_scraper(source)

        elif source["Source Type"].upper() == "WEB":
            run_webpage_scraper(source)
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()