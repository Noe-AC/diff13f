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

Steps to improve the app:
    python -m diff13f.app
(code what you have to code)
"""

################################################################################
################################################################################
# Import libraries

import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import webbrowser
import os

TEXTBOX_HEIGHT = "220px"
SPINNER_TYPE = "dot"
MAX_WIDTH = "1000px"

################################################################################
################################################################################
# Utility functions



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

def create_more_to_come():
    return html.Div(
        children=[
            html.H2(
                "Stay tuned...",
                style={
                    "fontSize": "16px",
                    "margin": 0,
                    "lineHeight": "40px",
                    "fontWeight": "600",
                    "textShadow": "0 0 10px #00ff66, 0 0 1px #00ff66, 0 0 1px #00ff66",  # halo vert léger
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
        },
    )

def create_layout():
    return html.Div(
        children = [
            html.Div(
                children = [
                    create_header(),
                    create_more_to_come(),
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
    ...

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

