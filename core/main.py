"""
Modified on Tue Apr 18 22:20:53 2023
"""

import configparser
import json
import os
import re
import sys
import time
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# Main scraper class
class Scraper:
    def __init__(self):
        self.config = self.read_config()
        self.aldi_data_path = self.get_path(self.config["paths"]["aldi_data"])

    # Define the function to construct absolute path from relative paths
    @staticmethod
    def get_path(relative_path: str) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        final_path = os.path.join(script_dir, relative_path)
        return final_path

    # Define the function to read the configuration settings from config.ini
    @staticmethod
    def read_config() -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config_path = Scraper.get_path("../config.ini")
        config.read(config_path)
        return config

    # Define the function for parsing html with Beautiful soup
    def scrape(self) -> BeautifulSoup:
        driver = webdriver.Chrome()
        driver.get("https://www.aldi-nord.de/angebote.html#2023-04-11-10-obst-gemuese")

        # Click intercepting element
        try:
            skip_sign_in = driver.find_element(
                By.CLASS_NAME, "ffbULy"
            )  # Skip sign-in pop up
            skip_sign_in.click()
        except NoSuchElementException:
            print("Pop-up skipped")

        time.sleep(5)

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
        return soup

    # Define the function for scraping with selenium
    def etl(self) -> pd.DataFrame:
        try:
            page = self.scrape()

        except Exception as e:
            print(e)
            sys.exit()

        time.sleep(5)
        p1 = page.find_all("div", class_="mod-article-tile")

        base_url = "https://www.aldi-nord.de"
        titles = []
        prices = []
        links = []
        img_urls = []
        descriptions = []

        for i in p1:
            title = i.find("span", class_="mod-article-tile__title")
            price = i.find("span", class_="price__wrapper")
            link = i.find("a")

            img = i.find("img", class_="img-responsive")
            description_json = i.find("script", type="application/ld+json")

            titles.append(title.text.strip())
            match: Optional[re.Match[str]] = re.search("[0-9.]+", price.text)
            if match is not None:
                prices.append(match.group())
            links.append(urljoin(base_url, link["href"]))
            img_urls.append(
                urljoin(base_url, img["src"]) if img and img.has_attr("src") else None
            )
            if description_json:
                try:
                    description_data = json.loads(description_json.string)
                    descriptions.append(description_data.get("description", ""))
                except json.JSONDecodeError:
                    descriptions.append("")

        df = pd.DataFrame()
        df["title"] = titles
        df["price"] = prices
        df["article_link"] = links
        df["img_url"] = img_urls
        df["description"] = descriptions
        return df

    # Define the function to export scraped data to csv
    def export_csv(self, df: pd.DataFrame) -> None:
        print("Data from Aldi scraped successfully")
        df.to_csv(self.aldi_data_path, index=False, encoding="utf_8_sig")

    # Define the function to run the entire process
    def run(self) -> None:
        df = self.etl()
        self.export_csv(df)


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()
