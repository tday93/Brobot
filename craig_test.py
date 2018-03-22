import requests
from re import sub
from decimal import Decimal
from bs4 import BeautifulSoup
from random import choice as rchoice


def find_from_craigslist(budget):
    r = requests.get("https://losangeles.craigslist.org/d/for-sale/search/sss")
    print(r.status_code)
    soup = BeautifulSoup(r.content, "html5lib")
    all_items = soup.findAll("li", "result-row")
    items_formatted = []
    for item in all_items:
        price = None
        prices = item.findAll("span", "result-price")
        if prices:
            price = str(prices[0].contents)
            value = Decimal(sub(r'[^\d.]', '', price)) * 100
            if value < budget:
                f_item = {
                    "name": item.p.a.contents,
                    "price": value,
                    "link": item.a["href"]
                }
                items_formatted.append(f_item)
    return rchoice(items_formatted)


print(find_from_craigslist(4050))
