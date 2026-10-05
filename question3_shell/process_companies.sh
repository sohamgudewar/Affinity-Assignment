#!/usr/bin/env bash
# ==============================================================================
# File: question3_shell/process_companies.sh
# Purpose: Unix shell script to download, parse, and sort company constituents
#          from an S&P 500 CSV dataset by founding year.
# Author: Soham Gudewar (Data Engineer Applicant)
#
# Usage:
#   1. CLI Argument:
#      ./process_companies.sh <URL_OR_FILEPATH>
#   2. Stdin / Pipeline:
#      echo "<URL>" | ./process_companies.sh
#   3. Interactive Prompt:
#      ./process_companies.sh (prompts user for URL)
#
# Requirements Handled:
#   - Accepts CSV URL as input.
#   - Downloads or reads the CSV data.
#   - Outputs: Company Name, Location, Founding Year.
#   - Handles embedded commas inside quoted fields (e.g. "Saint Paul, Minnesota").
#   - Sorts records chronologically by founding year.
# ==============================================================================

set -euo pipefail

# Display usage banner and help
usage() {
    cat << EOF
Usage: $0 [CSV_URL_OR_FILE]

Downloads or reads an S&P 500 company CSV file, extracts company name,
location, and founding year, and outputs the records sorted by founding year.

Examples:
  $0 "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"
  echo "https://raw.githubusercontent.com/.../constituents.csv" | $0
EOF
    exit 1
}

# ------------------------------------------------------------------------------
# 1. Input Acquisition (CLI arg, pipe, or prompt)
# ------------------------------------------------------------------------------
INPUT_SOURCE=""

if [ $# -ge 1 ]; then
    INPUT_SOURCE="$1"
elif [ ! -t 0 ]; then
    # Read from standard input / pipe
    read -r INPUT_SOURCE || true
fi

# If input source is still empty, prompt interactively
if [ -z "${INPUT_SOURCE}" ]; then
    read -rp "Enter CSV URL or local file path: " INPUT_SOURCE
fi

if [ -z "${INPUT_SOURCE}" ]; then
    echo "[!] Error: No input URL or file path provided." >&2
    usage
fi

# ------------------------------------------------------------------------------
# 2. Temporary Workspace Setup with Automatic Cleanup
# ------------------------------------------------------------------------------
TMP_CSV=$(mktemp 2>/dev/null || mktemp -t 'companies_csv')
TMP_PARSED=$(mktemp 2>/dev/null || mktemp -t 'companies_parsed')
trap 'rm -f "${TMP_CSV}" "${TMP_PARSED}"' EXIT

# ------------------------------------------------------------------------------
# 3. Data Ingestion (Download or local read)
# ------------------------------------------------------------------------------
if [[ "${INPUT_SOURCE}" =~ ^https?:// ]]; then
    echo "[*] Downloading CSV data from: ${INPUT_SOURCE}" >&2
    if command -v curl >/dev/null 2>&1; then
        curl -sSL --fail "${INPUT_SOURCE}" -o "${TMP_CSV}"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "${TMP_CSV}" "${INPUT_SOURCE}"
    else
        echo "[!] Error: Neither curl nor wget is available to fetch remote URL." >&2
        exit 1
    fi
elif [ -f "${INPUT_SOURCE}" ]; then
    echo "[*] Reading local file: ${INPUT_SOURCE}" >&2
    cp "${INPUT_SOURCE}" "${TMP_CSV}"
else
    echo "[!] Error: Input '${INPUT_SOURCE}' is neither a valid URL nor an existing file." >&2
    exit 1
fi

# Verify downloaded content is non-empty
if [ ! -s "${TMP_CSV}" ]; then
    echo "[!] Error: Downloaded or read CSV file is empty." >&2
    exit 1
fi

# ------------------------------------------------------------------------------
# 4. RFC 4180 CSV Parsing & Field Extraction
# Target Fields:
#   - Column 2: Company Name (Security)
#   - Column 5: Headquarters Location (May contain commas inside quotes)
#   - Column 8: Founding Year (e.g., '1902' or '2013 (1888)')
# ------------------------------------------------------------------------------
# We use AWK with FPAT for robust RFC-4180 CSV handling
awk -v FPAT='([^,]+)|("[^"]+")' '
BEGIN {
    OFS = "\t"
}
NR > 1 {
    # Skip lines with insufficient fields
    if (NF < 8) next;

    company = $2
    location = $5
    founded = $8

    # Strip surrounding quotes and carriage returns
    gsub(/^"|"$/, "", company)
    gsub(/^"|"$/, "", location)
    gsub(/^"|"$/, "", founded)
    gsub(/\r/, "", company)
    gsub(/\r/, "", location)
    gsub(/\r/, "", founded)

    # Extract primary 4-digit founding year for sorting (handling e.g. "2013 (1888)")
    sort_year = 9999
    match(founded, /[0-9]{4}/)
    if (RSTART > 0) {
        sort_year = substr(founded, RSTART, 4)
    }

    # Emit tab-separated fields: sort_year \t company \t location \t founded_display
    print sort_year, company, location, founded
}
' "${TMP_CSV}" > "${TMP_PARSED}"

# ------------------------------------------------------------------------------
# 5. Sorting and Formatted Output Display
# ------------------------------------------------------------------------------
# Print Table Header
printf "%-40s | %-32s | %-15s\n" "COMPANY NAME" "HEADQUARTERS LOCATION" "FOUNDED"
printf "%s\n" "-----------------------------------------+----------------------------------+----------------"

# Sort numerically by sort_year (field 1), then format cleanly
sort -t$'\t' -k1,1n -k2,2 "${TMP_PARSED}" | awk -F'\t' '{
    printf "%-40s | %-32s | %-15s\n", substr($2, 1, 40), substr($3, 1, 32), $4
}'

TOTAL_COMPANIES=$(wc -l < "${TMP_PARSED}" | tr -d ' ')
echo >&2
echo "[+] Successfully processed and sorted ${TOTAL_COMPANIES} companies by founding year." >&2
