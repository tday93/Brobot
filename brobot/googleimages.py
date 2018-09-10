import bs4
import requests
import sys


def get_page(search_string):

    """headers = requests.utils.default_headers()
    headers.update(  {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
       """ 
    url = "https://www.google.com/search?q={}&tbm=isch".format(search_string)
    page = requests.get(url)
    page.raise_for_status()
    return page


def scrape_images(page,search_string):
    soup = bs4.BeautifulSoup(page.text, "html.parser")
    elems = soup.find_all("img", alt='Image result for {}'.format(search_string))
    image_urls = [element.get("src") for element in elems]
    return image_urls

def get_images(search_string):
    page = get_page(search_string)
    images = scrape_images(page, search_string)
    return images


if __name__ =="__main__":
    print(get_images(sys.argv[0]))
