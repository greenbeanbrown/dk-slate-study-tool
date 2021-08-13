

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