# Stellar Cyber Executive Report Generator App

This is a Python Streamlit app using the Stellar Cyber Public API to generate executive reports from Stellar Cyber.

## Getting Started

1. Clone the repository: `git clone https://github.com/stellarcyber/executive_report_generator.git`
2. Go to the cloned directory: `cd executive_report_generator`
3. Install the dependencies: `pip install -r requirements.txt`  or `pip3 install -r requirements.txt`
4. Run the app: `streamlit run app.py`  
   It should open a tab in your browser. (Tested in Chrome)
5. To stop the app: `CTRL-C`

> [!NOTE]
> To make sure you can run `streamlit`, make sure your python bin directory is added to your `PATH`. Alternatively you can use the absolute path to `streamlit` to run it.
> Tested with Python 3.10+

## Project Structure

- `app.py`: This file is the entry point of the Streamlit application. It sets up the user interface and the functionality of the app.
- `report_pages.py` This file contains functions for displaying Stellar Cyber report sections with streamlit.
- `stellar_api.py` This file is used for authenticating and making requests to the Stellar Cyber Public API.
- `stellar_plots.py` This file is used for generating the charts/plots used in the pdf report.
- `stellar_stats.py` This file collects all the stats used in the report into a class called StellarCyberStats.
- `stats` This directory contains several python files for collecting Stellar Cyber stats used in the report.
- `requirements.txt`: This file lists the dependencies required for the project. It is used by pip to install the dependencies.
- `README.md`: This file contains the documentation for the project. It provides information on how to set up and run the Streamlit app.

## Usage

1. Run the app: `streamlit run app.py`
2. Follow the instructions on the app to use it.
3. To stop the app: `CTRL-C`

## Customization

The `report_template` directory contains:
- `report-cover.jpg` -- image file used for the report cover. Replace this file with your own image/logo to customize the cover page of the report pdf.
- `report.html.template` -- HTML template file for the report. Copy/paste into a new .template file in the report_template directory to customize the generated report or to add new sections with your own data. Variables are rendered using the get_report_html() function in `report.py`.
