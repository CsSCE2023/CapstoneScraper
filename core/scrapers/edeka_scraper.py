import configparser
import os
import re
import sys
from datetime import datetime

import pandas as pd
import requests

from core.scrapers.scrapers import AbstractScraper


# Main scraper class
class EdekaScraper(AbstractScraper):
    def __init__(self):
        super().__init__()
        self.edeka_data_path = self.get_path(self.config["paths"]["edeka_data"])

    # Define the function to construct absolute path from relative paths
    @staticmethod
    def get_path(relative_path: str) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        final_path = os.path.join(grandparent_dir, relative_path)
        return final_path

    # Define the function to read the configuration settings from config.ini
    @staticmethod
    def read_config() -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config_path = EdekaScraper.get_path("./config.ini")
        config.read(config_path)
        return config

    # Define the function for parsing html with Beautiful soup
    def scrape(self):
        url = "https://www.edeka.de/api/offers"

        params = {"limit": 999, "marketId": 2658965}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code}")
            return None

    # Define the function for scraping with selenium
    def etl(self) -> pd.DataFrame:
        try:
            page = self.scrape()

        except Exception as e:
            print(e)
            sys.exit()

        offers = page["offers"]
        titles = []
        prices = []
        links = []
        img_urls = []
        descriptions = []
        scraped_dates = []
        valid_from_list = []
        valid_until_list = []
        ids = []
        additional_text_list = []
        weights_list = []
        store_location = []

        # Store the current date
        scraped_date = datetime.now().strftime("%Y-%m-%d")

        for i in range(len(offers)):
            ids.append(offers[i]["id"])
            valid_from_list.append(page["validFrom"])
            valid_until_list.append(page["validTill"])
            scraped_dates.append(scraped_date)
            descriptions.append(offers[i]["descriptions"][0])
            img_urls.append(offers[i]["images"]["original"])
            links.append("https://www.edeka.de/")
            prices.append(offers[i]["price"]["value"])
            titles.append(offers[i]["title"])
            additional_text_list.append(offers[i]["additionalTextApp"])
            weights_list.append(offers[i]["baseUnit"])
            location_pattern = r"EDEKA-Markt[^.]*\d{5}\s*[^.]*\."
            match = re.search(location_pattern, offers[i]["additionalTextApp"])
            store_location.append(
                match.group() if match else "Store location not found"
            )

        df = pd.DataFrame()
        df["title"] = titles
        df["price"] = prices
        df["weight (kg)"] = weights_list
        df["description"] = descriptions
        df["article_link"] = links
        df["img_link"] = img_urls
        df["extra_details"] = additional_text_list
        df["date_published"] = valid_until_list
        df["date_expires"] = valid_from_list
        df["scraped_date"] = scraped_dates
        df["store_location"] = store_location

        return df

    # Define the function to export scraped data to csv
    def export_csv(self, df: pd.DataFrame) -> None:
        print("Data from Edeka scraped successfully")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "id"}, inplace=True)

        if os.path.exists(self.edeka_data_path):
            # Read the existing CSV file into a DataFrame
            existing_df = pd.read_csv(self.edeka_data_path, encoding="utf_8_sig")

            # Concatenate the new data with the existing data
            combined_df = pd.concat([existing_df, df], ignore_index=True)

            # Remove duplicate rows based on a subset of columns
            combined_df = combined_df.drop_duplicates(subset=["title", "img_link"])

            # Write the combined DataFrame to the CSV file
            combined_df.to_csv(self.edeka_data_path, index=False, encoding="utf_8_sig")
        else:
            # Create a new CSV file with the header and data
            df.to_csv(self.edeka_data_path, index=False, encoding="utf_8_sig")

    # Define the function to run the entire process
    def run(self) -> None:
        df = self.etl()
        self.export_csv(df)


if __name__ == "__main__":
    scraper = EdekaScraper()
    scraper.run()
