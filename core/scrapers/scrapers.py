import configparser
import os
from abc import ABC, abstractmethod

import pandas as pd
from bs4 import BeautifulSoup


class AbstractScraper(ABC):
    def __init__(self):
        self.config = self.read_config()

    @staticmethod
    def get_path(relative_path: str) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        final_path = os.path.join(grandparent_dir, relative_path)
        return final_path

    @staticmethod
    def read_config() -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config_path = AbstractScraper.get_path("../../config.ini")
        config.read(config_path)
        return config

    @abstractmethod
    def scrape(self) -> BeautifulSoup:
        pass

    @abstractmethod
    def etl(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def export_csv(self, df: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass
