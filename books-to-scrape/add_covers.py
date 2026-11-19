"""
Adds the real book-cover images to catalogue.html.

Why this is needed: the cover images live at addresses like
  https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg
and that random-looking part can't be guessed from the title. It can only be read from the
website itself, so this script visits all 50 catalogue pages, collects each book's cover
address, and writes them into catalogue.html.

Run it once, in the folder with catalogue.html and scraper.py:
    python3 add_covers.py
Takes about 30 seconds. Afterwards just open catalogue.html - no internet scraping needed again.
"""

import json
import re

from scraper import scrape_all_books   # re-uses the scraper (the version that collects image_url)

PAGE = "catalogue.html"

books = scrape_all_books()

# Build a dictionary: book slug -> image path
#   url       https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html  -> slug "a-light-in-the-attic_1000"
#   image_url https://books.toscrape.com/media/cache/2c/da/2cda...jpg                    -> path "2c/da/2cda...jpg"
covers = {}
for book in books:
    slug = book["url"].split("/catalogue/")[1].replace("/index.html", "")
    covers[slug] = book["image_url"].split("/media/cache/")[1]

# Put the dictionary into the page, between the /*COVERS*/ and /*END_COVERS*/ markers
html = open(PAGE, encoding="utf-8").read()
new_html, replaced = re.subn(
    r"/\*COVERS\*/.*?/\*END_COVERS\*/",
    lambda _: "/*COVERS*/" + json.dumps(covers) + "/*END_COVERS*/",
    html,
    flags=re.S,
)
if not replaced:
    raise SystemExit(f"Couldn't find the COVERS markers in {PAGE}.")

open(PAGE, "w", encoding="utf-8").write(new_html)
print(f"Added {len(covers)} covers to {PAGE}. Open it in your browser!")
