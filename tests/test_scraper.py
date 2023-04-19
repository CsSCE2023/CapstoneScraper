import sys
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from bs4 import BeautifulSoup

from core.main import Scraper

# Add the main module to path

sys.path.append("/Users/divinefavourodion/Documents/CapstoneScraper/core")


class TestScraper(unittest.TestCase):
    def test_get_path(self):
        scraper = Scraper()
        relative_path = "../config.ini"
        abs_path = scraper.get_path(relative_path)
        self.assertTrue(abs_path.endswith("config.ini"))

    def test_read_config(self):
        scraper = Scraper()
        config = scraper.read_config()
        self.assertIsNotNone(config["paths"]["aldi_data"])

    @patch("core.main.webdriver.Chrome")
    def test_scrape(self, mock_chrome):
        scraper = Scraper()
        mock_driver = Mock()
        mock_driver.page_source = "<html></html>"
        mock_chrome.return_value = mock_driver

        soup = scraper.scrape()
        self.assertIsNotNone(soup)

    @patch("core.main.Scraper.scrape")
    def test_etl(self, mock_scrape):
        scraper = Scraper()
        with open("sample_page.html") as file:
            html_content = file.read()
            soup = BeautifulSoup(html_content, "html.parser")
            mock_scrape.return_value = soup

        df = scraper.etl()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 16)  # 16 items on the sample page

    @patch("core.main.pd.DataFrame.to_csv")
    def test_export_csv(self, mock_to_csv):
        scraper = Scraper()
        df = pd.DataFrame()
        scraper.export_csv(df)
        mock_to_csv.assert_called_once()


if __name__ == "__main__":
    unittest.main()
