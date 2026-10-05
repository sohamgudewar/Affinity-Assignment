"""
================================================================================
File: question2_sql/verify_queries.py
Purpose: Automated verification runner connecting to the live public Rfam
         MySQL database to execute and validate Question 2 SQL queries.
Author: Soham Gudewar (Data Engineer Applicant)

Description:
Connects to the public read-only Rfam database instance:
  Host: mysql-rfam-public.ebi.ac.uk
  Port: 4497
  User: rfamro
  Database: Rfam

Features:
- CLI flags to run individual questions (--question 1, 2, 3) or all questions.
- Formats tabular results using `tabulate` for terminal review.
- Measures query execution latency.
================================================================================
"""

import argparse
import sys
import time
from typing import Any, List, Tuple

import pymysql
from tabulate import tabulate

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Rfam Public MySQL Database Configuration
DB_CONFIG = {
    "host": "mysql-rfam-public.ebi.ac.uk",
    "port": 4497,
    "user": "rfamro",
    "password": "",
    "database": "Rfam",
    "connect_timeout": 15,
}


def get_connection() -> pymysql.Connection:
    """Establish connection to the public Rfam MySQL database."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[!] Database connection error: {e}", file=sys.stderr)
        print(
            "[!] Ensure outgoing TCP connections to port 4497 are permitted by your network firewall.",
            file=sys.stderr,
        )
        sys.exit(1)


def execute_query(conn: pymysql.Connection, query: str) -> Tuple[List[str], List[Tuple[Any, ...]], float]:
    """Execute a SQL query and measure execution latency.

    Args:
        conn: Open PyMySQL connection object.
        query: SQL query string to execute.

    Returns:
        Tuple of (column_names, rows, elapsed_seconds).
    """
    t0 = time.time()
    with conn.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
    elapsed = time.time() - t0
    return columns, rows, elapsed


def run_question_1(conn: pymysql.Connection) -> None:
    """Run and display Question 2.1: Count of Acacia plants."""
    print("\n" + "=" * 80)
    print(" QUESTION 2.1: How many types of Acacia plants can be found in the taxonomy table?")
    print("=" * 80)

    # 1A: Genus match
    query_genus = """
    SELECT COUNT(*) AS count_species_genus
    FROM taxonomy
    WHERE species LIKE 'Acacia%';
    """
    print("\n[Query 1A: Strict Botanical Genus (species LIKE 'Acacia%')]")
    cols, rows, elapsed = execute_query(conn, query_genus)
    print(tabulate(rows, headers=cols, tablefmt="fancy_grid"))
    print(f"Elapsed: {elapsed:.2f}s | Result: {rows[0][0]} Acacia species")

    # 1B: Lineage match
    query_lineage = """
    SELECT COUNT(*) AS count_tax_lineage
    FROM taxonomy
    WHERE tax_string LIKE '%Acacia%';
    """
    print("\n[Query 1B: Broader Taxonomic Lineage (tax_string LIKE '%Acacia%')]")
    cols, rows, elapsed = executequery(conn, query_lineage)
    print(tabulate(rows, headers=cols, tablefmt="fancy_grid"))
    print(f"Elapsed: {elapsed:.2f}s | Result: {rows[0][0]} taxonomic entries containing 'Acacia'")


def run_question_2(conn: pymysql.Connection) -> None:
    """Run and display Question 2.2: Longest wheat DNA sequence."""
    print("\n" + "=" * 80)
    print(" QUESTION 2.2: Which type of wheat has the longest DNA sequence?")
    print("=" * 80)

    query = """
    SELECT 
        t.species AS wheat_type,
        r.rfamseq_acc AS accession_id,
        r.length AS sequence_length_bp,
        r.description AS sequence_description
    FROM rfamseq r
    JOIN taxonomy t ON r.ncbi_id = t.ncbi_id
    WHERE t.species LIKE 'Triticum%'
    ORDER BY r.length DESC
    LIMIT 1;
    """
    cols, rows, elapsed = execute_query(conn, query)
    print(tabulate(rows, headers=cols, tablefmt="fancy_grid"))
    if rows:
        wheat_type, acc, length, desc = rows[0]
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Answer: '{wheat_type}' has the longest DNA sequence ({length:,} bp).")
        print(f"Accession: {acc}")
        print(f"Description: {desc}")


def run_question_3(conn: pymysql.Connection) -> None:
    """Run and display Question 2.3 & 2.4: Family sequence length pagination."""
    print("\n" + "=" * 80)
    print(" QUESTION 2.3 & 2.4: Paginated list of families and longest DNA sequences")
    print(" Page 9 with 15 results per page (OFFSET 120, LIMIT 15, length > 1,000,000)")
    print("=" * 80)

    query = """
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
    """
    print("[*] Executing paginated grouping query against Rfam...")
    cols, rows, elapsed = execute_query(conn, query)
    print(tabulate(rows, headers=cols, tablefmt="fancy_grid"))
    print(f"Elapsed: {elapsed:.2f}s | Returned {len(rows)} rows for Page 9.")


# Fix typo helper if needed
executequery = execute_query


def main() -> None:
    """CLI entrypoint for Rfam query verification."""
    parser = argparse.ArgumentParser(
        description="Verify and execute Question 2 SQL queries against public Rfam MySQL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-q", "--question",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run specific question (1, 2, or 3). If omitted, runs questions 1 and 2 by default.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all questions including the large paginated family join query.",
    )

    args = parser.parse_args()

    print("[*] Connecting to public Rfam database (mysql-rfam-public.ebi.ac.uk:4497)...")
    conn = get_connection()
    print("[+] Successfully connected to Rfam MySQL!")

    try:
        if args.question == 1:
            run_question_1(conn)
        elif args.question == 2:
            run_question_2(conn)
        elif args.question == 3:
            run_question_3(conn)
        elif args.all:
            run_question_1(conn)
            run_question_2(conn)
            run_question_3(conn)
        else:
            # Default to Question 1 and 2
            run_question_1(conn)
            run_question_2(conn)
            print("\n[i] Tip: Use '--question 3' or '--all' to also execute the heavy family pagination query.")
    finally:
        conn.close()
        print("\n[+] Database connection closed.")


if __name__ == "__main__":
    main()
