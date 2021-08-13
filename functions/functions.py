import pandas as pd
import numpy as np

import time 

import Levenshtein
from Levenshtein import distance as levenshtein_distance 

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table

import plotly.express as px
import plotly.graph_objs as go

import base64
import os
import io

import json

import colorlover



# Clean EntryName to remove entry numbers if necessary
def clean_entry_name(entry_name):
    # Find (), index, and remove
    index = entry_name.find('(')
    # If only 1 entry then just take the clean entry name
    if index == -1:
        clean_name = entry_name.strip()
    else:
        clean_name = entry_name[:index].strip()
    return(clean_name)

def create_points_own_df(raw_dk_contest_data):

    # Create the 1st dataset
    points_own_df = pd.DataFrame()

    # Add the main datapoints
    points_own_df['player'] = raw_dk_contest_data.Player.dropna()
    points_own_df['position'] = raw_dk_contest_data['Roster Position'].dropna() 
    # Need to clean this up a bit, the percentages are coming in as strings from the file so we convert to a float
    # Strip the percentage sign from the last char and then cast
    points_own_df['ownership'] = [float(ownership[:-1]) for ownership in  raw_dk_contest_data['%Drafted'].dropna()]
    points_own_df['points'] = raw_dk_contest_data['FPTS'].dropna()

    return(points_own_df)


def melt_crosstab(agg_lineups_df, user):
    # Get exposure numbers
    
    # Get all lineups in a single dataframe for a specific user
    focus_lineups = agg_lineups_df[agg_lineups_df['EntryName'] == user]

    # Melt dataframe
    melted_lineup = focus_lineups.melt(var_name='columns', value_name='player')
    melted_lineup = melted_lineup[melted_lineup['columns'] != 'EntryName']
    
    # Crosstab dataframe
    crosstab_lineup = pd.crosstab(index=melted_lineup['player'], columns=melted_lineup['columns'])
    crosstab_lineup.reset_index(inplace=True)
    
    
    # Create column with total count across positions
    crosstab_lineup['count'] = crosstab_lineup.sum(axis=1)
    
    # Create percentage column
    total_lineups = len(focus_lineups)
    crosstab_lineup['exposure'] = crosstab_lineup['count'] / total_lineups * 100
    
    # Sorting
    crosstab_lineup = crosstab_lineup.sort_values('count', ascending=False)    
    
    return(crosstab_lineup)

# This function will take in a list of provided DK usernames and a df with aggregate lineup data (which is the output of cleanup_mlb_lineup_data()
# The return is a filtered dataframe containing only the data of those users exposures and related info
def filter_dk_users(agg_lineups_df, points_ownership_df, dk_users):
#def filter_dk_users(agg_lineups_df, dk_users_list):

    # Make this a dynamic input !!!
    #dk_users = ['Awesemo', 'giantsquid', 'bkreider', 'dacoltz', 'getloose', 'totoroll33', 'BigT44', 'thepickler']

    # Loop through each user and create a dictionary with their data
    user_data_dict = {}

    for user in dk_users:
        # Use this for MMA
        #user_data_dict[user]['F'] = user_data_dict[user][['F1','F2','F3','F4','F5','F6']].sum(axis=1)
        try:
            user_exposures = melt_crosstab(agg_lineups_df, user)[['player','count','exposure']]
            user_data_dict[user] = user_exposures
        except:
            print('Error with ', user)
            # Remove that user from the list to prevent more errors
            #dk_users.remove(user)

    # Aggregate the various dataframes into a single one
    agg_exposures = pd.DataFrame()
    
    #for user in dk_users:
    for user in list(user_data_dict.keys()):
        if user == list(user_data_dict.keys())[0]:
            agg_exposures = user_data_dict[user][['player','exposure']].round(2)
            agg_exposures.rename(columns={'exposure':user}, inplace=True)
        else:
            agg_exposures = pd.merge(agg_exposures, user_data_dict[user][['player','exposure']].round(2), how='outer', on='player')
            agg_exposures.rename(columns={'exposure':user}, inplace=True)

        agg_exposures = agg_exposures.replace(np.nan, 0.0)    
    # Now merge the 2 datasets that we've created together into 1
    master_df = pd.merge(agg_exposures, points_ownership_df, on='player')
    non_user_cols = ['player','Team', 'nickname','position','points', 'ownership']
    
    master_df = master_df[[*non_user_cols, *list(user_data_dict.keys())]]
    
    master_df = master_df.sort_values('points', ascending=False)

    return(master_df)

# SCRAPING FUNCTION
# This function parses rotogrinders website for Player Names, Teams, and Positions for MLB data
# Input is a url that has a GET result for the rotogrinders url
# example url = 'https://rotogrinders.com/game-stats/mlb-pitcher?site=draftkings&range=season'
def parse_mlb_stat_data(url):
    # Initialize driver object
    driver = webdriver.Firefox()   # Establish the driver, we are using FireFox in this case
    driver.get(url) 

    # Find the ALL button, to show all results 
    page_buttons = driver.find_elements_by_class_name("page")
    all_button = page_buttons[len(page_buttons)-1]
    # Click the button
    driver.execute_script("arguments[0].click();", all_button)
    # Find the table we want
    table = driver.find_element_by_id('game-stats-table') 
    # Get the stats table
    table = driver.find_element_by_id('game-stats-table') 
    
    df = pd.DataFrame()
    
    # Loop through each column
    for col in table.find_elements_by_class_name('rgt-col'):
        # Get the column header for each column and append
        for header in col.find_elements_by_class_name('rgt-hdr'):
            # Grabbing all players names into a list 
            div_tags = col.find_elements_by_tag_name('div')
            column_data = [tag.text for tag in div_tags]
            
            df[column_data[0]] = column_data[1:]
        
    return(df)


# Create a function that takes two lists of strings for matching
def match_name(name, list_names, min_score=0.80):

    # -1 score incase we don't get any matches
    max_score = -1
    # Returning empty name for no match as well
    max_name = ""
    # Iterating over all names in the second list
    for name2 in list_names:
        #Finding fuzzy match score
        score = Levenshtein.ratio(name, name2)
           
        # Checking if we are above our threshold and have a better score
        if (score > min_score) & (score > max_score):
            max_name = name2
            max_score = score
           
    return(max_name, max_score)    

# NOT SURE WHAT THE POINT OF THIS FUNCTION IS 
# FLAG
def handle_outlier_names(df):

    # Loop through every row with an empty team field
    for row in df['Team']:
        pass

    return(df)


# This takes in a file upload from the UI and returns a dataframe version
def parse_uploaded_data(contents, filename, date):
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

    return(df)   

def discrete_background_color_bins(df, n_bins=10, columns='all'):

    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]

    # Add formatting to all numeric columns - not really using this
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    
    # Only apply the conditional formatting to the player exposures 
    elif columns == 'exposures':
        # Define what columns we want to add the conditional formatting to
        df_numeric_columns = df[df.columns.difference(['player','points','nickname','ownership'])]

    # Otherwise, still apply to all columns - again, not really using this
    else:
        df_numeric_columns = df[columns]

    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()

    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]

    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        #backgroundColor = colorlover.scales[str(n_bins)]['seq']['Blues'][i - 1]
        # This defines what color palette/gradient to use
        backgroundColor = colorlover.scales[str(n_bins)]['div']['RdYlGn'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        #import ipdb; ipdb.set_trace()

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))