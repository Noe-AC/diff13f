# Changelog

## 0.1.2 (2025-10-19)

- The green glow now oscillates in amplitude over time. By default this feature is not activated.
- New *Select the 13F txt files* button.
- New utility function `get_cik_folders`. It gets the list of available imported cik.
- New utility function `date_to_quarter`. It converts a date to a quarter.
- New utility function `parse_txt_data_to_raw_csv`. It parses the raw 13F txt files to raw csv files (i.e. one csv file per txt file).
- New utility function `cik_to_company_conformed_name`. It returns the most recent conformed company name corresponding to a given cik.
- New utility function `convert_raw_csv_to_clean_csv`. It converts the raw csv files to a cleaned up version (i.e. one csv file per quarter).
- New utility function `map_nameOfIssuer_variants`. It maps the variants of `nameOfIssuer`.
- New utility function `merge_portfolio_proportions`. It merges the proportions and shares of a cik (i.e. `central_index_key`) in a file with one column per quarter.
- New dropdown that shows the available imported cik.
- New tabs to select three views: 1. top % of the portfolio of a given quarter, top variations between a pair of quarters, portfolio evolution in time over the available quarters.
- New function `get_cik_numbers` that takes the list of cik numbers (as string).
- New function `generate_one_quarter_figure` that generates the figure of the top N holdings of a cik at a given quarter.
- New function `generate_two_quarters_figure` that generates the figure of the top N variations of a cik between two given quarters.
- New function `generate_all_quarters_figure` that generates the figure of the top N titles of a cik during all available quarters.
- And many other layout functions and callbacks.
- New screenshot of the app.

## 0.1.1 (2025-10-15)

- Created the repo.
- New folder `screenshots/` to put screenshots of the app.
- New folder `src/`.
- New folder `src/diff13f/`.
- New folder `src/diff13f/assets/`.
- New file `pyproject.toml`.
- New file `src/diff13f/__init__.py`
- New file `src/diff13f/app.py`
- New file `src/diff13f/assets/style.css`
- New file `src/diff13f/assets/favicon.ico`
- New file `src/diff13f/assets/DIFF13F_1024x1024.png`
- First sketch of the layout in the app.
