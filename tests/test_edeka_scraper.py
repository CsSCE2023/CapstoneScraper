import json
import sys
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from core.scrapers.edeka_scraper import EdekaScraper

sys.path.append("/Users/divinefavourodion/Documents/CapstoneScraper/core")


class TestEdekaScraper(unittest.TestCase):
    def test_get_path(self):
        scraper = EdekaScraper()
        relative_path = "../config.ini"
        abs_path = scraper.get_path(relative_path)
        self.assertTrue(abs_path.endswith("config.ini"))

    def test_read_config(self):
        scraper = EdekaScraper()
        config = scraper.read_config()
        self.assertIsNotNone(config["paths"]["edeka_data"])

    @patch("core.scrapers.edeka_scraper.requests.get")
    def test_scrape(self, mock_get):
        scraper = EdekaScraper()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"offers": []}
        mock_get.return_value = mock_response

        data = scraper.scrape()
        self.assertIsNotNone(data)

    def test_etl(self):
        scraper = EdekaScraper()
        with open("sample_page.json") as file:
            json_content = file.read()
            data = json.loads(json_content)

        with patch.object(scraper, "scrape", return_value=data):
            df = scraper.etl()
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 3)  # Assuming 16 items in the sample json

    @patch("core.scrapers.edeka_scraper.pd.DataFrame.to_csv")
    def test_export_csv(self, mock_to_csv):
        scraper = EdekaScraper()
        df = pd.DataFrame()
        scraper.export_csv(df)
        mock_to_csv.assert_called_once()

    @patch("core.scrapers.edeka_scraper.EdekaScraper.etl")
    @patch("core.scrapers.edeka_scraper.EdekaScraper.export_csv")
    def test_run(self, mock_export_csv, mock_etl):
        scraper = EdekaScraper()
        mock_df = pd.DataFrame()
        mock_etl.return_value = mock_df

        scraper.run()
        mock_etl.assert_called_once()
        mock_export_csv.assert_called_once_with(mock_df)


if __name__ == "__main__":
    unittest.main()
