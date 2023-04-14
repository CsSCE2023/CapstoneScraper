"""
Created on Tue Mar 20 16:23:53 2018
"""
import re
import time
from re import Match
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium import webdriver


# scraping CME is soooo effortless
# just simple html parse tree
# how i love Chicago
def scrape() -> bs:
    driver = webdriver.Firefox()
    driver.get("https://www.aldi-nord.de/angebote.html#2023-04-11-10-obst-gemuese")
    time.sleep(5)
    htmlSource = driver.page_source
    soup = bs(htmlSource, "html.parser")

    return soup


def etl() -> pd.DataFrame:
    try:
        page = scrape()
        print(page)

    except Exception as e:
        print(e)

    # i need date, prior settle price and volume
    # it is essential to view source of the website first
    # then use beautiful soup to search specific class
    p1 = page.find_all("div", class_="mod-article-tile")
    # p2 = page.find_all('td', class_=['statusOK', 'statusNull', 'statusAlert'])
    # p3 = page.find_all('td', class_="cmeTableRight")

    a = []
    b = []
    c = []

    for i in p1:
        # innerDiv = i.find("div",class_="mod-article-tile__content")
        title = i.find("span", class_="mod-article-tile__title")
        price = i.find("span", class_="price__wrapper")
        link = i.find("a")

        a.append(link["href"])
        b.append(title.text.strip())
        match: Optional[Match[str]] = re.search("[0-9.]+", price.text)
        if match is not None:
            c.append(match.group())

    df = pd.DataFrame()
    df["article_link"] = a
    df["title"] = b
    df["price"] = c
    return df


def main() -> None:
    # scraping and etl
    df1 = etl()
    # df2 = etl('precious', 'gold')
    # df3 = etl('precious', 'palladium')
    # df4 = etl('base', 'copper')

    # concatenate then export
    # dd = pd.concat([df1, df2, df3, df4])
    dd = pd.concat([df1])
    dd.to_csv("/data/aldi.csv", encoding="utf_8_sig")


if __name__ == "__main__":
    main()
