"""
================================================================================
File: question1_python/scraper.py
Purpose: CLI web scraping utility to search and extract structured product
         information from MD Computers (https://mdcomputers.in).
Author: Soham Gudewar (Data Engineer Applicant)

Description:
This script accepts a search query as input, queries the MD Computers e-commerce
search endpoint, parses the returned HTML using BeautifulSoup4, and outputs
structured product information (title, price, product URL, availability status).

Design Highlights:
1. Dynamic Input: Accepts search terms via CLI arguments (--search) or
   interactive prompt if omitted (zero hard-coding).
2. Defensive DOM Selectors: Designed for the OpenCart Retrina theme layout
   (.product-grid-item, .product-entities-title) with multi-level fallbacks.
3. Multiple Output Formats: Supports JSON (primary), CSV, and ASCII terminal
   tables for data engineering pipelines or human inspection.
4. Robust Encoding: Configures standard UTF-8 stream handling to safely display
   the Indian Rupee symbol (\u20b9) across all platforms including Windows terminals.
5. Error Resilience: Graceful error handling for HTTP timeouts, network drops,
   and zero-result queries.
================================================================================
"""

import argparse
import csv
import json
import re
import sys
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Ensure UTF-8 output encoding on Windows terminals to prevent charmap errors on ₹
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Target website constants
BASE_URL = "https://mdcomputers.in"
SEARCH_ENDPOINT = f"{BASE_URL}/index.php"

# Default request headers mimicking a modern desktop browser
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
    "Connection": "keep-alive",
}


def build_search_url(search_term: str) -> str:
    """Build the search URL for MD Computers OpenCart engine.

    Args:
        search_term: The keyword query entered by the user.

    Returns:
        The formatted search URL string.
    """
    params = {
        "route": "product/search",
        "search": search_term.strip(),
    }
    return f"{BASE_URL}/?{urllib.parse.urlencode(params)}"


def fetch_html(url: str, timeout: int = 15) -> str:
    """Fetch raw HTML content from the given URL.

    Args:
        url: Target search URL.
        timeout: Network timeout in seconds.

    Returns:
        The raw HTML string of the response page.

    Raises:
        requests.RequestException: If network connection fails or HTTP error occurs.
    """
    session = requests.Session()
    response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def clean_text(text: Optional[str]) -> str:
    """Normalize extracted text by stripping whitespace and collapse spaces.

    Args:
        text: Raw string extracted from BeautifulSoup.

    Returns:
        Clean, normalized string.
    """
    if not text:
        return ""
    # Collapse multiple spaces, newlines, and non-breaking spaces
    normalized = re.sub(r"\s+", " ", text)
    return normalized.strip()


def parse_price(price_str: str) -> Optional[float]:
    """Extract numeric price value from a price string (e.g., '₹3,450' -> 3450.0).

    Args:
        price_str: Raw price text with currency symbols.

    Returns:
        Float value of the price, or None if extraction fails.
    """
    cleaned = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def extract_products(html_content: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Parse product items from MD Computers search results page.

    Args:
        html_content: Raw HTML text of the search results page.
        limit: Optional maximum number of product records to extract.

    Returns:
        List of product dictionaries containing title, price, url, and availability.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    products: List[Dict[str, Any]] = []

    # Target the product cards using theme-specific and fallback classes
    product_cards = soup.select(".product-grid-item")
    if not product_cards:
        # Fallback selectors for alternate OpenCart themes/layouts
        product_cards = (
            soup.select(".product-layout")
            or soup.select(".product-thumb")
            or soup.select(".product-item")
        )

    for card in product_cards:
        # 1. Product Title and Link
        title_el = (
            card.select_one(".product-entities-title a")
            or card.select_one("h3.product-entities-title")
            or card.select_one(".title a")
            or card.select_one("h4 a")
        )

        title = clean_text(title_el.get_text()) if title_el else "Unknown Title"

        # Determine product URL
        product_url = ""
        if title_el and title_el.name == "a" and title_el.get("href"):
            product_url = title_el["href"]
        else:
            any_link = card.select_one("a[href]")
            if any_link and any_link.get("href"):
                product_url = any_link["href"]

        # Ensure absolute URL
        if product_url and not product_url.startswith("http"):
            product_url = urllib.parse.urljoin(BASE_URL, product_url)

        # 2. Product Price (handling del for original price and ins for discounted price)
        price_box = card.select_one(".price")
        raw_price = "Price unavailable"
        raw_old_price: Optional[str] = None

        if price_box:
            ins_el = price_box.select_one("span.ins .amount") or price_box.select_one(".price-new")
            del_el = price_box.select_one("span.del .amount") or price_box.select_one(".price-old")

            if ins_el:
                raw_price = clean_text(ins_el.get_text())
                if del_el:
                    raw_old_price = clean_text(del_el.get_text())
            elif del_el:
                raw_price = clean_text(del_el.get_text())
            else:
                # Regular non-discounted price
                amount_el = price_box.select_one(".amount")
                raw_price = clean_text(amount_el.get_text()) if amount_el else clean_text(price_box.get_text())

        # 3. Discount badge
        discount_el = card.select_one(".product-label") or card.select_one(".onsale")
        discount = clean_text(discount_el.get_text()) if discount_el else None

        # 4. Stock / Availability status
        cart_btn = card.select_one(".add-to-cart-loop") or card.select_one(".product-add-cart-icon")
        stock_label = card.select_one(".stock-status") or card.select_one(".out-of-stock")

        if stock_label and any(w in stock_label.get_text().lower() for w in ["out of stock", "notify"]):
            availability = "Out of Stock"
        elif cart_btn and "out-of-stock" not in " ".join(cart_btn.get("class", [])):
            availability = "In Stock"
        else:
            availability = clean_text(stock_label.get_text()) if stock_label else "In Stock"

        # Normalize product record
        product_record = {
            "title": title,
            "current_price": raw_price,
            "numeric_price": parse_price(raw_price),
            "original_price": raw_old_price,
            "discount": discount,
            "availability": availability,
            "product_url": product_url,
        }

        products.append(product_record)

        if limit and len(products) >= limit:
            break

    return products


def format_as_table(products: List[Dict[str, Any]]) -> str:
    """Format product records as an ASCII terminal table.

    Args:
        products: List of extracted product dictionaries.

    Returns:
        Formatted ASCII table string.
    """
    try:
        from tabulate import tabulate

        table_rows = []
        for idx, p in enumerate(products, start=1):
            # Truncate title for clean display if overly long
            title = (p["title"][:45] + "...") if len(p["title"]) > 48 else p["title"]
            table_rows.append([
                idx,
                title,
                p["current_price"],
                p["availability"],
                p["product_url"],
            ])
        headers = ["#", "Product Name", "Price", "Availability", "URL"]
        return tabulate(table_rows, headers=headers, tablefmt="fancy_grid")
    except ImportError:
        # Graceful fallback if tabulate is unavailable
        lines = []
        lines.append(f"{'#':<4} {'Product Name':<50} {'Price':<15} {'Availability':<15}")
        lines.append("-" * 84)
        for idx, p in enumerate(products, start=1):
            name = (p['title'][:47] + '..') if len(p['title']) > 49 else p['title']
            lines.append(f"{idx:<4} {name:<50} {p['current_price']:<15} {p['availability']:<15}")
        return "\n".join(lines)


def format_as_csv(products: List[Dict[str, Any]]) -> str:
    """Format product records as CSV string.

    Args:
        products: List of extracted product dictionaries.

    Returns:
        CSV formatted string.
    """
    import io

    output = io.StringIO()
    fieldnames = [
        "title",
        "current_price",
        "numeric_price",
        "original_price",
        "discount",
        "availability",
        "product_url",
    ]
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL
    )
    writer.writeheader()
    for p in products:
        writer.writerow(p)
    return output.getvalue()


def run_scraper(
    search_term: str,
    output_format: str = "json",
    output_file: Optional[str] = None,
    limit: Optional[int] = None,
    timeout: int = 15,
) -> List[Dict[str, Any]]:
    """Execute the scraping workflow and handle rendering.

    Args:
        search_term: Search query string.
        output_format: 'json', 'csv', or 'table'.
        output_file: Optional path to save output file.
        limit: Optional maximum number of items.
        timeout: Network timeout in seconds.

    Returns:
        List of extracted product records.
    """
    search_url = build_search_url(search_term)
    print(f"[*] Querying MD Computers for: '{search_term}'", file=sys.stderr)
    print(f"[*] Request URL: {search_url}", file=sys.stderr)

    try:
        html = fetch_html(search_url, timeout=timeout)
    except requests.RequestException as e:
        print(f"[!] Network error fetching results: {e}", file=sys.stderr)
        return []

    products = extract_products(html, limit=limit)
    print(f"[*] Successfully extracted {len(products)} product(s).", file=sys.stderr)

    # Format the extracted content
    rendered_output: str
    if output_format.lower() == "csv":
        rendered_output = format_as_csv(products)
    elif output_format.lower() == "table":
        rendered_output = format_as_table(products)
    else:
        # Default to JSON
        rendered_output = json.dumps(
            {
                "search_query": search_term,
                "total_extracted": len(products),
                "source_url": search_url,
                "products": products,
            },
            indent=2,
            ensure_ascii=False,
        )

    # Output to console
    print(rendered_output)

    # Optional file output
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered_output)
            print(f"[+] Output successfully saved to: {output_file}", file=sys.stderr)
        except OSError as e:
            print(f"[!] Failed to write output file: {e}", file=sys.stderr)

    return products


def main() -> None:
    """CLI entrypoint for MD Computers product scraper."""
    parser = argparse.ArgumentParser(
        description="Extract structured product listings from MD Computers search results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s", "--search",
        type=str,
        default=None,
        help="Search keyword or product name (e.g., 'external harddrive'). If omitted, you will be prompted.",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["json", "csv", "table"],
        default="json",
        help="Output format: 'json' (default), 'csv', or 'table'.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Optional destination file path to save output (e.g., results.json, results.csv).",
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=None,
        help="Optional maximum number of products to return.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP request timeout in seconds.",
    )

    args = parser.parse_args()

    # If search term was not provided as a CLI argument, ask interactively
    search_term = args.search
    if not search_term:
        try:
            search_term = input("Enter search term (e.g., 'external harddrive'): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(0)

    if not search_term:
        print("[!] Error: Search term cannot be empty.", file=sys.stderr)
        sys.exit(1)

    run_scraper(
        search_term=search_term,
        output_format=args.format,
        output_file=args.output,
        limit=args.limit,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
