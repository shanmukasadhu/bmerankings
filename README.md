# BMERankings

A metrics-based ranking of biomedical engineering research institutions, in the style of [CSRankings](https://csrankings.org/).

## How it works

- Publications (articles and reviews, 2016–2026) come from selected BME journals via [OpenAlex](https://openalex.org/).
- Each paper's credit is split evenly among its authors (adjusted count) and goes to the university listed on the paper. Hospitals, companies and non-university institutes get no credit; medical schools and departments count toward their parent university.
- Institutions are ranked by the geometric mean of (adjusted count + 1) across the selected subareas, the same formula CSRankings uses.
- For general-scope journals (marked † on the site), only papers with at least one author in a biomedical engineering or bioengineering department count.
- Journals are grouped into 8 categories plus a Multidisciplinary group; see `scripts/config.py`.

## Limits

- There is no hand-curated faculty list, so author lists include students and postdocs.
- OpenAlex author disambiguation is automatic and can split or merge people.
- Some journals in `scripts/config.py` are not fetched yet; the site footer lists them.

## Rebuilding the data

```sh
# fetch raw paper data into raw/ (resumable; one .json.gz per journal)
python3 scripts/fetch_initial.py raw              # the original 16 journals
python3 scripts/fetch.py raw scripts/plan.json    # the rest of the journal list
# build institutions.json and authors.json
python3 scripts/aggregate.py raw .
```

OpenAlex limits keyless requests to a small daily budget. Raw data is not committed.

## Credits

Layout modeled on CSRankings by Emery Berger. Not affiliated with CSRankings. Flags from [flagcdn](https://flagcdn.com/). Publication data from OpenAlex (CC0).
