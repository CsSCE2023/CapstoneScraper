import configparser
import os
import re
import string
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.scrapers.scrapers import AbstractScraper


# Main scraper class
class ReweScraper(AbstractScraper):
    def __init__(self):
        super().__init__()
        self.edeka_data_path = self.get_path(self.config["paths"]["rewe_data"])

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
        config_path = ReweScraper.get_path("./config.ini")
        config.read(config_path)
        return config

    # Define the function for parsing html with Beautiful soup
    def scrape(self):
        url1 = "https://www.rewe.de/api/marketsearch?searchTerm=Bremen"
        url2 = "https://www.rewe.de/"

        response = requests.get(url1)

        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error: {response.status_code}")
            sys.exit()

        market_location = {
            "Company_name": [],
            "Street_address": [],
            "Contact_city": [],
            "Zipcode": [],
            "wwIdent": [],
        }

        for i in range(len(data)):
            market_location["Company_name"].append(data[i]["companyName"])
            market_location["Street_address"].append(data[i]["contactStreet"])
            market_location["Contact_city"].append(data[i]["contactCity"])
            market_location["Zipcode"].append(data[i]["contactZipCode"])
            market_location["wwIdent"].append(data[i]["wwIdent"])

        soup_bowl = {
            key: [] for key in market_location["Street_address"]
        }  # Dictionary to store prettyfied web pages from BeautifulSoup

        url_bowl = {
            key: [] for key in market_location["Street_address"]
        }  # Dictionary to store the url of the prettified webpages

        # Get the data for each Rewe store in Bremen

        for i in range(len(market_location["Company_name"])):
            url = (
                "https://www.rewe.de/angebote/"
                + "-".join(
                    re.split(r"[/\s]", market_location["Contact_city"][i])
                ).lower()
                + f"/{market_location['wwIdent'][i]}/rewe-markt-{'-'.join(''.join(c for c in market_location['Street_address'][i] if c not in string.punctuation).lower().split(' '))}/"
            )
            driver = webdriver.Chrome()
            driver.get(url)

            # Scroll down the page to trigger JavaScript
            body = driver.find_element(By.TAG_NAME, "body")
            last_height = driver.execute_script("return window.pageYOffset;")
            while True:
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.1)
                new_height = driver.execute_script("return window.pageYOffset;")
                if new_height == last_height:
                    break
                last_height = new_height

            html_source = driver.page_source
            soup = BeautifulSoup(html_source, "html.parser")
            soup_bowl[market_location["Street_address"][i]].append(soup)
            url_bowl[market_location["Street_address"][i]].append(url)

        return soup_bowl, url_bowl

    # Define the function for scraping with selenium
    def etl(self) -> pd.DataFrame:
        try:
            page, urls = self.scrape()

        except Exception as e:
            print(e)
            sys.exit()

        master_df = pd.DataFrame(
            columns=[
                "title",
                "price",
                "weight (kg)",
                "description",
                "article_link",
                "img_link",
                "extra_details",
                "date_published",
                "date_expires",
                "scraped_date",
            ]
        )

        for soup in page:
            time.sleep(5)
            name = page[soup][0].find_all("h3", class_="cor-offer-information__title")
            price = page[soup][0].find_all("div", class_="cor-offer-price__tag-price")
            picture_links = page[soup][0].find_all(
                "img", class_="cor-offer-image--animated cor-offer-image--loaded"
            )
            date = page[soup][0].find_all("h2", class_="sos-headings__duration")
            item_links = page[soup][0].find_all(
                "a", class_="cor-offer-information__title-link"
            )
            # Find all the 'cor-offer-information__additional' class elements
            additional_info = page[soup][0].find_all(
                class_="cor-offer-information__additional"
            )
            additional_info_text = " ".join(
                [info.get_text(strip=True) for info in additional_info]
            )

            base_url = urls[soup][
                0
            ]  # Get the base url for the corresponding market webpage.
            titles = []
            prices = []
            links = []
            descriptions = []
            img_urls = []
            weights_list = []
            scraped_dates = []
            valid_until_list = []
            date_published_list = []
            additional_text_list = []

            # Store the current date
            scraped_date = datetime.now().strftime("%Y-%m-%d")

            for i in range(len(name)):
                titles.append(
                    name[i]
                    .find("a", class_="cor-offer-information__title-link")
                    .get("data-offer-title")
                )
                prices.append(price[i].text.replace("€", "").strip())
                links.append(
                    urljoin(base_url, f"#{item_links[i].get('data-offer-nan')}")
                )
                img_urls.append(picture_links[i].get("data-src"))
                date_published_list.append("placeholder")
                scraped_dates.append(scraped_date)
                valid_until_list.append(date[0].text.split(",")[1].strip())
                weights_list.append("placeholder")
                additional_text_list.append("placeholder")
                descriptions.append("placeholder")

            df = pd.DataFrame()
            df["title"] = titles
            df["price"] = prices
            df["weight (kg)"] = weights_list
            df["description"] = descriptions
            df["article_link"] = links
            df["img_link"] = img_urls
            df["extra_details"] = additional_text_list
            df["date_published"] = date_published_list
            df["date_expires"] = valid_until_list
            df["scraped_date"] = scraped_dates

            master_df = pd.concat([master_df, df], ignore_index=True)

        master_df["date_expires"] = pd.to_datetime(
            master_df["date_expires"], format="%d.%m.%Y"
        )
        master_df["scraped_date"] = pd.to_datetime(master_df["scraped_date"])

        return master_df

    # Define the function to export scraped data to csv
    def export_csv(self, df: pd.DataFrame) -> None:
        print("Data from Rewe scraped successfully")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "id"}, inplace=True)

        if os.path.exists(self.edeka_data_path):
            # Read the existing CSV file into a DataFrame
            existing_df = pd.read_csv(self.edeka_data_path, encoding="utf_8_sig")

            # Concatenate the new data with the existing data
            combined_df = pd.concat([existing_df, df], ignore_index=True)

            # Remove duplicate rows based on a subset of columns
            combined_df = combined_df.drop_duplicates(
                subset=["title", "img_link", "article_link"]
            )

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
    scraper = ReweScraper()
    scraper.run()
