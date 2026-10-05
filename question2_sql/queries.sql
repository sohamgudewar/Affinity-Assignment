-- ==============================================================================
-- File: question2_sql/queries.sql
-- Purpose: SQL solutions and technical explanations for Question 2 of the
--          Affinity Answers Data Engineer assessment (public Rfam database).
-- Author: Soham Gudewar (Data Engineer Applicant)
-- Target Database: Rfam (Public MySQL: mysql-rfam-public.ebi.ac.uk:4497)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Question 2.1: How many types of Acacia plants can be found in the taxonomy table?
-- ------------------------------------------------------------------------------
-- Analysis:
-- In botanical taxonomy, the genus 'Acacia' encompasses specific flowering plant
-- species. In the Rfam `taxonomy` table, species names follow binomial nomenclature
-- (e.g., 'Acacia acradenia', 'Acacia acuminata').
--
-- Query 1A (Strict Botanical Genus - Recommended):
-- Counts all taxa whose scientific name belongs directly to the genus Acacia.
SELECT COUNT(*) AS acacia_species_count
FROM taxonomy
WHERE species LIKE 'Acacia%';
-- Result: 326 species

-- Query 1B (Broader Taxonomic Lineage):
-- If considering any organism whose full phylogenetic lineage string contains 'Acacia'
-- (capturing varieties, sub-species, and related classifications in the lineage):
SELECT COUNT(*) AS acacia_lineage_count
FROM taxonomy
WHERE tax_string LIKE '%Acacia%';
-- Result: 357 entries


-- ------------------------------------------------------------------------------
-- Question 2.2: Which type of wheat has the longest DNA sequence?
-- Hint: Use the rfamseq and taxonomy tables.
-- ------------------------------------------------------------------------------
-- Analysis:
-- Wheat refers to cereal grain plants belonging to the botanical genus *Triticum*.
-- In Rfam, NCBI taxonomy categorizes wheat species under 'Triticum%' (such as
-- 'Triticum aestivum (bread wheat)' and 'Triticum durum (durum wheat)').
-- Filtering by 'Triticum%' also cleanly excludes non-plant organisms with 'wheat'
-- in their common names (e.g., 'Wheat dwarf virus', aphids, and sawflies).
--
-- Query:
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

-- Answer:
-- Type of wheat: Triticum durum (durum wheat)
-- Sequence length: 836,514,780 base pairs (Chromosome 3B, Accession: LT934116.1)
-- Runner up: Triticum aestivum (bread wheat) with 830,829,764 base pairs


-- ------------------------------------------------------------------------------
-- Question 2.3 & 2.4: Paginate a list of families and their longest DNA sequence lengths.
-- Requirements:
--   1. Include only families whose longest DNA sequence is greater than 1,000,000.
--   2. Sort by DNA sequence length in descending order.
--   3. Return family accession ID, family name, and maximum sequence length.
--   4. Return the 9th page, with 15 results per page.
-- ------------------------------------------------------------------------------
-- Pagination Mathematics:
--   Page size = 15
--   Page number = 9
--   OFFSET = (Page_Number - 1) * Page_Size = (9 - 1) * 15 = 120
--   LIMIT = 15
--
-- Tables and Relationships:
--   - `family` (f): Contains `rfam_acc` (Accession ID, e.g. RF00001) and `rfam_id` (Family Name, e.g. 5S_rRNA).
--   - `full_region` (fr): Connects families (`rfam_acc`) to sequences (`rfamseq_acc`).
--   - `rfamseq` (r): Contains `length` (DNA sequence length) and `rfamseq_acc`.
--   - Filter `fr.is_significant = 1` follows standard Rfam practice to exclude
--     low-scoring or clan-duplicate hits.
--
-- Query for Question 2.4:
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
