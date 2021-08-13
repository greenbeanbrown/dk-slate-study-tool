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

import sys
#sys.path.insert(0, '../../functions/')
from functions import *

def prep_raw_nfl_contest_data(raw_dk_contest_data, sport):

    # Take in 1 raw dataframe as an input
    working_df = raw_dk_contest_data.copy()

    # Return a list of 2 dataframes: 1) points ownership df 2) exposures by entry name
    # 1st create points ownership df
    points_ownership_df = create_points_own_df(raw_dk_contest_data)

    # Now, create the ownership exposures
    # FLAG - this is unnecessary after separating the functions into different files by sport
    if sport == 'MLB':
        exposures_df = cleanup_mlb_lineup_data(raw_dk_contest_data)
    elif sport == 'MMA':
        exposures_df = cleanup_mma_lineup_data(raw_dk_contest_data)
    elif sport == 'NFL':
        exposures_df = cleanup_nfl_lineup_data(raw_dk_contest_data)
    else:
        raise ValueError('incorrect sport type entered as input')

    # Merge player team and position data for reference (should always be in same dir)
    player_team_pos_df = pd.read_csv('assets/nfl_players_pos_teams_data.csv') 

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

# This function takes in a dataframe of the raw DK contest results and cleans it up a bit for our purposes
def cleanup_nfl_lineup_data(raw_lineup_data):

    # Create an empty df that will hold the final output
    clean_lineup_data = raw_lineup_data.copy()

    # First thing to do is drop the nans from the Lineup field - these are empty lineups that people submitted and should not be included in this analysis
    clean_lineup_data = clean_lineup_data[['Rank','EntryId','EntryName','Points','Lineup']]
    clean_lineup_data = clean_lineup_data.dropna()

    # Clean the username field - it comes out with extra chars 
    clean_lineup_data['raw_entry_name'] = clean_lineup_data['EntryName']
    clean_lineup_data['EntryName'] = clean_lineup_data['EntryName'].apply(lambda row: clean_entry_name(row))

    # Replace all position substrings with ##, which we can use to split the lineups easily with - then we will add the positions back after
    list_of_all_lineups = [lineup.replace('QB ', '#').replace('RB ', '#').replace('FLEX ','#').replace('WR ','#').replace('TE ','#').replace('DST ', '#') for lineup in clean_lineup_data.Lineup]

    # Split up all the Fighter names and get rid of extra space - this is MUCH better than the original idea
    list_of_all_lineups = [[player_name.strip() for player_name in lineup[1:].split('#')] for lineup in list_of_all_lineups]

    # Assign all of the list values to the df
    clean_lineup_data['1'] = [lineup[0] for lineup in list_of_all_lineups]
    clean_lineup_data['2'] = [lineup[1] for lineup in list_of_all_lineups]
    clean_lineup_data['3'] = [lineup[2] for lineup in list_of_all_lineups]
    clean_lineup_data['4'] = [lineup[3] for lineup in list_of_all_lineups]
    clean_lineup_data['5'] = [lineup[4] for lineup in list_of_all_lineups]
    clean_lineup_data['6'] = [lineup[5] for lineup in list_of_all_lineups]
    clean_lineup_data['7'] = [lineup[6] for lineup in list_of_all_lineups]
    clean_lineup_data['8'] = [lineup[7] for lineup in list_of_all_lineups]
    clean_lineup_data['9'] = [lineup[8] for lineup in list_of_all_lineups]
    #clean_lineup_data['10'] = [lineup[9] for lineup in list_of_all_lineups]

    # Drop that dirty Lineup column now that its unnecessary
    clean_lineup_data.drop('Lineup', axis=1, inplace=True)

    return(clean_lineup_data)
    
    
# SCRAPING FUNCTION
# This function parses rotogrinders website for Player Names, Teams, and Positions for MLB data
# Input is a url that has a GET result for the rotogrinders url
# example url = 'https://rotogrinders.com/game-stats/mlb-pitcher?site=draftkings&range=season'
def parse_nfl_stat_data(url):
    # Initialize driver object
    driver = webdriver.Firefox()   # Establish the driver, we are using FireFox in this case
    driver.get(url) 

    try:
        # Find the ALL button, to show all results 
        page_buttons = driver.find_elements_by_class_name("page")
    
        all_button = page_buttons[len(page_buttons)-1]
        # Click the button
        driver.execute_script("arguments[0].click();", all_button)
    except:
        pass
    
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
    
# Function takes in an input of: 1) list of MLB team names and 2) the path to the dash app's asset folder
# Output is a list of .jpeg images to embed in the app layout
# We need them in the same order as the teams are showing
#def merge_team_logos(players_teams_df):
#
#    # Base dir - might need to make this dynamic in the future
#    #file_path = 'C:/Users/Sean/Documents/python/dk_slate_study_tool/dash/assets/mlb_logo_lookup.csv'
#    file_path = 'assets/mlb_logo_lookup.csv'
#    
#
#    # Read in the lookup table 
#    team_logo_lookup_df = pd.read_csv(file_path)
#
#    # Merge the series/dataframe 
#    merged_df = pd.merge(players_teams_df, team_logo_lookup_df, how='left', left_on='Team', right_on='nickname')
#
#    return(merged_df)

# This is used to insert CSS styling into the dash table from the app.py

# This takes in a file upload from the UI and returns an HTML table (of sorts..) of the data
def convert_nfl_df_to_html(df, style='team_colors', page_size=250):

    #df = pd.read_json(json_serialized_df)

    if style == 'team_colors':
        return html.Div([

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                sort_action="native",
                filter_action='native',
                page_size=page_size,
                #style_data_conditional = (get_team_colors())
            ),

            html.Hr(),  # horizontal line
        ])       
    
    # Option for no formatting 
    elif style == None:
        return html.Div([

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                sort_action="native",
                filter_action='native',
                page_size=page_size
            ),

            html.Hr(),  # horizontal line
        ]) 


    else:
        # Conditional Formatting for players exposures
        (styles, legend) = discrete_background_color_bins(df)

        return html.Div([

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                sort_action="native",
                filter_action='native',
                style_data_conditional=styles,
                page_size=page_size
            ),

            html.Hr(),  # horizontal line
        ])               

# Used by the Individual Lineup Analyzer to filter the data by user
def parse_nfl_lineup(lineups_df, points_ownership_df, player_team_pos_df, entry_name):
    
    # Get the lineup for that exact entry_name
    entry_lineup = lineups_df[lineups_df['raw_entry_name'] == entry_name]
    
    # Clean up some columns
    #entry_lineup['DK User'] = entry_lineup['EntryName']
    entry_lineup['Lineup Name'] = entry_lineup['raw_entry_name']
    
    # Final columns and order
    output_cols = ['EntryId','Rank', 'Points', 'Lineup Name', '1','2','3','4','5','6','7','8','9']
    non_player_cols = ['EntryId','Rank','Points','Lineup Name']
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

# This is used by the individual lineup analyzer tab to add the stack info at the bottom section of the page
# The expectation is that the input for this function is the output from parse_mlb_lineup()
def calculate_nfl_stacks(entry_lineup_df):
    
    working_df = entry_lineup_df

    # Trim the dataframe down to avoid pitchers in the count
    working_df.rename(columns={'nickname':'Team'}, inplace=True)

    #working_df = merge_team_logos(working_df)
    working_df['Count'] = working_df.groupby('Team')['Team'].transform('count')

    import ipdb; ipdb.set_trace()
    
    # Add the EntryId as a column for merging in later use - this is the first field of the Data column
    # This is hardcoded for now basically because it's a strange shaped dataframe at this point in time
    working_df['EntryId'] = working_df.loc[0, 'Data']
    # Filter down columns
    #working_df = working_df[['EntryId','logo_path','Team','Count']].dropna()
    working_df = working_df[['EntryId','Team','Count']].dropna()

    working_df = working_df.drop_duplicates().sort_values('Count', ascending=False)

    stacks_df = working_df 

    return(stacks_df)        
    
    
# This function takes in a triple that contains the stack info and styles it into HTML for the app.layout()
# FLAG - need to update this
def convert_nfl_stacks_to_html(app, stacks_df):

    # This function parses each team's stack info into an html, this will be applied to each element of the input
    def create_stack_html_row(stack_row):
        # Just grabbing the path here to make it cleaner
        logo_path = app.get_asset_url('mlb_logos/' + os.path.basename(stack_row['logo_path']))

        html_block = html.Div(children=[
            # Team logo
            html.Div(
                html.Img(src=logo_path), 
                style={'textAlign':'center', 'width':'15%','display':'inline-block'}),
            # Team name 
            html.Div(
                html.H3(stack_row['Team']),
                style={'textAlign':'center', 'width':'15%','display':'inline-block'}),
            # Stack count
            html.Div(
                html.H3(stack_row['Count']),
                style={'textAlign':'center', 'width':'15%','display':'inline-block'})
        ])
        
        return(html_block)
    
    # Empty list that will hold all the div elements later on
    stacks_html_blocks = []

    # General idea here is we loop through each element of the triple and apply the HTML template structure to each element
    for index, row in stacks_df.iterrows():
        # Create a list of the various div tags for each team_stack
        stacks_html_blocks.append(create_stack_html_row(row))

    return(stacks_html_blocks)


# This is used by the Stacks Calculator to convert raw lineup data into a digestable table of aggregate MLB stacks
def summarize_nfl_lineup_stacks(raw_dk_contest_data, points_ownership_df, player_team_pos_df, *args):
    
    # Cleanup mlb lineup data
    lineups_df = cleanup_nfl_lineup_data(raw_dk_contest_data)

    # If there is no optional user parameter passed, then don't filter the dataframe
    if len(list(*args)) == 0:
        pass
    # if there is a parameter passed then filter the df with only those users
    else:
        lineups_df = lineups_df[lineups_df['EntryName'].isin(list(*args))]

    # Parse mlb lineup
    list_of_all_lineup_dfs = [parse_nfl_lineup(lineups_df, points_ownership_df, player_team_pos_df, entry_name) for entry_name in lineups_df.raw_entry_name]
    
    # Calculate stacks
    list_of_all_lineup_stacks = [calculate_nfl_stacks(lineup_df) for lineup_df in list_of_all_lineup_dfs]
    
    def convert_stack_to_string(nfl_stacks_df):
        return(str('-'.join(str(int(x)) for x in nfl_stacks_df['Count'])))
    
    def convert_teams_to_string(nfl_stacks_df):
        return(str('-'.join(str(x) for x in nfl_stacks_df['Team'])))
    
    # This function adds trailing zeros to relevant series of data related to stacks, due to blank entries
    # Main purpose of this is to allow for a clean dataframe to be constructed
    def add_zeros_for_blank_entries(raw_dk_contest_data, data_list):
        # Assess how far off the lengths are
        length_needed = len(raw_dk_contest_data)
        series_length = len(data_list)
        # Determine how many zeros need to be added
        num_zeros_to_add = length_needed - series_length
        # Add the zeros to the end of the list
        new_data_list = np.concatenate([data_list, np.zeros(num_zeros_to_add)])
        return(new_data_list)
    
    # Convert the stack count to a single string, delimited by dashes
    stack_strings = [convert_stack_to_string(nfl_stack_df) for nfl_stack_df in list_of_all_lineup_stacks]
    team_strings = [convert_teams_to_string(nfl_stack_df) for nfl_stack_df in list_of_all_lineup_stacks]

    #    # Return a dataframe with all this stuff for output
    #    agg_stacks_df = pd.DataFrame({'DK User':raw_dk_contest_data['EntryName'], 
    #                                  'Points':raw_dk_contest_data['Points'], 
    #                                  'P1':add_zeros_for_blank_entries(raw_dk_contest_data, lineups_df['P1']), 
    #                                  'P2':add_zeros_for_blank_entries(raw_dk_contest_data, lineups_df['P2']),
    #                                  'Teams Stacked':add_zeros_for_blank_entries(raw_dk_contest_data, team_strings), 
    #                                  'Stack Type':add_zeros_for_blank_entries(raw_dk_contest_data, stack_strings)})

    
    # Return a dataframe with all this stuff for output
    agg_stacks_df = pd.DataFrame({'DK User':lineups_df['EntryName'], 
                                  'Points':lineups_df['Points'], 
                                  #'P1':lineups_df['P1'], 
                                  #'P2':lineups_df['P2'],
                                  'Teams Stacked':team_strings, 
                                  'Stack Type':stack_strings})    

    

    return(agg_stacks_df)    