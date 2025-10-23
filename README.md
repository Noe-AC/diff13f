[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![Dash](https://img.shields.io/badge/Dash-app-red)]()

# DIFF13F

*DIFF13F* is a minimal Dash app to explore quarterly 13F filings, view top positions, track changes between quarters, and visualize holdings over time.

## ✨ Features
- 📊 Explore top positions in a single quarter
- 🔍 Spot largest changes between two quarters
- 📈 Track top positions over time with line plots across multiple quarters
- 💻 Minimal web interface powered by Dash

## 🛠️ Installation

Make sure Python 3.9+ is installed with pip.

**Install the `diff13f` library:**
   ```bash
	pip install git+https://github.com/Noe-AC/diff13f.git
   ```
This will add the `diff13f` command to your PATH.

## 🧩 Requirements

**Python libraries (installed automatically via pip):**

- ``dash`` and ``dash-bootstrap-components``: for the interactive web interface.
- ``pandas``: for data loading and comparison logic.

## 💡 Usage

1. Launch the app:
   ```bash
	diff13f
   ```
2. Select two 13F filings.
3.	View the comparison summary.

## 📸 Screenshots

![URL2TLDR Screenshot](screenshots/screenshot-v0.1.6.png)

## ⚖️ License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.