import os
from datetime import datetime

def get_epw_search_string(dt_obj, hour=1):
    """
    Creates the search string for EPW format: ',Month,Day,Hour,'
    matches the format found in AMY/TMY files (e.g., '1973,1,1,1,0' matches ',1,1,1,').
    
    NOTE: Year is excluded to allow matching dates in TMY files 
    where the year column might not match the actual calendar year.
    """
    return f",{dt_obj.month},{dt_obj.day},{hour},"

def get_week_data(epw_path, start_date):
    """
    Reads an AMY EPW file and extracts 168 hours (1 week) of data 
    starting from the specified date.
    """
    search_str = get_epw_search_string(start_date, hour=1)
    week_data = []
    capture = False
    
    # Check if file exists first
    if not os.path.exists(epw_path):
        raise FileNotFoundError(f"AMY file not found: {epw_path}")

    with open(epw_path, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        # Start capturing when we find the date (Month,Day) and hour 1
        # We check if search_str is in line to ignore the Year column at the start
        if not capture and search_str in line:
            capture = True
        
        if capture:
            week_data.append(line)
            # Stop after 168 hours (1 week)
            if len(week_data) == 168:
                break
    
    # Check if date was found
    if not capture:
        print(f"Date {start_date.strftime('%b %d')} not present in {epw_path}")
        raise ValueError(f"Date {start_date.strftime('%b %d')} not present in {epw_path}")

    if len(week_data) < 168:
        raise ValueError(f"Could not find a full week (168 hours) starting {start_date} in {epw_path}")
        
    return week_data

def generate_hybrid_epw(date1, date2, tmy_file, amy1_file, amy2_file, output_file="modified_tmy.epw"):
    """
    Creates a hybrid EPW file by replacing two specific weeks in a TMY file 
    with data from AMY files.

    Arguments:
    date1 (datetime): Start date for the first replacement period.
    date2 (datetime): Start date for the second replacement period.
    tmy_file (str): Path to the base TMY EPW file.
    amy1_file (str): Path to the AMY file corresponding to date1.
    amy2_file (str): Path to the AMY file corresponding to date2.
    output_file (str): Name of the resulting file.
    """
    
    print(f"--- Starting EPW Modification ---")
    
    # 1. Organize events to ensure we process them in chronological order
    events = [
        {'date': date1, 'amy_file': amy1_file, 'name': 'Period 1'},
        {'date': date2, 'amy_file': amy2_file, 'name': 'Period 2'}
    ]
    # Sort by date (month/day)
    events.sort(key=lambda x: x['date'])

    # 2. Extract the replacement weeks from the AMY files
    for event in events:
        print(f"Extracting week for {event['name']} ({event['date'].strftime('%Y-%b-%d')}) from {os.path.basename(event['amy_file'])}...")
        try:
            event['data'] = get_week_data(event['amy_file'], event['date'])
        except (ValueError, FileNotFoundError) as e:
            print(f"Stopping: {e}")
            return

    # 3. Read the entire TMY file into memory
    if not os.path.exists(tmy_file):
        print(f"Error: TMY file not found at {tmy_file}")
        return

    with open(tmy_file, 'r') as f:
        tmy_lines = f.readlines()

    # 4. Find the line indices in the TMY file where the swaps should happen
    for event in events:
        search_str = get_epw_search_string(event['date'], hour=1)
        found = False
        for idx, line in enumerate(tmy_lines):
            # We look for the specific date signature to find the start line index
            if search_str in line:
                event['start_index'] = idx
                event['end_index'] = idx + 168 # The index where TMY data resumes (1 week later)
                found = True
                break
        
        # Check if date was found in TMY
        if not found:
            print(f"Date {event['date'].strftime('%b %d')} not present in TMY file.")
            return # Stop execution if date is missing

    # 5. Construct the new file content
    first_event = events[0]
    second_event = events[1]

    # Check for overlap
    if first_event['end_index'] > second_event['start_index']:
        print("Warning: The two selected weeks overlap! Cannot merge.")

    new_content = []
    
    # A. Header and TMY data before first event
    new_content.extend(tmy_lines[ : first_event['start_index']])
    
    # B. First AMY Week
    new_content.extend(first_event['data'])
    
    # C. TMY data between first and second event
    new_content.extend(tmy_lines[first_event['end_index'] : second_event['start_index']])
    
    # D. Second AMY Week
    new_content.extend(second_event['data'])
    
    # E. TMY data after second event
    new_content.extend(tmy_lines[second_event['end_index'] : ])

    # 6. Write to file
    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, 'w') as f:
            for line in new_content:
                f.write(line)
        print(f"Success! New EPW saved as: {output_file}")
    except IOError as e:
        print(f"Error writing output file: {e}")

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Example: Define your dates and file paths here
    d1 = datetime(2016, 7, 11)  # Tampa Cold Date
    d2 = datetime(1989, 12, 24)  # Tampa Hot Date

    # Paths (Using Raw strings r'' to handle Windows backslashes)
    base_dir = r'Y:/DIY_EPW/results_new/Tampa/'
    tmy = os.path.join(base_dir, 'USA_FL_Tampa-MacDill.AFB.747880_TMYx.2009-2023.epw')
    amy1 = os.path.join(base_dir, 'FL747880AMY_2010.epw')
    amy2 = os.path.join(base_dir, 'FL747880AMY_2016.epw')

    output_path = os.path.join(base_dir, "Hybrid_Weather_747880_Tampa.epw")

    generate_hybrid_epw(d1, d2, tmy, amy1, amy2, output_path)