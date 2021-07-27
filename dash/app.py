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
from functions import cleanup_mlb_lineup_data, cleanup_mma_lineup_data, prep_raw_dk_contest_data, filter_dk_users, merge_team_logos, get_team_colors

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


mlb_team_colors = {'ARI':'red','ATL':'blue','BAL':'orange','BOS':'red','CHC':'blue','CHW':'black','CIN':'red','CLE':'blue','COL':'purple','DET':'blue','HOU':'orange','KCR':'blue','LAA':'red','LAD':'blue','MIA':'orange','MIL':'blue','MIN':'blue','NYM':'orange','NYY':'blue','OAK':'green','PHI':'red','PIT':'yellow','SDP':'yellow','SFG':'orange','SEA':'black','STL':'red','TBR':'blue','TEX':'red','TOR':'blue','WAS':'red'}

#image_directory = '/Users/Sean/Documents/python/dk_slate_study_tool/data/mlb_logos/arizona_diamondbacks.jpeg'
#image_filename = '/Users/Sean/Documents/python/dk_slate_study_tool/data/mlb_logos/arizona_diamondbacks.jpeg'
#encoded_image = base64.b64encode(open(image_filename, 'rb').read())

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

ALLOWED_TYPES = (
    "text", "number"
)

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
    html.Div(id='output-data-upload'),
    # Adding function to process data
    html.Div(children=[
        html.H4(children='DK Slate Study Lineups')
        #generate_table(df)
    ]),
    html.Img(src=app.get_asset_url('mlb_logos/arizona_diamondbacks.jpeg'))

])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # Prep data prior to returning output 
    #df = 

    return html.Div([
        html.H5(filename),
        #html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data = filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0]).to_dict('records'),
            #data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0]).columns],

            sort_action="native",
            filter_action='native',
            #sort_mode="multi"
            style_data_conditional = (
                get_team_colors()
            )
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
    else:
        pass


if __name__ == '__main__':
    app.run_server(debug=True)