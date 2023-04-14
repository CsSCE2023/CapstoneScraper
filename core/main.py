"""
Created on Tue Mar 20 16:23:53 2018
"""

import configparser
import os
import re
import time
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver


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
        time.sleep(5)
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        return soup

    # Define the function for scraping with selenium
    def etl(self) -> pd.DataFrame:
        try:
            page = self.scrape()

        except Exception as e:
            print(e)

        p1 = page.find_all("div", class_="mod-article-tile")

        a = []
        b = []
        c = []

        for i in p1:
            title = i.find("span", class_="mod-article-tile__title")
            price = i.find("span", class_="price__wrapper")
            link = i.find("a")

            a.append(link["href"])
            b.append(title.text.strip())
            match: Optional[re.Match[str]] = re.search("[0-9.]+", price.text)
            if match is not None:
                c.append(match.group())

        df = pd.DataFrame()
        df["article_link"] = a
        df["title"] = b
        df["price"] = c
        return df

    # Define the function to export scraped data to csv
    def export_csv(self, df: pd.DataFrame) -> None:
        df.to_csv(self.aldi_data_path, index=False, encoding="utf_8_sig")

    # Define the function to run the entire process
    def run(self) -> None:
        df = self.etl()
        self.export_csv(df)


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()
