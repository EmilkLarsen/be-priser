"""Brico.be (EUR, Belgium) — sitemap index has /{fr,nl}/category/sitemap.xml
per language. Product URLs discovered from category pages; ld+json price."""
import re
from common import get, sane_price, valid_ean, first_str, ldjson_products, offer_from_ld, write_jsonl, scrape_urls

BASE = "https://www.brico.be"
OUT = "data/latest/brico_be.jsonl"


def fetch_url_list(limit=None):
    idx = get(f"{BASE}/sitemap.xml")
    files = re.findall(r"<loc>([^<]+)</loc>", idx)
    urls = []
    for f in files:
        try:
            xml = get(f if f.startswith("http") else BASE + f)
        except Exception:
            continue
        # product URLs end in a slug pattern with digits
        us = re.findall(r'<loc>(https://www\.brico\.be/(?:fr|nl)/[^<]+/\d+[^<]*)</loc>', xml)
        urls.extend(us)
        if limit and len(urls) >= limit:
            break
    return urls[:limit] if limit else urls


def handle(u, html):
    rows = []
    for p in ldjson_products(html):
        off = offer_from_ld(p)
        if off:
            off["price"] = sane_price(off["price"])
        if not off or not off["price"]:
            continue
        rows.append({
            "chain": "brico_be",
            "country": "be",
            "currency": off["currency"],
            "sku": u.rstrip("/").rsplit("/", 1)[-1],
            "ean": valid_ean(p.get("gtin13") or p.get("gtin") or p.get("ean")),
            "name": p.get("name"),
            "url": u,
            "price": off["price"],
            "in_stock": off["in_stock"],
            "image": first_str(p.get("image")),
        })
        break
    return rows


def scrape(limit=None):
    return scrape_urls(fetch_url_list(limit), handle)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("brico_be: %d products -> %s" % (len(rows), OUT))
