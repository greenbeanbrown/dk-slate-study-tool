import pandas as pd
import numpy as np

import time 

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

#def clean_player_name(player_name):
#    # Removing 
#    clean_name = player_name.replace('Jr.', '')
#    clean_name = player_name.replace('Sr.', '')
#    clean_name = player_name.replace(' I ', ' ')
#    clean_name = player_name.replace(' II ', ' ')
#    clean_name = player_name.replace(' III ', ' ')
#
#    clean_name = clean_name.strip()
#
#    return(clean_name)

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

    # Clean the username field - it comes out with extra chars 
    clean_lineup_data['EntryName'] = clean_lineup_data['EntryName'].apply(lambda row: clean_entry_name(row))

    # Replace all position substrings with ##, which we can use to split the lineups easily with - then we will add the positions back after
    list_of_all_lineups = [lineup.replace('P ', '#').replace('C ', '#').replace('1B ','#').replace('2B','#').replace('3B','#').replace('SS', '#').replace('OF','#') for lineup in raw_lineup_data.Lineup]


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
    
    # Mutate dataframe for simplicity
    #crosstab_lineup = crosstab_lineup[['player','count','exposure']]
    
    # Sorting
    crosstab_lineup = crosstab_lineup.sort_values('count', ascending=False)    
    
    return(crosstab_lineup)