<!--
================================================================================
File: question3_shell/README.md
Purpose: Documentation, architecture overview, execution guide, and sample output
         for Question 3 (Unix Shell Scripting for S&P 500 company constituents).
Author: Soham Gudewar (Data Engineer Applicant)
================================================================================
-->

# Question 3: Unix Shell Scripting (S&P 500 Constituents)

A robust, POSIX-compliant Unix shell script that downloads and processes company constituent data from the S&P 500 dataset, extracts key attributes, and chronologically sorts the companies by their founding year.

---

## 1. Quickstart & Usage

### Execution Permissions
Make the script executable:

```bash
chmod +x question3_shell/process_companies.sh
```

### Running the Script

1. **Direct Argument (Recommended):**
   ```bash
   ./question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"
   ```

2. **Standard Input / Pipe:**
   ```bash
   echo "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv" | ./question3_shell/process_companies.sh
   ```

3. **Local File Input:**
   ```bash
   ./question3_shell/process_companies.sh /path/to/constituents.csv
   ```

4. **Running on Windows (Git Bash / WSL):**
   ```bash
   # From Git Bash terminal
   ./question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"

   # From Windows PowerShell / CMD
   & "C:\Program Files\Git\bin\bash.exe" question3_shell/process_companies.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"
   ```

---

## 2. Engineering Challenges & Design Decisions

### A. The Quoted Comma Challenge (RFC 4180 Compliance)
The S&P 500 CSV dataset contains embedded commas inside quoted location strings and company names, for example:
- `Headquarters Location`: `"Saint Paul, Minnesota"`, `"Dublin, Ireland"`
- `Security`: `"Nike, Inc."`
- `GICS Sub-Industry`: `"Apparel, Accessories & Luxury Goods"`

A naive `cut -d','` or `awk -F','` splits incorrectly on commas inside quotation marks, misaligning all subsequent columns.

#### Solution:
We utilize GNU Awk's field pattern parsing feature:
```awk
awk -v FPAT='([^,]+)|("[^"]+")' ...
```
This treats either non-comma tokens OR fully quoted substrings as atomic fields, guaranteeing that `"Phoenix, Arizona"` or `"Nike, Inc."` remain intact as single columns.

---

### B. Accurate Chronological Sorting
Certain companies have compound founding dates reflecting mergers or predecessor dates (e.g., `AbbVie`: `2013 (1888)`, `DuPont`: `2017 (1802)`).

The script uses regex extraction in Awk (`match(founded, /[0-9]{4}/)`) to isolate the primary 4-digit founding year into a numeric sort key, ensuring clean numerical sorting (`sort -t$'\t' -k1,1n -k2,2`) while preserving the full descriptive date in the final output.

---

### C. Clean Resource Hygiene
The script utilizes `mktemp` to isolate temporary working buffers and installs an automatic exit trap:
```bash
trap 'rm -f "${TMP_CSV}" "${TMP_PARSED}"' EXIT
```
This guarantees zero leftover temporary files even if the process is terminated prematurely.

---

## 3. Sample Sorted Output

```text
COMPANY NAME                             | HEADQUARTERS LOCATION            | FOUNDED        
-----------------------------------------+----------------------------------+----------------
State Street Corporation                 | Boston, Massachusetts            | 1792           
Colgate-Palmolive                        | New York City, New York          | 1806           
Hartford (The)                           | Hartford, Connecticut            | 1810           
Bunge Global                             | Chesterfield, Missouri           | 1818           
Consolidated Edison                      | New York City, New York          | 1823           
KeyCorp                                  | Cleveland, Ohio                  | 1825           
Citizens Financial Group                 | Providence, Rhode Island         | 1828           
McKesson Corporation                     | Irving, Texas                    | 1833           
Deere & Company                          | Moline, Illinois                 | 1837           
Procter & Gamble                         | Cincinnati, Ohio                 | 1837           
Berkshire Hathaway                       | Omaha, Nebraska                  | 1839           
...
Meta Platforms                           | Menlo Park, California           | 2004           
Airbnb                                   | San Francisco, California        | 2008           
Uber                                     | San Francisco, California        | 2009           
CrowdStrike                              | Austin, Texas                    | 2011           
DoorDash                                 | San Francisco, California        | 2012           
Solventum                                | Saint Paul, Minnesota            | 2023           
GE Vernova                               | Cambridge, Massachusetts         | 2024           
Paramount Skydance Corporation           | Los Angeles, California          | 2025 (Paramount Pictures 1912)
```
