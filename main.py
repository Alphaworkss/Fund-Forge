from scraper import MufapScraper
import scraper

print("Scraper file being used:")
print(scraper.__file__)

def main():

    scraper_obj = MufapScraper()

    print(type(scraper_obj))
    print(hasattr(scraper_obj, "run"))

    scraper_obj.run()


if __name__ == "__main__":
    main()