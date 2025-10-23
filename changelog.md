# Changelog

## 0.1.6 (2025-10-22)

- Removed the div that was showing the company conformed name.
- The dropdown to choose the cik is now wider and shows the company conformed name.
- New button that opens up the SEC's web page for the 13F-HR filings of the selected cik.
- Updated the project description in the `pyproject.toml`.
- Updated the `README`.

## 0.1.5 (2025-10-21)

- The scope of the function `parse_txt_data_to_raw_csv` is now limited to convert a single txt file to a single csv file.
- New function `parse_contents_to_raw_csv` that takes the list of selected contents and uses the function `parse_txt_data_to_raw_csv` to convert them to raw csv files.
- New function `parse_13f_fwf` which aims at parsing all the old nasty non standard FWF files.
- New function `generate_quarters` to reindex the quarters from the first to the last, used in the function `generate_all_quarters_figure`.

## 0.1.4 (2025-10-20)

- The function `parse_txt_data_to_raw_csv` now returns the set of cik for which something was imported.
- The function `get_cik_folders` has a new parameter `cik_set`.
- The function `convert_raw_csv_to_clean_csv` has a new parameter `cik_set`.
- The function `map_nameOfIssuer_variants` has a new parameter `cik_set`.
- The function `merge_portfolio_proportions` has a new parameter `cik_set`.
- Now the function `parse_txt_data_to_raw_csv` ignores the file in more situations when parsing issues occur.

## 0.1.3 (2025-10-19)

- Fixed a bug in the function `generate_all_quarters_figure` where the curves where not in the good order.

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
