"""
Scraper for https://books.toscrape.com/

What it does:
  1. Downloads each catalogue page (page-1.html, page-2.html, ... until there's no "next" button)
  2. Finds every book on the page
  3. Pulls out title, price, star rating, availability and link
  4. Saves everything to books.csv  -> one row per book (1,000 books in total)

Run it with:   python scraper.py
Needs:         pip install requests beautifulsoup4
"""

import csv
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/catalogue/"
START_PAGE = "page-1.html"
OUTPUT_FILE = "books.csv"
MAX_ATTEMPTS = 3      # how many times to try downloading a page before giving up
RETRY_PAUSE = 2       # seconds to wait between attempts

# The site writes the rating as a word inside a CSS class, e.g. class="star-rating Three".
# This dictionary turns that word into a number we can sort and calculate with.
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_page(url):
    """Download one page and return it as a BeautifulSoup object we can search in.
    If the download fails (no internet, timeout, server error), try again up to MAX_ATTEMPTS times."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()      # treat a bad status (e.g. 404, 500) as an error too
            break                            # it worked -> leave the retry loop
        except requests.RequestException as error:
            if attempt == MAX_ATTEMPTS:      # out of attempts -> give up and show the error
                raise
            print(f"  Attempt {attempt} failed ({error}). Trying again in {RETRY_PAUSE} s...")
            time.sleep(RETRY_PAUSE)          # short pause before the next try

    response.encoding = "utf-8"              # makes the £ sign come out correctly
    return BeautifulSoup(response.text, "html.parser")


def parse_book(article, page_url):
    """Take the HTML block for ONE book and return its data as a dictionary (= one table row)."""
    link_tag = article.h3.a
    title = link_tag["title"]                                   # full title (the visible text is often cut off with "...")
    url = urljoin(page_url, link_tag["href"])                   # turn the relative link into a full web address

    price_text = article.find("p", class_="price_color").text  # e.g. "£51.77"
    price = float(price_text.replace("£", "").replace("Â", "").strip())

    rating_classes = article.find("p", class_="star-rating")["class"]  # e.g. ["star-rating", "Three"]
    rating = RATING_WORDS.get(rating_classes[1], None)

    availability = article.find("p", class_="availability").text.strip()  # e.g. "In stock"

    # The cover is an <img> whose src is relative, e.g. "../media/cache/2c/da/....jpg".
    # urljoin turns it into a full address: https://books.toscrape.com/media/cache/2c/da/....jpg
    image_url = urljoin(page_url, article.find("img")["src"])

    return {
        "title": title,
        "price_gbp": price,
        "rating": rating,
        "availability": availability,
        "url": url,
        "image_url": image_url,
    }


def scrape_all_books(max_books=None):
    """Loop through every catalogue page and collect all books in one list.
    max_books: stop after this many books (handy for testing). None = scrape everything."""
    books = []
    next_page = START_PAGE

    while next_page:                                    # keep going as long as there is a next page
        page_url = urljoin(BASE_URL, next_page)
        print(f"Scraping {page_url}")
        soup = get_page(page_url)

        # Every book on the page sits inside <article class="product_pod">
        for article in soup.find_all("article", class_="product_pod"):
            books.append(parse_book(article, page_url))
            if max_books and len(books) >= max_books:   # test mode: stop as soon as we have enough
                return books

        # Look for the "next" button. On the last page it doesn't exist -> find() returns None -> loop stops.
        next_button = soup.find("li", class_="next")
        next_page = next_button.a["href"] if next_button else None

        time.sleep(0.5)                                 # be polite: small pause so we don't hammer the server

    return books


def save_to_csv(books, filename):
    """Write the list of dictionaries to a CSV file: a header row, then one row per book."""
    columns = ["title", "price_gbp", "rating", "availability", "url", "image_url"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(books)


if __name__ == "__main__":
    import sys

    # "python scraper.py 5"  -> test run, only 5 books, printed and saved to books_test.csv
    # "python scraper.py"    -> full run, all 1,000 books saved to books.csv
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        books = scrape_all_books(max_books=limit)
        for book in books:
            print(book)
        save_to_csv(books, "books_test.csv")
        print(f"Test done! Saved {len(books)} books to books_test.csv")
    else:
        all_books = scrape_all_books()
        save_to_csv(all_books, OUTPUT_FILE)
        print(f"Done! Saved {len(all_books)} books to {OUTPUT_FILE}")
