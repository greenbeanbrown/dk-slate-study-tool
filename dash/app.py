import base64
import datetime
import io

import os
import glob

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import dash_bootstrap_components as dbc

import base64

import pandas as pd

import sys

sys.path.insert(0, '..')
from functions import cleanup_mlb_lineup_data, cleanup_mma_lineup_data, prep_raw_dk_contest_data, filter_dk_users, merge_team_logos, get_team_colors, parse_contents, generate_table, store_uploaded_data, convert_df_to_html

mlb_team_colors = {'ARI':'red','ATL':'blue','BAL':'orange','BOS':'red','CHC':'blue','CHW':'black','CIN':'red','CLE':'blue','COL':'purple','DET':'blue','HOU':'orange','KCR':'blue','LAA':'red','LAD':'blue','MIA':'orange','MIL':'blue','MIN':'blue','NYM':'orange','NYY':'blue','OAK':'green','PHI':'red','PIT':'yellow','SDP':'yellow','SFG':'orange','SEA':'black','STL':'red','TBR':'blue','TEX':'red','TOR':'blue','WAS':'red'}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    # Tabs
    html.Div([
            dcc.Tabs(id='tabs-example', value='tab-1', children=[
            dcc.Tab(label='Aggregate Exposures', value='tab-1', children=[html.Div(id='tabs-1-content')]),
            dcc.Tab(label='Individual Lineups', value='tab-2', children=[html.Div(id='tabs-2-content')]),
        ])
    
    ]),
    
    # This component 'stores' the uploaded file data into the session memory so it can be passed through various callbacks
    dcc.Store(id='output-data-upload')

])

@app.callback(Output('output-data-upload', 'data'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def store_data(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            #parse_contents(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
            store_uploaded_data(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
            ]
        # Serialize the df output as JSON to store it in session
        #json_children = children[0].to_json(date_format='iso', orient='split')
        json_children = children[0].to_json(date_format='iso', orient='columns')

        return json_children
    else:
        pass

@app.callback(Output('tabs-1-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'))
def render_content(tab, data):
    if data is None:
        pass
    
    else:
        return html.Div([
            html.H3('Aggregate DK User Exposures for current contest'),
            convert_df_to_html(data)
        ])

@app.callback(Output('tabs-2-content', 'children'),
              Input('tabs-example', 'value'))
def render_content(tab):
        return html.Div([
            html.H3('Individual Lineup Analyzer for current contest')
        ])

if __name__ == '__main__':
    app.run_server(debug=True)