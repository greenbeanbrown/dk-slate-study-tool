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

import plotly.express as px
import plotly.graph_objs as go

sys.path.insert(0, '..')
from functions import cleanup_mlb_lineup_data, cleanup_mma_lineup_data, prep_raw_dk_contest_data, filter_dk_users, merge_team_logos,  parse_uploaded_data, convert_df_to_html, parse_mlb_lineup, create_points_own_df, calculate_mlb_stacks, convert_stacks_to_html, summarize_lineup_stacks, clean_entry_name, discrete_background_color_bins

mlb_team_colors = {'ARI':'red','ATL':'blue','BAL':'orange','BOS':'red','CHC':'blue','CHW':'black','CIN':'red','CLE':'blue','COL':'purple','DET':'blue','HOU':'orange','KCR':'blue','LAA':'red','LAD':'blue','MIA':'orange','MIL':'blue','MIN':'blue','NYM':'orange','NYY':'blue','OAK':'green','PHI':'red','PIT':'yellow','SDP':'yellow','SFG':'orange','SEA':'black','STL':'red','TBR':'blue','TEX':'red','TOR':'blue','WAS':'red'}

# Define some global variables/data
PLAYER_TEAM_POS_DF = pd.read_csv('assets/mlb_players_pos_teams_data.csv') 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select DraftKings Contest CSV')
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
            dcc.Tabs(id='tabs-example', value='summary-tab', children=[
                dcc.Tab(label='Contest Summary', value='summary-tab', children=[
                                                                                html.Div([
                                                                                    html.Div(id='summary-tab-content', style={'display': 'inline-block'}),
                                                                                    dcc.Graph(id='stacks-pie-chart', style={'display': 'inline-block'})
                                                                                    ])
                                                                                ]),

                dcc.Tab(label='Aggregate Exposures', value='agg-exposures-tab', children=[dcc.Dropdown(id='agg-lineup-user-dropdown', style={'textAlign':'left', 'width':'100%','display':'inline-block'}, multi=True), 
                                                                          html.Div(id='agg-exposures-tab-content')]),
                dcc.Tab(label='Individual Lineups', value='ind-lineups-tab', children=[dcc.Dropdown(id='ind-lineup-user-dropdown'), 
                                                                          html.Div(id='ind-lineup-tab-content')]),
                dcc.Tab(label='Stacks Calculator', value='stack-calc-tab', children=[dcc.Dropdown(id='stacks-calc-user-dropdown', multi=True),
                                                                          html.Div(id='stacks-calc-tab-content')])                                                                          
        ])
    
    ]),
    
    # This component 'stores' the uploaded file data into the session memory so it can be passed through various callbacks
    dcc.Store(id='output-data-upload'),

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

# This is the dropdown menu on the aggregate exposures tab
@app.callback(Output('agg-lineup-user-dropdown', 'options'),
              Input('output-data-upload','data'))
def update_tab1_dropdown(data):
    # If there is no data uploaded
    if data is None:
        raise PreventUpdate
    # If there is data
    else:
        # Convert serialized JSON stirng into dataframe
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Clean up the raw data a bit
        df = cleanup_mlb_lineup_data(df)

        # Get every value from data.raw_entry_name into a list for the dropdown
        # We can just grab EntryName here because this data has not been cleaned yet - it's the raw upload data
        dk_users = pd.Series(df['EntryName'].dropna()).drop_duplicates()

        return [
                { 
                    'label': user,
                    'value' : user
                } for user in dk_users
                ]

# This is the dropdown menu for DK users on the individual tab
@app.callback(Output('ind-lineup-user-dropdown', 'options'),
              Input('output-data-upload','data'))
def update_individual_lineup_dropdown(data):
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
        dk_users = pd.Series(df['EntryName'].dropna()).drop_duplicates()

        return [
                { 
                    'label': user,
                    'value' : user
                } for user in dk_users
                ]

# This is the dropdown menu for DK users on the individual tab
@app.callback(Output('stacks-calc-user-dropdown', 'options'),
              Input('output-data-upload','data'))
def update_stacks_calc_dropdown(data):
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
        #dk_users = df['EntryName'].dropna()

        dk_users = pd.Series([clean_entry_name(entry_name) for entry_name in df['EntryName'].dropna()]).drop_duplicates()

        return [
                { 
                    'label': user,
                    'value' : user
                } for user in dk_users
                ]


@app.callback([Output('summary-tab-content', 'children'),
              Output('stacks-pie-chart', 'figure')],
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'))
def contest_summary_content(tab, data):
    # Check if there is no data, if there isn't, then don't do anything
    if (data is None):
        raise PreventUpdate
    
    else:
        # Read data and convert 
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Create the points ownership df to pass through parse_mlb_lineup()
        # NOTE: this should really be moved outside of the callback functions, only needs to be loaded 1 time
        points_ownership_df = create_points_own_df(df)

        # Goal of this is to show descriptive summary info of the contest, a "snapshot" if you will

        # First thing to present is the distribution of stack-types present in the contest (e.g. How many 5-2-1 stacks were there? 5-3? so on..)
        df = summarize_lineup_stacks(df, points_ownership_df, PLAYER_TEAM_POS_DF)
        # Get the frequency count of each stack type
        stack_frequency_df = pd.DataFrame({'Stack Type': df['Stack Type'].value_counts().index,
                                           'Count': df['Stack Type'].value_counts()})

        # Second thing to do is plot this as a pie chart 
        fig = px.pie(stack_frequency_df, values='Count', names='Stack Type', title='Stack Frequencies')

        # Third thing to do is present the distribution of team stacks
        
        return [
            # DataTable output
            html.Div([
            html.H3('Display Stack Distributions and such here'),
            convert_df_to_html(stack_frequency_df, style=None, page_size=10)]),

            # Pie Chart output
            fig]





@app.callback(Output('agg-exposures-tab-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'),
              Input('agg-lineup-user-dropdown','value'))
def aggregate_exposures_tab_content(tab, data, agg_exposures_dropdown_selection):
    # Check if there is no data, if there isn't, then don't do anything
    if (data is None):
        pass
    
    # If there is data then start processing the relevant tab data
    else:

        # Prep the dataframe before calling our processing function 
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')        

        #import ipdb; ipdb.set_trace()

        # Show the aggregate data if there are no users selected in the dropdown 
        if (agg_exposures_dropdown_selection is None):
            df = prep_raw_dk_contest_data(df, 'MLB')[0][['player','nickname','position','points','ownership']]
        # If there are users in the dropdown selection, then filter based on those users
        else:
            #dk_users = ['Awesemo', 'giantsquid', 'bkreider', 'dacoltz', 'getloose', 'totoroll33', 'BigT44', 'thepickler']
            dk_users = agg_exposures_dropdown_selection

            # Apply Aggregate Exposures processing 
            df = filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0], dk_users)

            # Conditional Formatting for players exposures
            #(styles, legend) = discrete_background_color_bins(df)

        return html.Div([
            html.H3('Aggregate DK User Exposures for current contest'),
            convert_df_to_html(df, style='conditional')
        ])

@app.callback(Output('ind-lineup-tab-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'),
              Input('ind-lineup-user-dropdown','value'))
def individual_lineups_tab_content(tab, data, dropdown_selection):

    # This gives us the current value of the DK User dropdown, because we used the 'value' property as the input
    dk_user = dropdown_selection

    # Check for data upload
    if (data is None) or (dropdown_selection is None):
        pass

    else:
        # Processing for Individual Lineup Analyzer
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Create the points ownership df to pass through parse_mlb_lineup()
        points_ownership_df = create_points_own_df(df)

        # Clean up the raw output a little bit
        df = cleanup_mlb_lineup_data(df)

        # Filter the individual lineup down based on dropdown menu user input
        df = parse_mlb_lineup(df, points_ownership_df, PLAYER_TEAM_POS_DF, dk_user)

        # Get stack data
        stacks_df = calculate_mlb_stacks(df)
        
        return html.Div([
            html.H3('Individual Lineup Analyzer'),
            # Convert the processed data into an HTML table for output
            convert_df_to_html(df),
            html.Div(children=convert_stacks_to_html(app, stacks_df))
        ])

@app.callback(Output('stacks-calc-tab-content', 'children'),
              Input('tabs-example', 'value'),
              Input('output-data-upload','data'),
              Input('stacks-calc-user-dropdown','value'))
def stack_calculator_tab_content(tab, data, dropdown_selection):

    # Check for data upload
    if (data is None):
        pass
    # If data is uploaded
    else:
        data = json.loads(data)
        df = pd.DataFrame.from_dict(data, orient='columns')

        # Create the points ownership df to pass through parse_mlb_lineup()
        points_ownership_df = create_points_own_df(df)
        
        # If the dropdown is empty, then show all entries stack info
        if dropdown_selection is None:
            # Process data 
            df = summarize_lineup_stacks(df, points_ownership_df, PLAYER_TEAM_POS_DF)
        else:
            df = summarize_lineup_stacks(df, points_ownership_df, PLAYER_TEAM_POS_DF, dropdown_selection)

        return html.Div([
            html.H3('Stack Calculator'),
            convert_df_to_html(df)
        ])


if __name__ == '__main__':
    app.run_server(debug=True)