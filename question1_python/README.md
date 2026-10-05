<!--
================================================================================
File: question1_python/README.md
Purpose: Documentation, architecture overview, design rationale, and execution
         instructions for Question 1 (Python Product Scraper for MD Computers).
Author: Soham Gudewar (Data Engineer Applicant)
================================================================================
-->

# Question 1: Python Web Scraper (MD Computers)

A modular, production-ready Python command-line utility to search and extract structured product listings from **MD Computers** ([mdcomputers.in](https://mdcomputers.in)).

---

## 1. Quickstart & Usage

### Prerequisites & Installation
Ensure Python 3.8+ is installed. Install the required dependencies:

```bash
cd question1_python
pip install -r requirements.txt
```

### Running the Program

1. **Interactive Mode (Prompts for search term):**
   ```bash
   python scraper.py
   ```

2. **CLI Argument Mode:**
   ```bash
   python scraper.py --search "external harddrive"
   ```

3. **Limit Number of Results:**
   ```bash
   python scraper.py --search "external harddrive" --limit 5
   ```

4. **Change Output Format (`json`, `table`, `csv`):**
   ```bash
   # Formatted ASCII table in terminal
   python scraper.py --search "external harddrive" --format table --limit 5

   # CSV format
   python scraper.py --search "external harddrive" --format csv --limit 5
   ```

5. **Save Results to File:**
   ```bash
   python scraper.py --search "external harddrive" --format json --output sample_output.json
   python scraper.py --search "external harddrive" --format csv --output sample_output.csv
   ```

---

## 2. Design Choices & Output Format Rationale (Extra Points)

### A. Why JSON is the Primary Output Format
The program defaults to **JSON** format for key data engineering considerations:

1. **Schema & Type Preservation:**
   - E-commerce product attributes naturally vary. For instance, some items have discounted prices (`₹550`), original prices (`₹1,299`), and explicit discount badges (`-58%`), while others only have a regular price.
   - JSON natively models numeric fields (`numeric_price: 550.0`) alongside formatted strings (`current_price: "₹550"`), preserving precision for downstream financial and analytics processing without lossy string conversion.

2. **Pipeline & Cloud Interoperability:**
   - In modern data platforms, scraped e-commerce data serves as raw Bronze-layer data. JSON payloads integrate directly into streaming brokers (**Apache Kafka**, **AWS Kinesis**), document stores (**MongoDB**, **Elasticsearch**), and lakehouses (**Apache Spark**, **Snowflake**, **Delta Lake**).

3. **Human & Machine Flexibility:**
   - By adding `--format table` and `--format csv` flags, the utility remains accessible for human visual inspection during debugging or tabular export into spreadsheet tools like Microsoft Excel and Google Sheets.

---

### B. Core Architecture & Engineering Highlights

1. **OpenCart & Retrina Theme Selector Resilience:**
   - MD Computers runs on OpenCart with a custom Retrina theme (`.product-grid-item`).
   - The extraction layer isolates specific DOM elements (`span.ins` for discounted price, `span.del` for original strikethrough price, and `.product-entities-title` for product title).
   - Defensive fallbacks (`.product-layout`, `.product-thumb`) ensure resilience against frontend template variations.

2. **Cross-Platform Currency Encoding Protection:**
   - On Windows terminals, default shell encodings (e.g., `cp1252`) crash with `UnicodeEncodeError` when printing the Indian Rupee symbol (`₹`, `\u20b9`).
   - `scraper.py` configures `sys.stdout.reconfigure(encoding="utf-8")` to guarantee flawless execution across Linux, macOS, and Windows PowerShell/Command Prompt.

3. **Polite and Robust Networking:**
   - A realistic desktop browser `User-Agent` and standard HTTP headers prevent 403 request drops.
   - Configurable network timeouts (`--timeout`) and structured exception handling guard against network drops and slow responses.

4. **Zero Hardcoding & Adherence to Style Guides:**
   - All parameters (search keywords, limits, formats, output paths) are exposed via `argparse`.
   - Adheres to the **Google Python Style Guide**, featuring PEP 484 type annotations and modular single-responsibility functions.

---

## 3. Sample JSON Output

```json
{
  "search_query": "external harddrive",
  "total_extracted": 3,
  "source_url": "https://mdcomputers.in/?route=product%2Fsearch&search=external+harddrive",
  "products": [
    {
      "title": "EK-Loop Connect - External USB Cable (1M)",
      "current_price": "₹550",
      "numeric_price": 550.0,
      "original_price": "₹1,299",
      "discount": "-58%",
      "availability": "In Stock",
      "product_url": "https://mdcomputers.in/product/ek-loop-connect-external-usb-cable"
    },
    {
      "title": "Seagate Expansion 1TB External Hard Drive",
      "current_price": "₹9,699",
      "numeric_price": 9699.0,
      "original_price": "₹10,000",
      "discount": "-3%",
      "availability": "In Stock",
      "product_url": "https://mdcomputers.in/product/seagate-expansion-1tb-external-hard-drive-stkm1000400"
    }
  ]
}
```


# Output
<!-- PS C:\Users\soham\Desktop\Affinity Assignment> python question1_python/scraper.py --search "external harddrive" --format table --limit 3

[*] Querying MD Computers for: 'external harddrive'
[*] Request URL: https://mdcomputers.in/?route=product%2Fsearch&search=external+harddrive
[*] Successfully extracted 3 product(s).
╒═════╤═══════════════════════════════════════════╤═════════╤════════════════╤═══════════════════════════════════════════════════════════════════════════════════════╕
│   # │ Product Name                              │ Price   │ Availability   │ URL                                                                                   │
╞═════╪═══════════════════════════════════════════╪═════════╪════════════════╪═══════════════════════════════════════════════════════════════════════════════════════╡
│   1 │ EK-Loop Connect - External USB Cable (1M) │ ₹550    │ In Stock       │ https://mdcomputers.in/product/ek-loop-connect-external-usb-cable                     │
├─────┼───────────────────────────────────────────┼─────────┼────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
│   2 │ Seagate Expansion 1TB External Hard Drive │ ₹9,699  │ In Stock       │ https://mdcomputers.in/product/seagate-expansion-1tb-external-hard-drive-stkm1000400  │
├─────┼───────────────────────────────────────────┼─────────┼────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
│   3 │ WD Elements 1TB External Hard Drive       │ ₹9,760  │ In Stock       │ https://mdcomputers.in/product/wd-elements-1tb-external-hard-drive-wdbhhg0010bbk-eesn │
╘═════╧═══════════════════════════════════════════╧═════════╧════════════════╧═══════════════════════════════════════════════════════════════════════════════════════╛ -->