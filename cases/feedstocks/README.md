# Development feedstock record

`lhs1-yu2025.csv` is a compact transcription of the LHS-1 row in Table 1 of
the main study linked as `yu2025-main`. Values are oxide weight percentages
as printed, with no normalization, imputed components or added uncertainty.
This is a study-reported simulant composition, not a fresh independent assay
of a reactor batch or an extracted Astromat record. Keep the analysis ID intact.

CSV integrity, composition completeness and chemical accounting will be
implemented and checked in Day 2. The Day 1 `validate-case` command does not
parse or scientifically validate this separate feedstock file. Review its ten
values against Table 1 before using it. No oxygen inventory calculation has run.
