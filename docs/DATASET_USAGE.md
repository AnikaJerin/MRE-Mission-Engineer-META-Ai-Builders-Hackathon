# Which originally proposed datasets are actually used?

Repository audit, 28 October 2026: the four archive entries are catalogued in
sources/manifest.json, but no active accounting, investigation or evaluation module
loads their raw datasets. The accounting feedstock is cases/feedstocks/lhs1-yu2025.csv,
transcribed from Table 1 of Yu et al. (NASA NTRS 20250004626). It is not an Astromat
subset. Published MRE experimental summaries and NTRS source records underpin the
current evidence reviews. Do not claim the four archives were used to validate them.

| Proposed resource | Current use | Appropriate potential use / boundary |
|---|---|---|
| Astromat lunar samples | Metadata catalogue only | A future provenance-preserving oxide analysis/sample selector and oxygen-inventory comparison. Composition does not establish extraction yield, corrosion or an optimal reactor test. |
| Astromat lunar meteorites | Metadata catalogue only | Optional wider chemistry variation; not a substitute for the exact tested simulant or reactor experiment. Current portal describes elemental/oxide/isotope composition and analytical metadata. |
| Lunar Regolith Database | Metadata catalogue only; current browser fetch unavailable | Potential simulant/soil-property context after file, schema, license and relevant property review. No unverified molten-electrolyte kinetics/corrosion model should be inferred from it. |
| NASA Lunar Data Project | Metadata catalogue only | Apollo/ALSEP environment/soil context for a different surface-system question. The official catalogue is not an MRE reactor-log archive and includes scans as well as tables/CDF. |

The earlier all-CSV/no-PDF description was too broad: NASA's LDP is a heterogeneous
restoration catalogue. Download sizes from the proposal are not verified local byte
counts. The current meteorite portal lists 58.72 MB, so avoid treating the screenshot's
56 MB as an exact size. No need to download these archives to finish current T12.

References reviewed:
- https://repo.astromat.org/view.php?id=3699&system=astro (redirects to https://ada.astromat.org/doi/10.60520/IEDA/113699)
- https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_data/
- Lunar-sample entry: https://repo.astromat.org/view.php?id=3696&system=astro (redirect destination inaccessible in this browser review)
- Regolith entry: https://doi.org/10.57745/NTSZ8G (current fetch unavailable; do not describe contents as newly inspected)

Keep resources as optional catalogue entries unless their rows are actually inspected
and ingested. Adding a large archive is not, by itself, stronger decision validation.
