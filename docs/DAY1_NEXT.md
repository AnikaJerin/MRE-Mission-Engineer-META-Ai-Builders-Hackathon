# Finish Day 1 locally

The owner reported the initial nine tests and local CLI checks passing. The new
registration/dashboard code has not been run by the assistant.

## 1. Install updates and validate

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer validate-case
python -m mre_engineer data-status
```

The suite now contains thirteen tests. `not-registered` is expected before actual
files are registered. No Meta key or credit is needed.

## 2. Preview the lunar interface

```sh
python -m mre_engineer serve
```

Open http://127.0.0.1:8766. Use `docs/UI.md` for manual checks. Stop with Ctrl+C.

## 3. Acquire the two core PDFs first

Open https://ntrs.nasa.gov/citations/20250004626 and use Available Downloads:

- `MRE_paper_revision_clean.pdf`
- `MRE_paper_revision_supplementary material_clean.pdf`

Leave them in Downloads if convenient. Register using each actual filename:

```sh
python -m mre_engineer register-file --source yu2025-main --path "$HOME/Downloads/MRE_paper_revision_clean.pdf"
python -m mre_engineer register-file --source yu2025-supplement --path "$HOME/Downloads/MRE_paper_revision_supplementary material_clean.pdf"
python -m mre_engineer data-status
```

Registration writes receipts under ignored `outputs/acquisitions/`. It does not
copy or publish the paper. The header check catches ordinary HTML error pages;
it does not parse/certify the PDF, source identity or science. A local SHA-256 is
not an independently published checksum. Rights review remains separate.

If saved elsewhere, pass the actual path. Do not redownload solely because the
static catalog says files were not acquired: `data-status` is the local inventory.
Do not register sensitive/private files in this public-source catalog; the UI
export includes file hashes, sizes and registration times.

## 4. Human source check

Compare the case entries with sections 2.2.2 / 3.1 and Table 2. Compare the LHS-1
CSV with Table 1. Report transcription discrepancies. Chemistry import and
numerical tools come next; no bulk dataset download is needed for these checks.
Day 1 completion means the foundation and source records are checked, not that
engineering decisions are validated.
