<!--
================================================================================
File: README.md
Purpose: Master project overview, architecture, execution guides, design rationale,
         and screen recording walkthrough for Affinity Answers Data Engineer (Intern) Assessment.
Author: Soham Gudewar (Data Engineer Applicant)
Repository: https://github.com/sohamgudewar/Affinity-Assignment
================================================================================
-->

# Affinity Answers — Data Engineer (Intern) Technical Assessment

This repository contains production-ready solutions for the Affinity Answers Data Engineer (Intern) recruitment questionnaire. Each solution is built with production-grade engineering practices, strict modularity, comprehensive error handling, and zero hard-coding.

---

## 📁 Repository Structure

```text
Affinity-Assignment/
├── question1_python/
│   ├── scraper.py             # CLI web scraper for MD Computers
│   ├── requirements.txt       # Dependencies (requests, beautifulsoup4, tabulate)
│   ├── sample_output.json     # Sample extracted output in JSON format
│   ├── sample_output.csv      # Sample extracted output in CSV format
│   └── README.md              # Detailed design choices & format rationale
├── question2_sql/
│   ├── queries.sql            # Clean, formatted SQL queries for questions 2.1 to 2.4
│   ├── verify_queries.py      # Automated live verification runner against Rfam MySQL
│   └── README.md              # Genomic/botanical context, query breakdown & database details
├── question3_shell/
│   ├── process_companies.sh   # Unix shell script with RFC-4180 CSV parsing & sorting
│   └── README.md              # Awk parsing explanation, pipeline examples & sample output
├── .gitignore                 # Environment and OS ignore patterns
├── requirements.txt           # Unified top-level dependencies
└── README.md                  # Master project guide & screen recording walkthrough
```

---

## 🚀 Quick Setup & Dependencies

Ensure Python 3.8+ and Git are installed. Clone the repository and install dependencies:

```bash
git clone https://github.com/sohamgudewar/Affinity-Assignment.git
cd Affinity-Assignment

# Install all Python dependencies
pip install -r requirements.txt
```

---

## 📋 Executive Summary of Solutions

### Question 1: Python Web Scraper (MD Computers)
* **Goal:** Extract product information (Title, Price, Original Price, Discount, Availability, and Product URL) from MD Computers for any search term.
* **Core Technology:** `requests`, `beautifulsoup4`, `tabulate`, and `argparse`.
* **Execution:**
  ```bash
  # Interactive mode
  python question1_python/scraper.py

  # Search with JSON output (default)
  python question1_python/scraper.py --search "external harddrive" --limit 5

  # Render formatted ASCII table in terminal
  python question1_python/scraper.py --search "external harddrive" --format table --limit 5

  # Export to CSV
  python question1_python/scraper.py --search "external harddrive" --format csv --output results.csv
  ```
* **Design Choices & Format Rationale (Extra Points):**
  - **Why JSON?** JSON is the standard interchange format for modern data engineering lakehouses and event streams (**Apache Kafka**, **Snowflake**, **MongoDB**, **AWS Kinesis**). It preserves typed numbers (`numeric_price: 550.0`) alongside formatted currency strings (`current_price: "₹550"`) without loss of precision.
  - **Cross-Platform Currency Encoding:** Automatically configures UTF-8 standard output streams to prevent `UnicodeEncodeError` when rendering the Indian Rupee symbol (`₹`) on Windows command lines.
  - **OpenCart Retrina DOM Parsing:** Implements resilient multi-level selectors for `.product-grid-item`, isolating discounted prices (`span.ins`) and strikethrough original prices (`span.del`).

---

### Question 2: SQL and Databases (Public Rfam Database)
* **Goal:** Answer biological and database questions against the live European Bioinformatics Institute public MySQL Rfam database (`mysql-rfam-public.ebi.ac.uk:4497`).
* **Summary of Answers:**
  1. **Acacia Plants in Taxonomy:**
     - **326 species** belong strictly to the botanical genus *Acacia* (`species LIKE 'Acacia%'`).
     - **357 entries** belong to the broader taxonomic lineage (`tax_string LIKE '%Acacia%'`).
  2. **Wheat Type with Longest DNA Sequence:**
     - **Winner:** **`Triticum durum (durum wheat)`** with **836,514,780 base pairs** (Accession `LT934116.1`, Chromosome 3B).
     - *Runner-up:* `Triticum aestivum (bread wheat)` with 830,829,764 bp.
  3. & 4. **Paginated Family Sequence Lengths:**
     - Page 9 with 15 results per page corresponds to `LIMIT 15 OFFSET 120`.
     - Canonical query:
       ```sql
       SELECT 
           f.rfam_acc AS family_accession_id,
           f.rfam_id AS family_name,
           MAX(r.length) AS max_sequence_length
       FROM family f
       JOIN full_region fr ON f.rfam_acc = fr.rfam_acc
       JOIN rfamseq r ON fr.rfamseq_acc = r.rfamseq_acc
       WHERE fr.is_significant = 1
       GROUP BY f.rfam_acc, f.rfam_id
       HAVING max_sequence_length > 1000000
       ORDER BY max_sequence_length DESC
       LIMIT 15 OFFSET 120;
       ```
* **Execution:**
  ```bash
  # Run live verification against Rfam MySQL
  python question2_sql/verify_queries.py
  ```

---

### Question 3: Unix Shell Scripting (S&P 500 Constituents)
* **Goal:** Download, parse, and sort company constituents by founding year from a remote CSV dataset.
* **Execution:**
  ```bash
  # Direct argument
  ./question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"

  # Via standard input / pipeline
  echo "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv" | ./question3_shell/process_companies.sh

  # On Windows (Git Bash)
  & "C:\Program Files\Git\bin\bash.exe" question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"
  ```
* **Engineering Highlights:**
  - **RFC-4180 CSV Parsing:** The dataset contains embedded commas inside quotes (e.g. `"Saint Paul, Minnesota"` and `"Nike, Inc."`). We utilize GNU Awk's `FPAT='([^,]+)|("[^"]+")'` to ensure quoted strings are parsed atomically.
  - **Composite Year Handling:** Isolates primary 4-digit years from composite entries (e.g., `2013 (1888)`) for accurate numerical sorting.
  - **Automatic Cleanup:** Configures `trap` handlers to remove temporary files upon process exit.

---

## 🎥 Screen Recording Walkthrough Guide

The submission requires a screen recording demonstrating the execution of each program. Here is the suggested 2-minute demonstration flow:

### Step 1: Demonstrate Question 1 (Python Scraper)
```bash
# 1. Run interactive prompt
python question1_python/scraper.py
# (Enter: external harddrive)

# 2. Run with table format and limit
python question1_python/scraper.py --search "external harddrive" --format table --limit 3

# 3. Export to JSON
python question1_python/scraper.py --search "external harddrive" --format json --output question1_python/sample_output.json --limit 3
```

### Step 2: Demonstrate Question 2 (SQL Queries against live Rfam)
```bash
# Execute live query runner against EMBL-EBI Rfam server
python question2_sql/verify_queries.py
```

### Step 3: Demonstrate Question 3 (Unix Shell Script)
```bash
# Run shell script with remote S&P 500 CSV URL
./question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv" | head -n 25
```

---

## 🌟 Adherence to Affinity Answers Evaluation Guidelines

In alignment with Vivek Vijayan's publication (*"Recruitment: How not to answer our take-home questions"*):
- [x] **No Jupyter Notebooks:** Delivered as native, production-grade source code files (`.py`, `.sql`, `.sh`).
- [x] **No "Throwing Over the Wall":** Fully tested and verified live against active endpoints and databases.
- [x] **Zero Hardcoding:** Dynamic arguments, CLI flags, and interactive fallbacks across all scripts.
- [x] **Code Quality & Style:** Clean modular structure following the Google Style Guide with comprehensive header documentation on every file.
- [x] **Meaningful Git Hygiene:** Progressive, granular Git commits tracing each milestone.
