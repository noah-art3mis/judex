from judex.core import JudexScraper


def main():
    scraper = JudexScraper(classe="ADI", processos="[1]", persistence_types=["json"])
    scraper.scrape()


if __name__ == "__main__":
    main()
