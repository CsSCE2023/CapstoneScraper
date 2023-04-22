import unittest
from unittest.mock import patch

import pandas as pd
from bs4 import BeautifulSoup

from core.scrapers.rewe_scraper import ReweScraper


class TestReweScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ReweScraper()

    def test_get_path(self):
        relative_path = "./config.ini"
        result = self.scraper.get_path(relative_path)
        self.assertIsInstance(result, str)
        self.assertTrue(result.endswith(relative_path))

    def test_read_config(self):
        config = self.scraper.read_config()
        self.assertIsNotNone(config)
        self.assertIn("paths", config.sections())

    @patch("core.scrapers.rewe_scraper.requests.get")
    def test_scrape(self, mock_get):
        # Mock the response from requests.get
        mock_response = MockResponse()
        mock_get.return_value = mock_response

        soup_bowl, url_bowl = self.scraper.scrape()
        self.assertIsNotNone(soup_bowl)
        self.assertIsNotNone(url_bowl)
        self.assertIsInstance(soup_bowl, dict)
        self.assertIsInstance(url_bowl, dict)

    def test_etl(self):
        with patch.object(self.scraper, "scrape") as mock_scrape:
            # Mock the return value of the scrape method with appropriate values
            mock_soup = BeautifulSoup("<html></html>", "html.parser")
            mock_scrape.return_value = (
                {"some_address": [mock_soup]},
                {"some_address": ["https://www.example.com"]},
            )
            df = self.scraper.etl()
            self.assertIsInstance(df, pd.DataFrame)

    def test_export_csv(self):
        with patch("core.scrapers.rewe_scraper.pd.read_csv") as mock_read_csv, patch(
            "core.scrapers.rewe_scraper.pd.DataFrame.to_csv"
        ) as mock_to_csv:
            # Mock the return value of pd.read_csv
            mock_read_csv.return_value = pd.DataFrame()
            test_df = pd.DataFrame(
                {
                    "title": ["title1", "title2"],
                    "img_url": ["url1", "url2"],
                    "article_link": ["link1", "link2"],
                    "A": [1, 2],
                    "B": [3, 4],
                }
            )
            self.scraper.export_csv(test_df)
            mock_to_csv.assert_called_once()

    def test_run(self):
        with patch.object(self.scraper, "etl") as mock_etl, patch.object(
            self.scraper, "export_csv"
        ) as mock_export_csv:
            # Mock the return value of the etl method
            mock_etl.return_value = pd.DataFrame()
            self.scraper.run()
            mock_etl.assert_called_once()
            mock_export_csv.assert_called_once()


class MockResponse:
    @property
    def status_code(self):
        return 200

    def json(self):
        # Add mock data here
        return [
            {
                "companyName": "Company",
                "contactStreet": "Street",
                "contactCity": "City",
                "contactZipCode": "12345",
                "wwIdent": "1234",
            }
        ]


if __name__ == "__main__":
    unittest.main()
