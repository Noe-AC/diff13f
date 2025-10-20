"""
DIFF13F
Noé Aubin-Cadot

Steps to use the app:
1. Install :
    pip install -e .
2. Run the app:
    diff13f
A web browser should open with the app at:
    http://127.0.0.1:8050/

For development:
    python src/diff13f/app.py
"""

################################################################################
################################################################################
# Import libraries

import dash
from dash import Dash, html, dcc, Input, Output, State, no_update, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import webbrowser
import os
import random
import time
import math
import base64
import io
import glob
import os
import re
import shutil
import json
import pandas as pd
import xmltodict # pip install xmltodict
import polars as pl
import colorsys

TEXTBOX_HEIGHT = "220px"
SPINNER_TYPE = "dot"
MAX_WIDTH = "1000px"
FIG_HEIGHT = 520
FIG_WIDTH = 960

################################################################################
################################################################################
# Utility functions

def get_cik_folders():
    # Look at the cik folders in the output directory
    cik_folders = sorted(glob.glob("output/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"))
    # Return the result
    return cik_folders

def get_cik_quarters(
    cik,
    ascending = True
):
    # Look at the cik folders in the output directory
    quarters = sorted([filename.split('/')[-1].split('.')[0] for filename in glob.glob(f"output/{cik}/clean/*.csv")])
    # Reverse if needed
    if not ascending:
        quarters = quarters[::-1]
    # Return the quarters
    return quarters

def date_to_quarter(
    date_str: str,
)->str:
    """
    Convert a date 'YYYY-MM-DD' into a quarter string 'YYYY-q[N]'
    """
    year, month, _ = date_str.split('-')
    month = int(month)
    if 1 <= month <= 3:
        quarter = 'q1'
    elif 4 <= month <= 6:
        quarter = 'q2'
    elif 7 <= month <= 9:
        quarter = 'q3'
    elif 10 <= month <= 12:
        quarter = 'q4'
    else:
        raise ValueError(f"Invalid month: {month}")
    return f"{year}-{quarter}"

def parse_txt_data_to_raw_csv(
    contents_list,
    filename_list,
    do_scrape_xml = True,
    do_scrape_txt = True,
    verbose       = False,
):
    # Define some patterns to look for
    patterns = {
        'accession_number': r'ACCESSION NUMBER:\s*(\d+)',
        'conformed_period_of_report': r'CONFORMED PERIOD OF REPORT:\s*(\d+)',
        'filed_as_of_date': r'FILED AS OF DATE:\s*(\d+)',
        'company_conformed_name': r'COMPANY CONFORMED NAME:\s*(.+)',
        'central_index_key': r'CENTRAL INDEX KEY:\s*(\d+)',
    }
    # Loop over the input files
    for content, filename in zip(contents_list, filename_list):
        # Decode the base64 file
        content_type, content_string = content.split(",")
        text = base64.b64decode(content_string).decode("utf-8")
        # Fine some informations about the file
        fields = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            fields[key] = match.group(1) if match else None
        # Define some variables
        central_index_key          = fields['central_index_key']
        accession_number           = fields['accession_number']
        company_conformed_name     = fields['company_conformed_name']
        filed_as_of_date           = fields['filed_as_of_date']
        conformed_period_of_report = fields['conformed_period_of_report']
        # Format dates as YYYY-MM-DD
        conformed_period_of_report = f"{conformed_period_of_report[:4]}-{conformed_period_of_report[4:6]}-{conformed_period_of_report[6:]}"
        filed_as_of_date           = f"{filed_as_of_date[:4]}-{filed_as_of_date[4:6]}-{filed_as_of_date[6:]}"
        # Convert the date to a quarter
        quarter = date_to_quarter(
            date_str = conformed_period_of_report,
        )
        # Print some infos
        if verbose:
            print(f"{central_index_key} / {company_conformed_name} / filed {filed_as_of_date} / period {conformed_period_of_report} / quarter {quarter}")
        # Create the output directory for the company metadata
        output_dir_meta = f"output/{central_index_key}/meta"
        os.makedirs(output_dir_meta, exist_ok=True)
        # Export the metadata
        metadata = {
            "central_index_key": central_index_key,
            "accession_number": accession_number,
            "company_conformed_name": company_conformed_name,
            "filed_as_of_date": filed_as_of_date,
            "conformed_period_of_report": conformed_period_of_report,
            "quarter": quarter
        }
        output_file_meta = f"{output_dir_meta}/{quarter}_{filed_as_of_date}.json"
        if verbose:
            print("Exporting meta file :",output_file_meta)
        with open(output_file_meta, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

        # Create the output directory for the raw csv files
        output_dir_raw = f"output/{central_index_key}/raw"
        os.makedirs(output_dir_raw, exist_ok=True)
        # Keep only what we need
        matches_start   = re.finditer('<XML>',text)
        positions_start = [match.start() for match in matches_start]
        matches_end     = re.finditer('</XML>',text)
        positions_end   = [match.start() for match in matches_end]
        if len(positions_start)>0:
            if verbose:
                print('XML found')
            scraping_type = 'XML'
            if not do_scrape_xml:
                continue
            start = positions_start[-1]
            end   = positions_end[-1]
            text = text[start+6:end]
            # Convert remaining XML text to a dict
            d       = xmltodict.parse(text)
            d_info  = d['informationTable']['infoTable']
            # Conversion en DataFrame
            df_out = pd.DataFrame({
                'nameOfIssuer': [d_i['nameOfIssuer'] for d_i in d_info],
                'titleOfClass': [d_i['titleOfClass'] for d_i in d_info],
                'cusip': [d_i['cusip'] for d_i in d_info],
                'value': [d_i['value'] for d_i in d_info],
                'shrsOrPrnAmt_sshPrnamt': [d_i['shrsOrPrnAmt']['sshPrnamt'] for d_i in d_info],
                'shrsOrPrnAmt_sshPrnamtType': [d_i['shrsOrPrnAmt']['sshPrnamtType'] for d_i in d_info],
                'investmentDiscretion': [d_i['investmentDiscretion'] for d_i in d_info],
                'otherManager': [d_i['otherManager'] for d_i in d_info],
                'votingAuthority_Sole': [d_i['votingAuthority']['Sole'] for d_i in d_info],
                'votingAuthority_Shared': [d_i['votingAuthority']['Shared'] for d_i in d_info],
                'votingAuthority_None': [d_i['votingAuthority']['None'] for d_i in d_info],
            })
            # Add the % of the portfolio
            df_out['portfolio %'] = 100*df_out['value'].astype(int)/df_out['value'].astype(int).sum()
            # Sort by the name
            df_out.sort_values(by='nameOfIssuer',inplace=True)
            # Export the file
            output_file = f"{output_dir_raw}/{quarter}_{filed_as_of_date}.csv"
            if verbose:
                print("Exporting :",output_file)
            df_out.to_csv(output_file,index=False)
            if verbose:
                print('CSV file exported.')
        else:
            if verbose:
                print('No XML found')
            scraping_type = 'TXT'
            if not do_scrape_txt:
                continue
            # Keep only what we need
            matches_start   = re.finditer('<DOCUMENT>',text)
            positions_start = [match.start() for match in matches_start]
            matches_end     = re.finditer('</DOCUMENT>',text)
            positions_end   = [match.start() for match in matches_end]
            start = positions_start[-1]
            end   = positions_end[-1]
            text  = text[start:end+11]
            # Find the main table
            matches_start   = re.finditer('<TABLE>',text)
            positions_start = [match.start() for match in matches_start]
            matches_end     = re.finditer('</TABLE>',text)
            positions_end   = [match.start() for match in matches_end]
            start = positions_start[-1]
            end   = positions_end[-1]
            text = text[start:end+8]
            rows = text.split('\n')
            # If the text is too short
            if len(rows)<10:
                print(f"WARNING: the file {filename} is too short, it is skipped.")
                continue
            if rows[9]=='<C>':
                bad_parsing=1
                if verbose:
                    print('BAD_PARSING - will be fixed.')
                rows = rows[10:-1]
            else:
                bad_parsing=0
                rows = rows[6:-1]
            # Fix a possible bad parsing of some files
            if bad_parsing:
                if verbose:
                    print('Fixed the parsing')
                rows = [i+'        '+j for i,j in zip(rows[::2],rows[1::2])]
            # Convert the rows to a text
            text = '\n'.join(rows)
            # Convert the text to a DataFrame
            df_text = pd.read_fwf(io.StringIO(text),header=None)
            if df_text.shape[1]!=10:
                if verbose:
                    print('PARSING ISSUE WITH FWF FILE - we fix it.')
                    print(df_text.columns.to_list())
                m = df_text.shape[1]
                if m==9:
                    if verbose:
                        print('m='+str(m))
                        print('m (old) =',m)
                    widths = [29,17,10,8,8,3,11,24,9,9]
                    df_text = pd.read_fwf(io.StringIO(text),header=None,widths=widths)
                    m = df_text.shape[1]
                    if verbose:
                        print('m (new) =',m)
                        print('Fixed.')
                elif m==11:
                    if verbose:
                        print('m (old) =',m)
                    widths = [29,17,10,8,8,3,11,24,9,7]
                    df_text = pd.read_fwf(io.StringIO(text),header=None,widths=widths)
                    m = df_text.shape[1]
                    if verbose:
                        print('m (new) =',m)
                        print('Fixed.')
                elif m==8:
                    if verbose:
                        print('m (old) =',m)
                    widths = [29,17,10,8,8,3,11,24,9,9]
                    df_text = pd.read_fwf(io.StringIO(text),header=None,widths=widths)
                    m = df_text.shape[1]
                    if verbose:
                        print('m (new) =',m)
                        print('Fixed.')
                else:
                    print('ERROR - m='+str(m))
                    quit()
            columns = [
                'nameOfIssuer',
                'titleOfClass',
                'cusip',
                'value',
                'shrsOrPrnAmt_sshPrnamt',
                'shrsOrPrnAmt_sshPrnamtType',
                'investmentDiscretion',
                #'otherManager',
                'votingAuthority_Sole',
                'votingAuthority_Shared',
                'votingAuthority_None',
            ]
            df_text.columns = columns
            df_text['otherManager'] = 0
            columns = [
                'nameOfIssuer',
                'titleOfClass',
                'cusip',
                'value',
                'shrsOrPrnAmt_sshPrnamt',
                'shrsOrPrnAmt_sshPrnamtType',
                'investmentDiscretion',
                #'otherManager',
                'votingAuthority_Sole',
                'votingAuthority_Shared',
                'votingAuthority_None',
            ]
            df_text = df_text[columns]
            output_file = f"{output_dir_raw}/{quarter}_{filed_as_of_date}.csv"
            df_text['value'] = df_text['value'].fillna(0)
            df_text['portfolio %'] = 100*df_text['value'].astype(int)/df_text['value'].astype(int).sum()
            df_text.sort_values(by='nameOfIssuer',inplace=True)
            if verbose:
                print("Exporting :",output_file)
            df_text.to_csv(output_file,index=False)
            if verbose:
                print('CSV file exported.')

    # Cleanup
    # Get the list of cik folders
    cik_folders = get_cik_folders()
    # Loop over the cik folders
    for cik_folder in cik_folders:
        # Take the cik corresponding to the folder
        cik = cik_folder.split('/')[1]
        # Look at the csv files in the raw folder
        input_files_raw = sorted(glob.glob(f"output/{cik}/raw/*.csv"))
        # If the raw folder is empty, delete the cik from the output folder
        if len(input_files_raw)==0:
            shutil.rmtree(f"output/{cik}")
            print(f"WARNING: the so-called 'raw' folder is empty. Deleting the imported data for cik={cik}.")
        else:
            if verbose:
                print(f"Number of raw files found for cik={cik}: {len(input_files_raw)}.")

def cik_to_company_conformed_name(
    cik,
    verbose = False,
):
    if not cik:
        return ""

    # Cherche tous les fichiers meta pour ce CIK
    meta_path = f"output/{cik}/meta/*.json"
    meta_files = sorted(glob.glob(meta_path), reverse=True)  # trier du plus récent au plus ancien

    if not meta_files:
        return ""

    # Ouvre le fichier le plus récent
    latest_file = meta_files[0]
    with open(latest_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    company_conformed_name = metadata.get("company_conformed_name", "")
    return company_conformed_name

def convert_raw_csv_to_clean_csv(
    verbose = False,
):
    # Get the list of cik folders
    cik_folders = get_cik_folders()
    # Loop over the folders
    for cik_folder in cik_folders:
        # Take the central_index_key (cik)
        cik = cik_folder.split('/')[1]
        if verbose:
            print(cik)
        # Create the output folder
        clean_dir = f"output/{cik}/clean"
        os.makedirs(clean_dir, exist_ok=True)
        # Look at the csv files in the raw folder
        input_dir = f'output/{cik}/raw'
        input_files = sorted(glob.glob(f"{input_dir}/*.csv"))
        if not input_files:
            raise Exception(f"ERROR: missing so-called 'raw' csv files for cik={cik}.")
        # Create a dict that maps a quarter to the list of files of that quarter
        d_quarter_to_files = dict()
        for input_file in input_files:
            # Extract the quarter part before the first underscore
            quarter = os.path.basename(input_file).split('_')[0]
            if quarter not in d_quarter_to_files:
                d_quarter_to_files[quarter] = []
            d_quarter_to_files[quarter].append(input_file)
        # Loop over each quarter
        for quarter, input_files in d_quarter_to_files.items():
            dst_file = os.path.join(clean_dir, f"{quarter}.csv")
            if len(input_files) == 1:
                src_file = input_files[0]
                # Destination file: keep only the quarter part as name
                shutil.copy2(src_file, dst_file)
                if verbose:
                    print(f"Copied {src_file} -> {dst_file}")
            else:
                # Multiple files, concatenate and remove duplicates by keeping the most recent
                df_list = []
                for input_file in input_files:
                    df = pd.read_csv(input_file)
                    df_list.append(df)
                df_concat = pd.concat(df_list, ignore_index=True)
                # Keep only the latest row per nameOfIssuer
                df_out = df_concat.drop_duplicates(subset='nameOfIssuer', keep='last').copy()
                # Uodate the % of the portfolio
                df_out['portfolio %'] = 100*df_out['value'].astype(int)/df_out['value'].astype(int).sum()
                # Sort by the name
                df_out.sort_values(by='nameOfIssuer',inplace=True)
                # Save the cleaned CSV
                df_out.to_csv(dst_file, index=False)
                if verbose:
                    print(f"Concatenated {len(input_files)} files for {cik} {quarter} -> {dst_file}")

def map_nameOfIssuer_variants(
    verbose = False,
):
    """
    For each cik, this function generates a csv of the unique triples (nameOfIssuer, titleOfClass, cusip).
    It also creates a column 'name' which is the first nameOfIssuer found for a given cusip.
    The column 'name' is useful to handle all the variants of names of a same company.
    This file will be used down the road to identify the unique name of issuers.
    """
    # Get the list of cik folders
    cik_folders = get_cik_folders()
    # Loop over the folders
    for cik_folder in cik_folders:
        # Take the central_index_key (cik)
        cik = cik_folder.split('/')[1]
        if verbose:
            print(cik)
        # Input directory
        input_dir = f"output/{cik}/clean"
        # List the files
        input_files = sorted(glob.glob(f"{input_dir}/*.csv"))
        if not input_files:
            raise Exception(f"ERROR: The so-called 'clean' files are missing for cik={cik}.")
        # Lazy loading
        l_df_lazy = []
        for input_file in input_files:
            df_lazy = pl.scan_csv(input_file).select(["nameOfIssuer", "titleOfClass", "cusip"])
            l_df_lazy.append(df_lazy)
        # Lazy vertical concat
        df_all_lazy = pl.concat(l_df_lazy)
        # Lazy remove the duplicates on the three columns
        df_all_lazy = df_all_lazy.unique(subset=["nameOfIssuer", "titleOfClass", "cusip"])
        # Collect the files in memory
        df_all = df_all_lazy.collect()
        # Remove rows with at least one missing value
        df_all = df_all.drop_nulls()
        # Alphabetic sorting on nameOfIssuer
        df_all = df_all.sort("nameOfIssuer")
        # Create a column 'name' which is the first nameOfIssuer for a given cusip
        df_all = df_all.with_columns([
            # Create the column 'name' which is the first nameOfIssuer for that cusip
            pl.col("nameOfIssuer").first().over("cusip").alias("name")
        ])
        # Define the output directory
        output_dir = f"output/{cik}/mapping"
        # Make sure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        # Define the output file name
        output_file = f"output/{cik}/mapping/nameOfIssuer_titleOfClass_cusip.csv"
        # Export the dataframe
        df_all.write_csv(output_file)

def merge_portfolio_proportions(
    verbose = False,
):
    """
    L'implémentation avec Polars est beaucoup plus rapide que Pandas.
    Soit Pandas prend 500 secondes ou 75 Go de RAM.
    Soit Polars prend presque pas de RAM et roule en une fraction de seconde...
    """
    # Mapping to the columns names
    target_variable_to_target_column = {
        'proportion': 'portfolio %',
        'shares': 'shrsOrPrnAmt_sshPrnamt',
    }
    # Define the merge keys
    merge_keys = [
        'nameOfIssuer',
        'cusip',
        'name',
    ]
    # Define the target variables
    target_variables  = [
        'proportion',
        'shares',
    ]
    # Get the list of cik folders
    cik_folders = get_cik_folders()
    # Loop over the cik folders
    for cik_folder in cik_folders:
        # Take the cik
        cik = cik_folder.split('/')[1]
        # Read the csv containing the pairs ('nameOfIssuer', 'name')
        input_file_map = f"output/{cik}/mapping/nameOfIssuer_titleOfClass_cusip.csv"
        df_map = pl.read_csv(input_file_map, columns=['nameOfIssuer', 'name'])
        df_map = df_map.unique(subset=['nameOfIssuer']) # Keep only a single row per nameOfIssuer
        # Define the input path containing the clean csv files
        input_path = f'output/{cik}/clean/'
        # Loop over the merge keys
        for merge_key in merge_keys:
            # Loop over target variables
            for target_variable in target_variables:
                # Take the target column name corresponding to the target variable
                target_column = target_variable_to_target_column[target_variable]
                # Take the list of input files
                input_files = sorted(glob.glob(os.path.join(input_path, '*.csv')))
                # Create a list of dataframes
                l_df = []
                # Loop over the input files
                for input_file in input_files:
                    # Take the quarter
                    quarter = os.path.basename(input_file).split('.')[0]  # '1999-q3'
                    if merge_key!='name':
                        # Read the csv and keep only the columns (merge_key, target_column)
                        df = pl.read_csv(input_file, columns=[merge_key, target_column])
                    else:
                        # Read the dataframe
                        df = pl.read_csv(input_file, columns=['nameOfIssuer', target_column])
                        # Map the 'nameOfIssuer' to 'name' using the dataframe with columns ('nameOfIssuer', 'name')
                        df = df.join(
                            df_map,
                            on = 'nameOfIssuer',
                            how = 'left',
                        )
                        # Keep only the columns ('name', target_column)
                        df = df.select(['name', target_column])
                    # Groupby sum over the column name
                    df = df.group_by(merge_key).agg(
                        pl.sum(target_column).alias(target_column)
                    )
                    # Add a column 'quarter' to the dataframe whose value is equal to the quarter 
                    df = df.with_columns(pl.lit(quarter).alias("quarter"))
                    l_df.append(df)
                # Vertical concat
                df_all = pl.concat(l_df, rechunk=True)
                # Pivot for wide format
                df_out = df_all.pivot(
                    values             = target_column,
                    index              = merge_key,
                    on                 = "quarter",
                    aggregate_function = "first"
                )
                # Sort the columns to have the most recent quarter to the left
                cols = df_out.columns
                cols = [merge_key] + sorted([c for c in cols if c != merge_key], reverse=True)
                df_out = df_out.select(cols)
                # Sort the rows alphabetically by the merge key ('nameOfIssuer' or 'cusip')
                df_out = df_out.sort(merge_key)
                # Define the output directory
                output_dir = f'output/{cik}/merge'
                # Make sure the output directory exists
                os.makedirs(output_dir, exist_ok=True)
                # Define the output file name
                output_file = f'{output_dir}/{merge_key}_to_{target_variable}.csv'
                # Export the output file
                df_out.write_csv(output_file)
                if verbose:
                    print(f"Saved merged file {output_file}")

################################################################################
################################################################################
# Create the layout of the app

def create_header():
    return html.A(
        href="https://github.com/Noe-AC/diff13f",
        target="_blank",  # ouvre dans un nouvel onglet
        children=[
            html.Img(
                src="/assets/DIFF13F_1024x1024.png",
                style={
                    "height": "40px",
                    "width": "40px",
                    "marginRight": "10px",
                    "display": "block",
                    "borderRadius": "5px",
                    "border": "1px solid #00ff66",  # vert matrice
                    "boxShadow": "0 0 20px rgba(0, 255, 102, 0.7)",  # halo vert léger
                },
            ),
            html.H1(
                "DIFF13F",
                style={
                    "fontSize": "24px",
                    "margin": 0,
                    "lineHeight": "40px",
                    "fontWeight": "600",
                    "textShadow": "0 0 1px #00ff66, 0 0 3px #00ff66, 0 0 2px #00ff66",  # halo vert léger
                    "color": "black",
                    #"fontWeight": "200",  # lettres plus fines
                },
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "marginBottom": "20px",
            "gap": "10px",
            "padding": "0",
            "textDecoration": "none",  # retire le soulignement
            "color": "inherit",         # garde la couleur du texte
            "cursor": "pointer",        # curseur main au survol
        },
    )

def create_import_bar():
    # Take the list of cik folders available
    cik_folders = get_cik_folders()

    if len(cik_folders)==0:
        # CIK dropdown
        dropdown_options     = []
        dropdown_value       = None
        dropdown_placeholder = "No CIK found."
        # Conformed company name
        conformed_company_name = ""
    else:
        # CIK dropdown
        dropdown_options     = [{"label": cik_folder.split('/')[1], "value": cik_folder.split('/')[1]} for cik_folder in cik_folders]
        cik                  = cik_folders[0].split('/')[1]
        dropdown_value       = cik
        dropdown_placeholder = "Select CIK"
        # Conformed company name
        conformed_company_name = cik_to_company_conformed_name(
            cik = cik,
        )

    # Return the layout
    return html.Div(
        children = [
            # Sélecteur de fichiers
            dcc.Upload(
                id="file-upload-selector",
                children = html.Div([
                    "Import 13F txt files"
                ]),
                style = {
                    "width": "250px",
                    "height": "40px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",  # horizontal
                    #"margin": "20px auto",
                    #"backgroundColor": "#1a1a1a",
                    "backgroundColor": "black",
                    "color": "white",
                    "cursor": "pointer",
                    "display": "flex",               # flexbox
                    "justifyContent": "center",      # centre horizontalement
                    "alignItems": "center",          # centre verticalement
                    "boxShadow": "0 0 10px #00ffcc",
                },
                multiple = True,
            ),
            # Conteneur qui contiendra soit le spinner soit le dropdown
            html.Div(
                children = [
                    dcc.Loading(
                        id       = "loading-cik-dropdown",
                        type     = "default",  # "default", "circle" ou "cube"
                        color    = "#00ffcc",  # couleur du spinner
                        style    = {
                            "display": "flex",
                            "flexDirection": "row",
                            #"alignItems": "center",
                            "gap": "10px",
                            #"flex": "1",  # pour occuper l'espace restant
                        },
                        children = [
                            # Dropdown des CIK disponibles
                            dcc.Dropdown(
                                id="cik-dropdown",
                                options     = dropdown_options,
                                value       = dropdown_value,
                                placeholder = dropdown_placeholder,
                                clearable=False,
                                style={
                                    "width": "160px",
                                    "height": "40px",
                                    "color": "white",
                                    "backgroundColor": "black",
                                    "borderRadius": "5px",
                                    "boxShadow": "0 0 10px #00ffcc",
                                    "fontFamily": "monospace",
                                    "flex": "1",
                                    "minWidth": "0",  # important pour que flex fonctionne dans un parent flex
                                },
                                className="cyberpunk-dropdown",
                            ),
                        ],
                    ),
                ],
                style={
                    "flex": "1",
                    "display": "flex",
                    #"backgroundColor": 'orange',
                },
            ),
            # Most recent conformed company name associated to the cik
            html.Div(
                id="latest-company-name",
                children = conformed_company_name,
                style={
                    # Size
                    "width": "100%",
                    "height": "40px",
                    # Text color
                    "color": "white",
                    # Background color
                    "backgroundColor": "black",
                    # Border
                    "borderWidth": "1px",
                    "borderRadius": "5px",
                    "boxShadow": "0 0 10px #00ffcc",
                    # Font
                    "fontFamily": "monospace",
                    #"flex": "1",
                    "minWidth": "0",  # important pour que flex fonctionne dans un parent flex
                    "textAlign": "center",  # horizontal
                    "display": "flex",
                    "alignItems": "center",          # centre verticalement
                    "justifyContent": "flex-start", # aligne le texte à gauche 
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "padding": "0 10px",  # optionnel pour un peu d’espace intérieur
                },
            ),
        ],
        style = {
            "display": "flex",
            "marginTop": "10px",
            "width": "100%",
            "margin": "0 auto",
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            'gap': '20px',
            #'backgroundColor': 'blue',
        },
    )

def create_tabs():

    tabs_style = {
        "marginTop": "10px",
        "borderRadius": "20px",
        "backgroundColor": "#1a1a1a",
        #"color": "white",
        #"fontFamily": "monospace",
        "border": "1px solid #00ffcc",
        "boxShadow": "0 0 10px #00ffcc",
        "padding": "5px",
        "height": "40px",
        "alignItems": "center",
    }

    tab_style = {
        "lineHeight": "30px",    # centre vertical du texte
        "padding": "0",
        "borderRadius": "15px",
        #"padding": "10px",
        "backgroundColor": "#1a1a1a",
        "color": "white",
        "margin": "2px",
        "border": "1px solid #00ffcc",
        #"height": '20px',
        "alignItems": "center",
    }
    tab_selected_style = tab_style.copy()
    tab_selected_style["backgroundColor"] = "#00b2a2"
    tab_selected_style["color"] = "white"
    tab_selected_style["boxShadow"] = "0 0 20px #00ffcc"

    return dcc.Tabs(
        id        = "tabs",
        value     = "one-quarter",
        style     = tabs_style,
        children  = [
            # This tab shows the top holdings of the portfolio at a given quarter
            dcc.Tab(
                label          = "One quarter",
                value          = "one-quarter",
                style          = tab_style,
                selected_style = tab_selected_style,
            ),
            # This tab shows the top variations between a pair of quarters
            dcc.Tab(
                label          = "Two quarters",
                value          = "two-quarters",
                style          = tab_style,
                selected_style = tab_selected_style,
            ),
            # This tab shows the evolution of the portfolio over time
            dcc.Tab(
                label          = "All quarters",
                value          = "all-quarters",
                style          = tab_style,
                selected_style = tab_selected_style,
            ),
        ],
    )

def generate_default_figure(
    title
):
    fig = go.Figure()
    fig.update_layout(
        title         = title,
        plot_bgcolor  = "black",
        paper_bgcolor = "black",
        font          = dict(
            color  = "white",
            family = "monospace",
        ),
        autosize      = True,
        height        = FIG_HEIGHT,
        width         = FIG_WIDTH,
    )
    return fig

def generate_one_quarter_figure(
    cik,
    quarter,
    merge_key = 'name',
    top_n     = 20,
):
    if (not cik) or (not quarter):
        if not cik:
            title = "Select a CIK"
        elif not quarter:
            title = "Select a quarter"
        return generate_default_figure(
            title = title,
        )

    # Take the data corresponding to that quarter
    input_file = f"output/{cik}/merge/{merge_key}_to_proportion.csv"
    df = pl.read_csv(input_file, columns=[merge_key, quarter])
    # TypeError: the `columns` argument should contain a list of all integers or all string values
    # Sort and top N and convert to Pandas for Plotly
    df = df.filter(
        pl.col(quarter).is_not_null()
    ).sort(
        quarter,
        descending = True,
    ).head(
        top_n
    ).to_pandas()
    # Rename the column
    df.rename(columns={quarter: "proportion"}, inplace=True)

    # Création du barplot cyberpunk
    fig = px.bar(
        data_frame = df,
        x          = 'proportion',
        y          = merge_key,
        orientation = 'h',
    )
    fig.update_layout(
        title={
            "text": f"Top {top_n} Holdings for {quarter}",
            "x": 0.5,
            "y": 0.95,
            "xanchor": "center",
            "yanchor": "top",
            "font": {
                "family": "monospace",
                "size": 20,
                "color": "white",
            },
        },
        font = dict(
            family = 'monospace',
            color = 'white',
            size = 12,
        ),
        autosize      = True,
        height        = FIG_HEIGHT,
        width         = FIG_WIDTH,
        plot_bgcolor  = "black",
        paper_bgcolor = "black",
        xaxis_title   = "Percentage",
        yaxis_title   = "Name",
        margin        = dict(l=40, r=40, t=60, b=40),
    )
    fig.update_traces(
        marker_color  = "#00ffcc",
        textposition  = "outside",
        hovertemplate = "<b>%{y}</b><br>%{x:.2f}%",
    )
    fig.update_yaxes(
        autorange = "reversed",
    )
    return fig

def create_one_quarter(
    cik,
    top_n = 20,
):
    # Take the list of quarters
    quarters = get_cik_quarters(
        cik       = cik,
        ascending = False,
    )
    # Take the most recent quarter if there's any
    quarter = quarters[0] if len(quarters)>0 else None
    # Define the dropdown options
    dropdown_options     = [{"label": q, "value": q} for q in quarters]
    dropdown_value       = quarter
    dropdown_placeholder = "Select quarter" if dropdown_options else "No quarters found"

    # Generate the figure
    fig = generate_one_quarter_figure(
        cik     = cik,
        quarter = quarter,
    )
    return html.Div(
        children = [
            # Dropdown pour les quarters disponibles
            dcc.Dropdown(
                id          = "one-quarter-dropdown",
                options     = dropdown_options,
                value       = dropdown_value,
                placeholder = dropdown_placeholder,
                clearable   = False,
                style = {
                    "width": "200px",
                    "height": "40px",
                    "color": "white",
                    "backgroundColor": "black",
                    "borderRadius": "5px",
                    "boxShadow": "0 0 10px #00ffcc",
                    "fontFamily": "monospace",
                    "flex": "1",
                    "minWidth": "0",  # important pour que flex fonctionne dans un parent flex
                    "position": "relative",
                    "zIndex": 10,
                    "marginBottom": "10px",
                },
                className="cyberpunk-dropdown",
            ),
            # Diagramme à bandes des top quarters
            html.Div(
                dcc.Graph(
                    id     = 'one-quarter-graph',
                    figure = fig,
                    config = {"displayModeBar": False},
                    style  = {
                        "width": "100%",
                        "height": f"{FIG_HEIGHT}px",
                        "backgroundColor": "yellow",
                    },
                ),
                style = {
                    "width": "100%",
                    "display": "flex",
                    "overflow": "hidden",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "borderRadius": "5px",
                },
            ),
        ],
        id = 'one-quarter-div',
        style = {
            'width': '100%',
            'display': 'block',
        },
    )

def generate_two_quarters_figure(
    cik,
    quarter0,
    quarter1,
    merge_key = 'name',
    top_n     = 20,
):
    # Fichier de proportions
    input_file_pr = f"output/{cik}/merge/{merge_key}_to_proportion.csv"

    if quarter0 == quarter1:
        title = f"Both dropdown have the value {quarter0}. Select two different quarters to compare"
        return generate_default_figure(
            title = title,
        )

    df = pl.read_csv(input_file_pr, columns = [merge_key, quarter0, quarter1])
    # Filtrer les lignes où les deux colonnes ne sont pas null
    df = df.drop_nulls(subset=[quarter0, quarter1])
    # Calculer la différence
    df = df.with_columns([
        (pl.col(quarter1) / pl.col(quarter0)).alias("ratio")
    ])
    # Prendre les top N en valeur absolue
    df = df.sort("ratio", descending=True).head(top_n).to_pandas()

    # Créer le barplot horizontal
    fig = px.bar(
        data_frame  = df,
        x           = "ratio",
        y           = merge_key,
        orientation = "h",
        labels      = {
            "ratio": f"Variation {quarter0}→{quarter1}", merge_key: "Name",
        },
    )
    fig.update_layout(
        title = {
            "text": f"Top {top_n} proportion ratios from {quarter0} to {quarter1}",
            "x": 0.5,
            "y": 0.95,
            "xanchor": "center",
            "yanchor": "top",
            "font": {
                "family": "monospace",
                "size": 20,
                "color": "white",
            },
        },
        font = dict(
            family="monospace",
            color="white",
            size = 12,
        ),
        autosize      = True,
        height        = FIG_HEIGHT,
        width         = FIG_WIDTH,
        plot_bgcolor  = "black",
        paper_bgcolor = "black",
        margin        = dict(l=40, r=40, t=60, b=40),
    )
    fig.update_traces(
        marker_color = "#00ffcc",
        textfont     = dict(color="white",
        family       = "monospace"),
    )
    # mettre les plus grandes valeurs en haut
    fig.update_yaxes(
        autorange = "reversed",
    )
    return fig

def create_two_quarters(
    cik,
    top_n = 20,
):
    # Récupère les trimestres disponibles
    quarters = get_cik_quarters(
        cik       = cik,
        ascending = False,
    )
    # Valeurs par défaut : les deux derniers trimestres
    if len(quarters)>=2:
        quarter0 = quarters[1]
        quarter1 = quarters[0]
    else:
        quarter0 = None
        quarter1 = None

    dropdown_options = [{"label": q, "value": q} for q in quarters]
    dropdown_placeholder = "Select quarter" if dropdown_options else "No quarters found"

    fig = generate_two_quarters_figure(
        cik      = cik,
        quarter0 = quarter0,
        quarter1 = quarter1,
        top_n    = top_n,
    )

    return html.Div(
        children=[
            # Div pour les dropdown
            html.Div(
                children = [
                    dcc.Dropdown(
                        id          = "two-quarters-dropdown-0",
                        options     = dropdown_options,
                        value       = quarter0,
                        clearable   = False,
                        placeholder = dropdown_placeholder,
                        style       = {
                            "width": "200px",
                            "height": "40px",
                            "color": "white",
                            "backgroundColor": "black",
                            "borderRadius": "5px",
                            "boxShadow": "0 0 10px #00ffcc",
                            "fontFamily": "monospace",
                            "position": "relative",
                            "zIndex": 10,
                        },
                        className="cyberpunk-dropdown",
                    ),
                    html.Div(
                        children="→",
                        style={
                            "display": "flex",             # active le mode flex
                            "justifyContent": "center",    # centre horizontalement
                            "alignItems": "center",        # centre verticalement
                            "height": "40px",
                            "width": "40px",               # optionnel, pour carré
                            "color": "white",
                            "backgroundColor": "black",
                            "borderRadius": "5px",
                            "fontSize": "24px",            # taille de la flèche
                            "fontWeight": "bold",          # optionnel, rend plus visible
                        },
                    ),
                    dcc.Dropdown(
                        id          = "two-quarters-dropdown-1",
                        options     = dropdown_options,
                        value       = quarter1,
                        clearable   = False,
                        placeholder = dropdown_placeholder,
                        style       = {
                            "width": "200px",
                            "height": "40px",
                            "color": "white",
                            "backgroundColor": "black",
                            "borderRadius": "5px",
                            "boxShadow": "0 0 10px #00ffcc",
                            "fontFamily": "monospace",
                            "position": "relative",
                            "zIndex": 10,
                        },
                        className="cyberpunk-dropdown",
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "10px",
                    "marginBottom": "10px",
                },
            ),
            # Div pour le graphe
            html.Div(
                dcc.Graph(
                    id     = "two-quarters-graph",
                    figure = fig,
                    config = {"displayModeBar": False},
                    style  = {
                        "width": "100%",
                        "height": f"{FIG_HEIGHT}px",
                        "backgroundColor": "yellow",
                    },
                ),
                style={
                    "width": "100%",
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "borderRadius": "5px",
                    "overflow": "hidden",
                },
            ),
        ],
        id = 'two-quarters-div',
        style={
            "width": "100%",
            "display": "none",
        },
    )

def generate_cyber_neon_colors(
    n = 20,
):
    colors = []
    for i in range(n):
        h = i / n             # fraction du cercle (0-1)
        s = 1.0               # saturation à 100%
        l = 0.5               # luminosité à 50%
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        hex_color = '#{:02X}{:02X}{:02X}'.format(int(r*255), int(g*255), int(b*255))
        colors.append(hex_color)
    return colors

def generate_all_quarters_figure(
    cik,
    merge_key ='name',
    top_n     = 10,
    alpha     = 0.5,  # smoothing factor
):
    if not cik:
        title = "Import at least one CIK"
        return generate_default_figure(
            title = title,
        )

    # Lire le CSV
    input_file_pr = f'output/{cik}/merge/{merge_key}_to_proportion.csv'
    try:
        df_pr = pd.read_csv(input_file_pr, index_col=merge_key)
    except:
        title = "Merge file unavailable"
        return generate_default_figure(
            title = title,
        )

    # On s'assure que la taille est ok
    if df_pr.shape[0] == 0 or df_pr.shape[1] == 0:
        title = "No data available"
        return generate_default_figure(
            title = title,
        )

    # Transposer pour avoir les quarters en index
    df_transposed = df_pr.T

    df_transposed.index.name = "Quarter"
    df_transposed.columns.name = merge_key

    # Ordre chronologique (plus ancien en haut, plus récent en bas)
    df_transposed = df_transposed.sort_index()

    if df_transposed.shape[0] == 0 or df_transposed.shape[1] == 0:
        # Si vide, renvoyer une figure vide
        title = "No data available"
        return generate_default_figure(
            title = title,
        )

    # Top N titres basé sur le dernier trimestre
    quarters = df_transposed.index.to_list()
    latest_quarter = quarters[-1]
    top_titles = df_transposed.loc[latest_quarter].nlargest(top_n).index
    df_top = df_transposed[top_titles].copy()

    # Appliquer l'EWM sur chaque titre
    df_ewm = pd.DataFrame(
        index   = df_top.index,
        columns = top_titles,
        dtype   = float,
    )
    for title in top_titles:
        series = df_top[title].dropna()
        if len(series) > 0:
            df_ewm.loc[series.index, title] = series.ewm(alpha=alpha, adjust=False).mean()

    five_cyber_colors = [
        "#00ffcc",  # cyan
        "#ff00ff",  # magenta
        "#39ff14",  # vert fluo
        "#ff8800",  # orange néon
        "#9933ff",  # violet
        "#00ffff",  # turquoise
    ]
    ten_cyber_colors = [
        "#00ffcc",  # cyan
        "#ff00ff",  # magenta
        "#39ff14",  # vert fluo
        "#ff8800",  # orange néon
        "#9933ff",  # violet
        "#f0ff00",  # jaune néon
        "#ff1493",  # rose néon
        "#7fff00",  # vert chartreuse
        "#ff4500",  # rouge-orange
        "#1e90ff",  # bleu électrique
    ]
    if top_n<=5:
        cyber_colors = five_cyber_colors
    elif top_n<=10:
        cyber_colors = ten_cyber_colors
    else:
        cyber_colors = generate_cyber_neon_colors(
            n = top_n,
        )

    # Création de la figure Plotly
    fig = go.Figure()
    x_order = sorted(df_top.index.tolist())
    fig.update_xaxes(
        tickmode="array",
        tickvals=x_order,
        ticktext=x_order,
        tickangle=45
    )
    for i, title in enumerate(top_titles):
        series = df_top[title].dropna()
        if len(series) > 0:
            smoothed = series.ewm(alpha=alpha, adjust=False).mean()
            smoothed = smoothed.reindex(quarters)
            color = cyber_colors[i % len(cyber_colors)]
            # Glow : ligne épaisse semi-transparente
            fig.add_trace(
                go.Scatter(
                    x=smoothed.index,
                    y=smoothed.values,
                    mode='lines',
                    line=dict(color=color, width=12),  # largeur épaisse pour le halo
                    opacity=0.2,                        # translucide
                    hoverinfo='skip',                   # pas de hover sur le glow
                    showlegend=False
                )
            )

            # Ligne principale fine
            fig.add_trace(
                go.Scatter(
                    x=smoothed.index,
                    y=smoothed.values,
                    mode='lines+markers',
                    name=title,
                    line=dict(color=color, width=3),   # ligne principale
                    marker=dict(size=6, color=color),
                    hovertemplate='%{x}<br>%{y:.2f} %<br>',
                )
            )

    fig.update_layout(
        title={
            "text": f"Latest top {top_n} proportions for {cik}",  # titre dynamique
            "y": 0.95,             # position verticale (0=bas, 1=haut)
            "x": 0.5,              # centré horizontalement
            "xanchor": "center",
            "yanchor": "top",
            "font": {"family": "monospace", "size": 20, "color": "white"},
        },
        autosize      = True,
        height        = FIG_HEIGHT,
        width         = FIG_WIDTH,
        xaxis_title   = "Quarter",
        yaxis_title   = "Proportion (%)",
        plot_bgcolor  = "black",
        paper_bgcolor = "black",
        font          = dict(color="white", family="monospace"),
        legend        = dict(font=dict(family="monospace", color="white")),
        margin        = dict(l=40, r=40, t=60, b=40),
    )

    # Supprimer la grille horizontale
    fig.update_yaxes(showgrid=False)

    # Réduire la densité des ticks sur l'axe X si beaucoup de quarters
    if len(df_ewm.index) > 12:
        step = max(1, len(df_ewm.index) // 12)
        fig.update_xaxes(tickmode="array", tickvals=df_ewm.index[::step], tickangle=45)

    return fig

def create_all_quarters(
    cik,
    top_n = 18,
):
    # Génère la figure
    fig = generate_all_quarters_figure(
        cik     = cik,
        top_n   = top_n,
    )

    return html.Div(
        children=[
            # Un espace vertical pour aligner la figure all-quarters avec les autres figures
            html.Div(
                children = [],
                style={
                    "height" : "40px",
                    "marginBottom": "10px",
                },
            ),
            html.Div(
                dcc.Graph(
                    id     = "all-quarters-graph",
                    figure = fig,
                    config = {"displayModeBar": False},
                    style  = {
                        "width": "100%",
                        "height": f"{FIG_HEIGHT}px",
                        "backgroundColor": "yellow",
                    },
                ),
                style={
                    "width": "100%",
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "borderRadius": "5px",  # arrondir les coins
                    "overflow": "hidden",
                },
            ),
        ],
        id = 'all-quarters-div',
        style={
            "width": "100%",
            "display": "none",
        },
    )

def create_figures(
    cik,
):
    return html.Div(
        children = [
            # View 
            create_one_quarter(
                cik = cik,
            ),
            create_two_quarters(
                cik = cik,
            ),
            create_all_quarters(
                cik = cik,
            ),
        ],
        style = {
            "height": "600px",
            "marginTop": "10px",
            "color": "white",
            "backgroundColor": "black",
            "borderRadius": "5px",
            "boxShadow": "0 0 10px #00ffcc",
            "fontFamily": "monospace",
            "flex": "1",
            "minWidth": "0",  # important pour que flex fonctionne dans un parent flex
        },
    )

def create_body(
    cik,
):
    return html.Div(
        children = [
            # Barre pour l'import de fichiers
            create_import_bar(),
            # Tabs pour le choix de la vue
            create_tabs(),
            # Vue des figures
            create_figures(
                cik = cik,
            ),
        ],
        style = {
            'width': '100%',
        },
    )

def get_cik_numbers():
    # Take the list of cik folders
    cik_folders = get_cik_folders()
    # Take the list of cik numbers
    cik_numbers = [cik_folder.split('/')[-1] for cik_folder in cik_folders]
    return cik_numbers

def create_layout():
    # Take the list of cik available
    cik_numbers = get_cik_numbers()
    # By default take the first cik
    cik = cik_numbers[0] if cik_numbers else None

    return html.Div(
        children = [
            html.Div(
                id="glow-box",
                children = [
                    # Header
                    create_header(),
                    # Body
                    create_body(
                        cik = cik,
                    ),
                ],
                style = {
                    "backgroundColor": "rgba(255, 223, 100, 0.2)",
                    "borderRadius": "15px",
                    "border": "1px solid #00ff66",  # vert matrice
                    "boxShadow": "0 0 20px rgba(0, 255, 102, 0.7)",  # halo vert léger
                    "padding": "20px",
                    #"margin": "40px auto",
                    "boxSizing": "border-box",
                    "height": "auto",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "maxWidth": MAX_WIDTH,
                    "margin": "0px auto",
                },
            ),
        ],
        style = {
            "backgroundColor": "#121212",
            "minHeight": "100vh",
            "overflowY": "auto",
            "padding": "20px",
            "display": "block",
            "justifyContent": "center",
        }
    )

################################################################################
################################################################################
# Define the callbacks of the app

def register_callbacks(
    app,
):
    # Un callback pour l'import de fichiers
    @app.callback(
        Output("cik-dropdown", "options"),
        Output("cik-dropdown", "value"),
        Output("cik-dropdown", "placeholder"),
        Input("file-upload-selector", "contents"),
        State("file-upload-selector", "filename"),
        prevent_initial_call=True
    )
    def handle_upload(
        contents,
        filenames,
    ):
        if not contents:
            raise dash.exceptions.PreventUpdate

        # Parse the txt files to raw csv data
        parse_txt_data_to_raw_csv(
            contents_list = contents,
            filename_list = filenames,
        )
        # Convert the raw csv data to clean csv data
        convert_raw_csv_to_clean_csv()
        # Map the variants of nameOfIssuer
        map_nameOfIssuer_variants()
        # Merge the portfolio proportions
        merge_portfolio_proportions()

        # Update the list of CIK after the import
        cik_folders = get_cik_folders()
        dropdown_options = [
            {"label": cik_folder.split("/")[-1], "value": cik_folder.split("/")[-1]}
            for cik_folder in cik_folders
        ]
        dropdown_placeholder = "Select CIK" if dropdown_options else "No CIK found."
        dropdown_value = dropdown_options[0]["value"] if dropdown_options else None

        return (
            dropdown_options,
            dropdown_value,
            dropdown_placeholder,
        )

    # Mise à jour de l'interface par divers dropdown
    @app.callback(
        Output("latest-company-name", "children"),
        Output("one-quarter-dropdown", "options"),
        Output("one-quarter-dropdown", "value"),
        Output("one-quarter-dropdown", "placeholder"),
        Output("one-quarter-graph", "figure"),
        Output("two-quarters-dropdown-0", "options"),
        Output("two-quarters-dropdown-0", "value"),
        Output("two-quarters-dropdown-0", "placeholder"),
        Output("two-quarters-dropdown-1", "options"),
        Output("two-quarters-dropdown-1", "value"),
        Output("two-quarters-dropdown-1", "placeholder"),
        Output("two-quarters-graph", "figure"),
        Output("all-quarters-graph", "figure"),
        Input("cik-dropdown", "options"),
        Input("cik-dropdown", "value"),
        Input("one-quarter-dropdown", "value"),
        Input("two-quarters-dropdown-0", "value"),
        Input("two-quarters-dropdown-1", "value"),
        prevent_initial_call=True
    )
    def update_latest_company_name(
        cik_dropdown_options,
        cik_dropdown_value,
        one_quarter_dropdown_value,
        two_quarters_dropdown_0_value,
        two_quarters_dropdown_1_value,
    ):
        ctx = callback_context
        trigger_type = ctx.triggered[0]["prop_id"]

        company_conformed_name              = no_update
        one_quarter_dropdown_options        = no_update
        one_quarter_dropdown_placeholder    = no_update
        one_quarter_graph_figure            = no_update
        two_quarters_dropdown_0_options     = no_update
        two_quarters_dropdown_0_placeholder = no_update
        two_quarters_dropdown_1_options     = no_update
        two_quarters_dropdown_1_placeholder = no_update
        two_quarters_graph_figure           = no_update
        all_quarters_graph_figure           = no_update

        if trigger_type in ['cik-dropdown.value', 'cik-dropdown.options']:

            # Update the conformed name of the company
            company_conformed_name = cik_to_company_conformed_name(
                cik = cik_dropdown_value,
            )
            # Update the one quarter dropdown
            quarters = get_cik_quarters(
                cik       = cik_dropdown_value,
                ascending = False,
            )
            dropdown_options = [{"label": q, "value": q} for q in quarters]
            dropdown_placeholder = "Select quarter" if dropdown_options else "No quarters found"
            one_quarter_dropdown_options     = dropdown_options
            one_quarter_dropdown_value       = quarters[0] if quarters else None
            one_quarter_dropdown_placeholder = dropdown_placeholder
            # Update the one quarter figure
            one_quarter_graph_figure = generate_one_quarter_figure(
                cik     = cik_dropdown_value,
                quarter = one_quarter_dropdown_value,
            )
            # Update the two quarters dropdown
            if len(quarters)>=2:
                quarter0 = quarters[1]
                quarter1 = quarters[0]
            else:
                quarter0 = None
                quarter1 = None
            dropdown_options = [{"label": q, "value": q} for q in quarters]
            dropdown_placeholder = "Select quarter" if dropdown_options else "No quarters found"
            two_quarters_dropdown_0_options     = dropdown_options
            two_quarters_dropdown_0_value       = quarter0
            two_quarters_dropdown_0_placeholder = dropdown_placeholder
            two_quarters_dropdown_1_options     = dropdown_options
            two_quarters_dropdown_1_value       = quarter1
            two_quarters_dropdown_1_placeholder = dropdown_placeholder
            # Update the two quarters figure
            two_quarters_graph_figure = generate_two_quarters_figure(
                cik      = cik_dropdown_value,
                quarter0 = two_quarters_dropdown_0_value,
                quarter1 = two_quarters_dropdown_1_value,
            )
            # Update the all quarters figure
            all_quarters_graph_figure = generate_all_quarters_figure(
                cik      = cik_dropdown_value,
            )

        elif trigger_type=='one-quarter-dropdown.value':

            # Update the one quarter figure
            one_quarter_graph_figure = generate_one_quarter_figure(
                cik     = cik_dropdown_value,
                quarter = one_quarter_dropdown_value,
            )

        elif trigger_type=='two-quarters-dropdown-0.value':

            # Update the two quarters figure
            two_quarters_graph_figure = generate_two_quarters_figure(
                cik      = cik_dropdown_value,
                quarter0 = two_quarters_dropdown_0_value,
                quarter1 = two_quarters_dropdown_1_value,
            )

        elif trigger_type=='two-quarters-dropdown-1.value':

            # Update the all quarters figure
            two_quarters_graph_figure = generate_two_quarters_figure(
                cik      = cik_dropdown_value,
                quarter0 = two_quarters_dropdown_0_value,
                quarter1 = two_quarters_dropdown_1_value,
                top_n    = 20,
            )

        # On rend le résultat
        return (
            company_conformed_name,
            one_quarter_dropdown_options,
            one_quarter_dropdown_value,
            one_quarter_dropdown_placeholder,
            one_quarter_graph_figure,
            two_quarters_dropdown_0_options,
            two_quarters_dropdown_0_value,
            two_quarters_dropdown_0_placeholder,
            two_quarters_dropdown_1_options,
            two_quarters_dropdown_1_value,
            two_quarters_dropdown_1_placeholder,
            two_quarters_graph_figure,
            all_quarters_graph_figure,
        )

    # Callback pour le changement de tab
    @app.callback(
        Output("one-quarter-div", "style"),
        Output("two-quarters-div", "style"),
        Output("all-quarters-div", "style"),
        Input("tabs", "value"),
        State("one-quarter-div", "style"),
        State("two-quarters-div", "style"),
        State("all-quarters-div", "style"),
        prevent_initial_call=True
    )
    def change_tab(
        tabs_value,
        one_quarter_div_style,
        two_quarters_div_style,
        all_quarters_div_style,
    ):
        if tabs_value=='one-quarter':
            one_quarter_div_style['display']  = 'block'
            two_quarters_div_style['display'] = 'none'
            all_quarters_div_style['display'] = 'none'
        elif tabs_value=='two-quarters':
            one_quarter_div_style['display']  = 'none'
            two_quarters_div_style['display'] = 'block'
            all_quarters_div_style['display'] = 'none'
        elif tabs_value=='all-quarters':
            one_quarter_div_style['display']  = 'none'
            two_quarters_div_style['display'] = 'none'
            all_quarters_div_style['display'] = 'block'
        return (
            one_quarter_div_style,
            two_quarters_div_style,
            all_quarters_div_style,
        )

################################################################################
################################################################################
# Create the app

def create_dash_app(
    url = None,
):

    # Absolute path to the assets folder inside the package
    assets_path = os.path.join(os.path.dirname(__file__), "assets")

    # Instantiate a Dash app
    app = Dash(
        __name__,
        title                = "DIFF13F",
        assets_folder        = assets_path,
        external_stylesheets = [
            dbc.themes.BOOTSTRAP,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css",
            'https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap',
        ]
    )

    # Create the layout
    app.layout = create_layout()

    # Register the callbacks
    register_callbacks(
        app = app,
    )

    # Return the app
    return app

################################################################################
################################################################################
# Execute the app

def main(
    turn_off_logs = True,
    open_browser  = True,
    debug         = False,
    use_reloader  = False,
):
    """
    Entry point of the app.
    """

    # Reduce the verbosity of Flask / Dash
    if turn_off_logs:
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    # Create the Dash App
    app = create_dash_app()

    # Open a browser
    if open_browser:
        webbrowser.open("http://127.0.0.1:8050")

    # Run the app
    app.run(
        debug        = debug,
        use_reloader = use_reloader,
        port         = 8050,
    )

if __name__ == "__main__":

    main(
        turn_off_logs = False, # Need logs for dev
        open_browser  = False, # No need to open a browser for dev
        debug         = True,  # Debug for dev
        use_reloader  = True,  # Reload for dev
    )

