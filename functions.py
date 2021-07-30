import pandas as pd
import numpy as np

import time 

import Levenshtein
from Levenshtein import distance as levenshtein_distance 

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table

import base64
import os
import io

import json

def prep_raw_dk_contest_data(raw_dk_contest_data, sport):

    # Take in 1 raw dataframe as an input
    working_df = raw_dk_contest_data.copy()

    # Return a list of 2 dataframes: 1) points ownership df 2) exposures by entry name
    # 1st create points ownership df
    points_ownership_df = create_points_own_df(raw_dk_contest_data)

    # Now, create the ownership exposures
    if sport == 'MLB':
        exposures_df = cleanup_mlb_lineup_data(raw_dk_contest_data)
    elif sport == 'MMA':
        exposures_df = cleanup_mma_lineup_data(raw_dk_contest_data)
    else:
        raise ValueError('incorrect sport type entered as input')

    # Merge player team and position data for reference (should always be in same dir)
    #player_team_pos_df = pd.read_csv('C:/Users/Sean/Documents/python/dk_slate_study_tool/data/mlb_players_pos_teams_data.csv') 
    player_team_pos_df = pd.read_csv('assets/mlb_players_pos_teams_data.csv') 



    # Fuzzy match the player names to the lookup df with every player
    player_team_pos_df['player'] = [match_name(player_name, points_ownership_df['player'])[0] for player_name in player_team_pos_df['Player']]
    player_team_pos_df = handle_outlier_names(player_team_pos_df)
    player_team_pos_df.drop('Player', axis=1, inplace=True)

    points_ownership_df = pd.merge(points_ownership_df, player_team_pos_df, how='left', on='player')
    # Add file paths to team logos for use in dash app
    points_ownership_df = merge_team_logos(points_ownership_df)

    # Return a list of dataframes, use index to get them [0,1]
    list_of_clean_dfs = [points_ownership_df, exposures_df]

    return(list_of_clean_dfs)

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

# This function takes in a dataframe of the raw DK MMA contest results and cleans it up a bit for our purposes
def cleanup_mma_lineup_data(raw_lineup_data):

    # Create an empty df that will hold the final output
    clean_lineup_data = raw_lineup_data.copy()

    # Clean the username field - it comes out with extra chars 
    clean_lineup_data['EntryName'] = clean_lineup_data['EntryName'].apply(lambda row: clean_entry_name(row))

    # Split up all the Fighter names and get rid of extra space - this is MUCH better than the original idea
    list_of_all_lineups = [[player_name.strip() for player_name in lineup[1:].split('F ')] for lineup in raw_lineup_data.Lineup]
    # Assign all of the list values to the df
    clean_lineup_data['F1'] = [lineup[0] for lineup in list_of_all_lineups]
    clean_lineup_data['F2'] = [lineup[1] for lineup in list_of_all_lineups]
    clean_lineup_data['F3'] = [lineup[2] for lineup in list_of_all_lineups]
    clean_lineup_data['F4'] = [lineup[3] for lineup in list_of_all_lineups]
    clean_lineup_data['F5'] = [lineup[4] for lineup in list_of_all_lineups]
    clean_lineup_data['F6'] = [lineup[5] for lineup in list_of_all_lineups]
    # Drop that dirty Lineup column now that its unnecessary
    clean_lineup_data.drop('Lineup', axis=1, inplace=True)

    return(clean_lineup_data)

# This function takes in a dataframe of the raw DK contest results and cleans it up a bit for our purposes
def cleanup_mlb_lineup_data(raw_lineup_data):

    # Create an empty df that will hold the final output
    clean_lineup_data = raw_lineup_data.copy()

    # First thing to do is drop the nans from the Lineup field - these are empty lineups that people submitted and should not be included in this analysis
    clean_lineup_data = clean_lineup_data[['Rank','EntryId','EntryName','Points','Lineup']]
    clean_lineup_data = clean_lineup_data.dropna()

    # Clean the username field - it comes out with extra chars 
    clean_lineup_data['raw_entry_name'] = clean_lineup_data['EntryName']
    clean_lineup_data['EntryName'] = clean_lineup_data['EntryName'].apply(lambda row: clean_entry_name(row))

    # Replace all position substrings with ##, which we can use to split the lineups easily with - then we will add the positions back after
    list_of_all_lineups = [lineup.replace('P ', '#').replace('C ', '#').replace('1B ','#').replace('2B','#').replace('3B','#').replace('SS', '#').replace('OF','#') for lineup in clean_lineup_data.Lineup]

    # Split up all the Fighter names and get rid of extra space - this is MUCH better than the original idea
    #list_of_all_lineups = [[player_name.strip() for player_name in lineup[1:].split('#')] for lineup in raw_lineup_data.Lineup]
    list_of_all_lineups = [[player_name.strip() for player_name in lineup[1:].split('#')] for lineup in list_of_all_lineups]

    # Assign all of the list values to the df
    clean_lineup_data['P1'] = [lineup[0] for lineup in list_of_all_lineups]
    clean_lineup_data['P2'] = [lineup[1] for lineup in list_of_all_lineups]
    clean_lineup_data['C'] = [lineup[2] for lineup in list_of_all_lineups]
    clean_lineup_data['1B'] = [lineup[3] for lineup in list_of_all_lineups]
    clean_lineup_data['2B'] = [lineup[4] for lineup in list_of_all_lineups]
    clean_lineup_data['3B'] = [lineup[5] for lineup in list_of_all_lineups]
    clean_lineup_data['SS'] = [lineup[6] for lineup in list_of_all_lineups]
    clean_lineup_data['OF1'] = [lineup[7] for lineup in list_of_all_lineups]
    clean_lineup_data['OF2'] = [lineup[8] for lineup in list_of_all_lineups]
    clean_lineup_data['OF3'] = [lineup[9] for lineup in list_of_all_lineups]

    # Drop that dirty Lineup column now that its unnecessary
    clean_lineup_data.drop('Lineup', axis=1, inplace=True)

    return(clean_lineup_data)

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
def filter_dk_users(agg_lineups_df, points_ownership_df):
#def filter_dk_users(agg_lineups_df, dk_users_list):

    # Make this a dynamic input !!!
    dk_users = ['Awesemo', 'giantsquid', 'bkreider', 'dacoltz', 'getloose', 'totoroll33', 'BigT44', 'thepickler']

    # Loop through each user and create a dictionary with their data
    user_data_dict = {}

    for user in dk_users:
        user_data_dict[user] = melt_crosstab(agg_lineups_df, user)
        # Use this for MMA
        #user_data_dict[user]['F'] = user_data_dict[user][['F1','F2','F3','F4','F5','F6']].sum(axis=1)
        try:
            user_data_dict[user] = user_data_dict[user][['player','count','exposure']]
        except:
            print('Error with ', user)
            # Remove that user from the list to prevent more errors
            dk_users.remove(user)

    # Aggregate the various dataframes into a single one
    agg_exposures = pd.DataFrame()

    for user in dk_users:
        if user == dk_users[0]:
            agg_exposures = user_data_dict[user][['player','exposure']].round(2)
            agg_exposures.rename(columns={'exposure':user}, inplace=True)
        else:
            agg_exposures = pd.merge(agg_exposures, user_data_dict[user][['player','exposure']].round(2), how='outer', on='player')
            agg_exposures.rename(columns={'exposure':user}, inplace=True)

        agg_exposures = agg_exposures.replace(np.nan, 0.0)    
    # Now merge the 2 datasets that we've created together into 1
    master_df = pd.merge(agg_exposures, points_ownership_df, on='player')
    non_user_cols = ['player','Team', 'nickname','position','points', 'ownership']
    
    #master_df = master_df[[*non_user_cols, *master_df.columns.difference(non_user_cols)]]
    master_df = master_df[[*non_user_cols, *dk_users]]

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

def handle_outlier_names(df):

    # Loop through every row with an empty team field
    for row in df['Team']:
        pass

    return(df)

# Function takes in an input of: 1) list of MLB team names and 2) the path to the dash app's asset folder
# Output is a list of .jpeg images to embed in the app layout
# We need them in the same order as the teams are showing
def merge_team_logos(players_teams_df):

    # Base dir - might need to make this dynamic in the future
    file_path = 'C:/Users/Sean/Documents/python/dk_slate_study_tool/dash/assets/mlb_logo_lookup.csv'
    
    # Read in the lookup table 
    team_logo_lookup_df = pd.read_csv(file_path)

    # Merge the series/dataframe 
    merged_df = pd.merge(players_teams_df, team_logo_lookup_df, how='left', left_on='Team', right_on='nickname')

    return(merged_df)

# This is used to insert CSS styling into the dash table from the app.py
def get_team_colors():

    style_block = [
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('ARI')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('ATL'),
            #'column_id': 'nickname',
        },
        'backgroundColor': '#1C4E80',
        'color': 'black'
    },
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('BAL')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#EA6A47',
        'color': 'white'
    },
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('BOS')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('CHC')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('CHW')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#000000',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('CIN')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },                
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('CLE')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('COL')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#703770',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('DET')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('HOU')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#EA6A47',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('KCR')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#0091D5',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('LAA')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('LAD')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#0091D5',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('MIA')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#EA6A47',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('MIL')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('MIN')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('NYM')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#EA6A47',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('NYY')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#1C4E80',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('OAK')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#6AB187',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('PHI')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('PIT')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#DBAE58',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('SDP')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#DBAE58',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('SFG')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#EA6A47',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('SEA')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#000000',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('STL')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('TBR')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#488A99',
        'color': 'white'
    },
        {

        'if': {
            'filter_query': '{{nickname}} = {}'.format('TEX')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    },

        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('TOR')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#4CB5F5',
        'color': 'white'
    },
        {
        'if': {
            'filter_query': '{{nickname}} = {}'.format('WAS')
            #'column_id': ['nickname','player'],
        },
        'backgroundColor': '#D32D41',
        'color': 'white'
    }
    ]    

    return style_block

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

# This takes in a file upload from the UI and returns an HTML table (of sorts..) of the data
def convert_df_to_html(df):

    #df = pd.read_json(json_serialized_df)

    return html.Div([

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            sort_action="native",
            filter_action='native',
            style_data_conditional = (
                get_team_colors()
            )
        ),

        html.Hr(),  # horizontal line
    ])        


# Used by the Individual Lineup Analyzer to filter the data by user
def parse_mlb_lineup(lineups_df, points_ownership_df, player_team_pos_df, entry_name):
    
    # Get the lineup for that exact entry_name
    entry_lineup = lineups_df[lineups_df['raw_entry_name'] == entry_name]
    
    # Clean up some columns
    #entry_lineup['DK User'] = entry_lineup['EntryName']
    entry_lineup['Lineup Name'] = entry_lineup['raw_entry_name']
    
    # Final columns and order
    output_cols = ['Rank', 'Points', 'Lineup Name', 'P1','P2','C','1B','2B','3B','SS','OF1','OF2','OF3']
    non_player_cols = ['Rank','Points','Lineup Name']
    entry_lineup = entry_lineup[output_cols]

    # Transpose the dataframe for readability
    entry_lineup = entry_lineup.transpose()
    entry_lineup.columns = ['Data']

    # Fuzzy match the player names to the lookup df with every player
    # Get the name matches - this is a dict with key being position and value being the player
    name_matches = {index:[match_name(value, player_team_pos_df['Player'])[0]] for index, value in zip(entry_lineup[np.logical_not(entry_lineup.index.isin(non_player_cols))].index, entry_lineup[np.logical_not(entry_lineup.index.isin(non_player_cols))].iloc[:,0])}
    # Create a dataframe of the matches from the dictionary
    matches_df = pd.DataFrame.from_dict(name_matches).transpose()
    matches_df.columns = ['player_match']
    matches_df['position'] = matches_df.index

    # Merge the team data
    merged_matches_df = pd.merge(matches_df, player_team_pos_df[['Player','Team']], how='left', left_on='player_match', right_on='Player')
    merged_matches_df = merged_matches_df[['player_match', 'position','Team']]

    # Then merge to the entry_lineup
    entry_lineup = pd.merge(entry_lineup, merged_matches_df, left_index=True, right_index=False, right_on='position', how='left')

    # Merge entry_lineup with points_ownership and get the points, ownership
    entry_lineup = pd.merge(entry_lineup, points_ownership_df[['player','ownership','points']], how='left', left_on='Data', right_on='player')

    # This is mostly just handling empty rows - prob not necessary
    entry_lineup.rename(columns={'position':'Lineup Info', 'Team':'nickname','ownership':'Ownership','points':'Points'}, inplace=True)
    entry_lineup = entry_lineup[['Lineup Info','Data','nickname','Ownership','Points']]
    
    return(entry_lineup)

