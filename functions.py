import pandas as pd
import numpy as np

import time 


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

    # First thing to do is drop the nans from the Lineup field - these are empty lineups that people submitted and should not be included in this analysis
    clean_lineup_data = clean_lineup_data[['Rank','EntryId','EntryName','Points','Lineup']]
    clean_lineup_data = clean_lineup_data.dropna()

    # Clean the username field - it comes out with extra chars 
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

    ############################# START MLB ##################################

    # Begin melting and crosstabbing the exposures data 
    # Eventually need the input to be dynamic in the web app, but hardcoding a list for now
    dk_users = ['Awesemo', 'giantsquid', 'bkreider', 'dacoltz', 'getloose', 'totoroll33', 'BigT44', 'I_Slewfoot_U', 'B_Heals152', 'thepickler']

# Loop through each user and create a dictionary with their data
    user_data_dict = {}

    for user in dk_users:
        user_data_dict[user] = melt_crosstab(agg_lineups, user)
        user_data_dict[user] = user_data_dict[user][['player','count','exposure']]
    

    ############################# END MLB ##################################

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