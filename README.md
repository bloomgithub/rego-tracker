# REGO Transaction Finder

🔗 **Live App**: [rego-tracker.streamlit.app](https://rego-tracker.streamlit.app)

A web application for analyzing REGO (Renewable Energy Guarantees of Origin) certificate transactions in the UK carbon credit market.

## Purpose

This tool tracks ownership changes of REGO certificates by comparing two Ofgem reports from different time periods. It identifies over-the-counter transactions and provides visibility into carbon credit trading activity.

## Features

- **Transaction Analysis** - Detects ownership changes between reports and shows which companies sold to which buyers
- **Current Ownership Tracking** - Displays current certificate holdings by company (non-expired, issued since April 2025)
- **Efficient Processing** - Handles large datasets with hundreds of thousands of rows
- **Export Functionality** - Download results as CSV files

## How to Use

1. Upload a "Previous Report" CSV from Ofgem
2. Upload a "Latest Report" CSV from Ofgem
3. Analysis runs automatically and displays two tables:
   - Transaction Summary (Seller → Buyer with volumes)
   - Current Ownership (Total MWh held by each company)
4. Download results using the export buttons

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/rego-transaction-finder.git
cd rego-transaction-finder

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Requirements

- Python 3.7+
- streamlit
- pandas

## Data Source

Reports are published by Ofgem twice weekly (Tuesday and Friday) via SharePoint.

## How It Works

1. Parses certificate IDs to extract station codes, sequence numbers, periods, and certificate types
2. Builds an index from the old report for efficient lookups
3. Compares certificates between reports to detect ownership changes
4. Aggregates transactions by company and calculates volumes
5. Filters current ownership for non-expired certificates issued since April 2025

## License

MIT License
