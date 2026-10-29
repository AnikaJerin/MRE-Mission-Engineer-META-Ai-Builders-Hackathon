# Resource acquisition and rights

The source catalog is not a completed data download. No source file checksum is asserted
until the actual bytes are acquired. Preserve URL, retrieval time, license, version,
original filename and SHA-256 in a separate local acquisition receipt when downloading.

## Core: obtain these first

1. Main study: https://ntrs.nasa.gov/citations/20250004626
   - Under Available Downloads select `MRE_paper_revision_clean.pdf`.
   - Direct link is recorded in the manifest.
   - Save locally under `data/raw/yu2025/` (ignored by git).
   - Sections 2.2.2 and 3.1, Table 2: conditions and one-hour outcome.
   - Published PDF page 15 contains Table 2 (PDF page index 14).
2. Same record: `MRE_paper_revision_supplementary material_clean.pdf`.
   - Save in the same directory. It contains figures, not a verified raw CSV archive.
   - Figures S3 and S4-S6 are relevant to later interpretation/characterization cases.
3. Chemistry source: https://repo.astromat.org/view.php?id=3696&system=astro
   - Pin DOI 10.60520/IEDA/113696, version 1.0 (February 2025).
   - The schema/fixture foundation does not require this large download yet.
   - The planned first import is a small compatible whole-rock analysis subset. No
     particular row or sample selection has been verified in the actual CSV yet.

## Cataloged extensions (not required to finish Day 1)

- Lunar meteorites: https://repo.astromat.org/view.php?id=3699&system=astro
  DOI 10.60520/IEDA/113699, version 1.0. Portal lists 58.72 MB. Keep meteorite and
  Apollo sample populations distinct. The owner's 56 MB estimate is not a verified byte count.
- Lunar Regolith Database: https://doi.org/10.57745/NTSZ8G (2026, version 2).
  Obtain README and relevant CSV files from the repository, about 1 MB combined.
  Geotechnical properties do not establish molten-reactor properties.
- NASA Lunar Data Project: https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_data/
  Optional Apollo/ALSEP context; no bulk download. Not reactor telemetry.
- NASA vacuum-test poster: https://ntrs.nasa.gov/citations/20250004983
  Different reactor context; do not merge it into the hollow-anode case.
- OxideProperties: https://github.com/MrMattHumbert/OxideProperties
  Optional research code; pin a commit and review actual license, model domain and units
  before use. It is not installed or run by this project.

## Rights and claims

Astromat DataCite metadata identifies CC BY 4.0; retain attribution and source references.
The regolith repository displays Etalab Open Licence 2.0. NTRS public distribution does
not imply that every figure or PDF can be relicensed: its hollow-anode record notes
potential copyrighted portions, and the poster has a specific rights statement. Do not
bundle either PDF into the public repo without confirming reuse rights. The supplied
case contains a few attributed factual values and links, not copied paper images.

Never treat chemistry archive rows as reactor fault labels. Never describe a digitized
curve as raw telemetry. Keep author's interpretations separate from observed measurements.
