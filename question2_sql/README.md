<!--
================================================================================
File: question2_sql/README.md
Purpose: Comprehensive answers, query explanations, and execution instructions
         for Question 2 (SQL & Databases) using the public Rfam database.
Author: Soham Gudewar (Data Engineer Applicant)
================================================================================
-->

# Question 2: SQL and Databases (Public Rfam Database)

Solutions, queries, botanical/genomic context, and automated verification scripts for the **Rfam** public MySQL database.

---

## 1. Database Access Details

The queries are executed against the official European Bioinformatics Institute (EMBL-EBI) public read-only Rfam instance:

| Parameter | Value |
| :--- | :--- |
| **Host** | `mysql-rfam-public.ebi.ac.uk` |
| **Port** | `4497` |
| **User** | `rfamro` |
| **Password** | *(None / blank)* |
| **Database** | `Rfam` |

---

## 2. Answers & Query Breakdown

### Sub-Question 1: How many types of Acacia plants can be found in the taxonomy table?

#### Botanical & Taxonomic Context
In botanical classification, species belonging to the *Acacia* genus follow standard binomial nomenclature where the first term is the capitalized genus name (e.g., *Acacia acradenia*, *Acacia acuminata*).

In the Rfam `taxonomy` table, we evaluate two queries:

1. **Strict Botanical Genus (Recommended):**
   ```sql
   SELECT COUNT(*) AS acacia_species_count
   FROM taxonomy
   WHERE species LIKE 'Acacia%';
   ```
   - **Answer:** **326** plant species in the genus *Acacia*.

2. **Broader Taxonomic Lineage:**
   ```sql
   SELECT COUNT(*) AS acacia_lineage_count
   FROM taxonomy
   WHERE tax_string LIKE '%Acacia%';
   ```
   - **Answer:** **357** taxonomic records whose lineage string contains *Acacia* (including sub-species and infraspecific taxa).

---

### Sub-Question 2: Which type of wheat has the longest DNA sequence?

#### Hint & Genomics Context
Wheat corresponds to cereal grasses in the genus ***Triticum***. Joining `rfamseq` (which stores DNA sequence lengths) with `taxonomy` on `ncbi_id` allows us to isolate genuine wheat organisms while filtering out non-plant entities that contain "wheat" in their colloquial name (such as *Wheat dwarf virus* or agricultural pests like aphids).

#### SQL Query:
```sql
SELECT 
    t.species AS wheat_type,
    r.rfamseq_acc AS sequence_accession,
    r.length AS sequence_length,
    r.description AS sequence_description
FROM rfamseq r
JOIN taxonomy t ON r.ncbi_id = t.ncbi_id
WHERE t.species LIKE 'Triticum%'
ORDER BY r.length DESC
LIMIT 1;
```

#### Answer:
* **Winning Wheat Type:** **`Triticum durum (durum wheat)`**
* **DNA Sequence Length:** **836,514,780 base pairs**
* **INSDC Accession ID:** `LT934116.1`
* **Chromosome / Description:** *Triticum turgidum subsp. durum* genome assembly, Chromosome 3B.
* *(Runner-up: Triticum aestivum (bread wheat) with 830,829,764 bp, Chromosome 3B, Accession LS992087.1)*

---

### Sub-Question 3 & 4: Paginate Families and Longest DNA Sequence Lengths

#### Requirements:
1. Include only families whose longest DNA sequence is greater than 1,000,000 base pairs.
2. Be sorted by DNA sequence length in descending order.
3. Return the family accession ID (`rfam_acc`), family name (`rfam_id`), and maximum sequence length.
4. Return the **9th page**, with **15 results per page**.
5. Write the SQL query for this.

#### Pagination Calculation:
* Page Size = 15
* Page Number = 9
* **Offset Formula:** $\text{OFFSET} = (\text{Page Number} - 1) \times \text{Page Size} = (9 - 1) \times 15 = \mathbf{120}$
* **Limit:** $\mathbf{15}$

#### Canonical SQL Query:
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

#### Query Mechanics & Optimization:
* **`family` (`f`):** Stores family-level metadata (`rfam_acc` e.g., `RF00001`, `rfam_id` e.g., `5S_rRNA`).
* **`full_region` (`fr`):** Cross-reference table associating families to sequence accessions (`rfamseq_acc`).
* **`rfamseq` (`r`):** Stores sequence coordinates and genomic base pair length (`length`).
* **`fr.is_significant = 1`:** Follows standard Rfam best practices to filter out low-confidence hits and duplicate clan matches.
* **`HAVING max_sequence_length > 1000000`:** Enforces the filter on aggregate maximum sequence length.

---

## 3. Automated Verification Runner

An automated Python script is included to run and test these queries live against the Rfam server:

```bash
# Run Question 1 & Question 2 (fast live check)
python verify_queries.py

# Run Question 1 only
python verify_queries.py -q 1

# Run Question 2 only
python verify_queries.py -q 2

# Run Question 3 & 4 (heavy join pagination)
python verify_queries.py -q 3
```
