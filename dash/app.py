import base64
import datetime
import io

import os
import glob

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

import dash_table


import dash_bootstrap_components as dbc

import base64
import json

import pandas as pd

import sys

sys.path.insert(0, '..')
from functions import cleanup_mlb_lineup_data, cleanup_mma_lineup_data, prep_raw_dk_contest_data, filter_dk_users, merge_team_logos, get_team_colors,  parse_uploaded_data, convert_df_to_html, parse_mlb_lineup

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
            dcc.Tab(label='Individual Lineups', value='tab-2', children=[dcc.Dropdown(id='dk-user-dropdown'), html.Div(id='tabs-2-content')]),
        ])
    
    ]),
    
    # This component 'stores' the uploaded file data into the session memory so it can be passed through various callbacks
    dcc.Store(id='output-data-upload')

])

@app.callback(Output('output-data-upload', 'data'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def store_raw_data(list_of_contents, list_of_names, list_of_dates):
    # Only process if a file has been uploaded
    if list_of_contents is not None:
        # The file is uploaded and passed through as a string of contents that need to be unpacked here
        children = [parse_uploaded_data(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)]
        # Serialize the df output as JSON to store it in session - these dash apps require JSON serialization for stored objects
        json_children = children[0].to_json(date_format='iso', orient='columns')

        return json_children
    else:
        pass


@app.callback(Output('dk-user-dropdown', 'options'),
              Input('output-data-upload','data'))
def update_tab2_dropdown(data):
    # If there is no data uploaded
    if data is None:
        raise PreventUpdate
    # If there is data
    else:
        # Convert serialized JSON stirng into dataframe
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Get every value from data.raw_entry_name into a list for the dropdown
        # We can just grab EntryName here because this data has not been cleaned yet - it's the raw upload data
        dk_users = df['EntryName']

        return [
                { 
                    'label': user,
                    'value' : user
                } for user in dk_users
                ]

@app.callback(Output('tabs-1-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'))
def aggregate_exposures_tab_content(tab, data):
    # Check if there is no data, if there isn't, then don't do anything
    if data is None:
        pass
    
    # If there is data then start processing the relevant tab data
    else:
        # Prep the dataframe before calling our processing function 
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Apply Aggregate Exposures processing 
        df = filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0])

        return html.Div([
            html.H3('Aggregate DK User Exposures for current contest'),
            convert_df_to_html(df)
        ])

@app.callback(Output('tabs-2-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'),
              Input('dk-user-dropdown','value'))
def inidividual_lineups_tab_content(tab, data, dropdown_selection):

    # This gives us the current value of the DK User dropdown, because we used the 'value' property as the input
    dk_user = dropdown_selection

    # Check for data upload
    if data is None:
        pass

    else:
        # Processing for Individual Lineup Analyzer
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        df = cleanup_mlb_lineup_data(df)
        #df = parse_mlb_lineup(df, 'youdacao (3/3)')
        df = parse_mlb_lineup(df, dk_user)

        return html.Div([
            html.H3('Individual Lineup Analyzer for current contest'),
            # Convert the processed data into an HTML table for output
            convert_df_to_html(df)
        ])

if __name__ == '__main__':
    app.run_server(debug=True)