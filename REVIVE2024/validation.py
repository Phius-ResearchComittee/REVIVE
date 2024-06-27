# native imports
import os
import json

# dependency imports
import pandas as pd


# define constants
P_CARBON_CORRECTION_DB_FILE_NAME = "Carbon Correction Database.csv"
CONSTRUCTION_DB_FILE_NAME = "Construction Database.csv"
COUNTRY_EMISSIONS_DB_FILE_NAME = "Country Emission Database.csv"
HOURLY_EMISSIONS_FILE_NAME = "Hourly Emission Rates.csv"
MATERIALS_DB_FILE_NAME = "Material Database.csv"
NP_CARBON_CORRECTION_DB_FILE_NAME = "Nonperformance Carbon Correction Database.csv"
WINDOW_DB_FILE_NAME = "Window Database.csv"
CAMBIUM_FACTORS_DIR = "CambiumFactors"
WEATHER_DATA_DIR = "Weather Data"

required_files = [
    P_CARBON_CORRECTION_DB_FILE_NAME,
    CONSTRUCTION_DB_FILE_NAME,
    COUNTRY_EMISSIONS_DB_FILE_NAME,
    HOURLY_EMISSIONS_FILE_NAME,
    MATERIALS_DB_FILE_NAME,
    NP_CARBON_CORRECTION_DB_FILE_NAME,
    WINDOW_DB_FILE_NAME,
]

required_dirs = [
    CAMBIUM_FACTORS_DIR,
    WEATHER_DATA_DIR
]

invalid_csv_prompt = lambda invalid_file : f"File \"{invalid_file}\" cannot be parsed as CSV."
missing_column_prompt = lambda missing_col, file : f"Column \"{missing_col}\" missing from file \"{file}\". Please make sure column exists and is named properly."
   


# define functions
def validate_database_content(req_cols_path, db_path):
    validate_database_exists(db_path)
    validate_database_structure(db_path)
    validate_database_file_structures(req_cols_path, db_path)


def validate_database_exists(db_path):
    # prelim: ensure the file path exists
    assert os.path.isdir(db_path), f"Directory path \"{db_path}\" does not exist. Please use the folder browser to select path."
    

def validate_database_structure(db_path):
    missing_item_prompt = lambda missing_item : f"Cannot find {missing_item} in specified database directory."
    
    # make sure the required items exist in the directory
    for file in required_files:
        assert os.path.isfile(os.path.join(db_path, file)), missing_item_prompt(f"file \"{file}\"")
    for dir in required_dirs:
        assert os.path.isdir(os.path.join(db_path, dir)), missing_item_prompt(f"folder \"{dir}\"")


def validate_database_file_structures(req_cols_path, db_path):
    # load the required columns
    with open(req_cols_path) as fp:
        content = json.load(fp)
     
    for file in required_files:
        # get required columns for this file
        key = file[:file.index(".csv")]
        cols = content[key]

        # ensure csv is valid
        file_path = os.path.join(db_path, file)
        try:
            df = pd.read_csv(file_path)
        except:
            raise AssertionError(invalid_csv_prompt(file_path))
        
        # ensure columns are correct
        for col in cols:
            assert col in df, missing_column_prompt(col, file)

    
def validate_runlist_content(req_cols_path, rl_path, db_path):
    validate_runlist_exists(rl_path)
    validate_runlist_structure(req_cols_path, rl_path)
    validate_runlist_inputs(rl_path, db_path)


def validate_runlist_exists(rl_path):
    assert os.path.isfile(rl_path), f"Runlist path \"{rl_path}\" does not exist. Please use the file browser to select path."


def validate_runlist_structure(req_cols_path, rl_path):
    # make sure runlist is valid csv
    try:
        df = pd.read_csv(rl_path)
    except:
        raise AssertionError(invalid_csv_prompt(rl_path))

    # load the column requirements
    with open(req_cols_path, "r") as fp:
        content = json.load(fp)
    cols = content["Runlist"]

    # compare columns
    for col in cols:
        assert col in df, f"Column {col} missing, runlist may be out of date."


def validate_runlist_inputs(rl_path, db_path):
    # load runlist and database files
    runlist_df = pd.read_csv(rl_path)
    construction_df = pd.read_csv(os.path.join(db_path, CONSTRUCTION_DB_FILE_NAME))
    carbon_df = pd.read_csv(os.path.join(db_path, P_CARBON_CORRECTION_DB_FILE_NAME))
    np_carbon_df = pd.read_csv(os.path.join(db_path, NP_CARBON_CORRECTION_DB_FILE_NAME))
    country_emissions_df = pd.read_csv(os.path.join(db_path, COUNTRY_EMISSIONS_DB_FILE_NAME))
    hourly_emissions_df = pd.read_csv(os.path.join(db_path, HOURLY_EMISSIONS_FILE_NAME))
    materials_df = pd.read_csv(os.path.join(db_path, MATERIALS_DB_FILE_NAME))
    window_df = pd.read_csv(os.path.join(db_path, WINDOW_DB_FILE_NAME))
    
    # case name (avoid strange characters)
    is_legal_char = lambda x : x.isalnum() or x in " _"
    for case_name in runlist_df["CASE_NAME"]:
        assert not any(is_legal_char(c) for c in case_name), "Case name may contain letters, numbers, underscores, or spaces only."
    
    # check for geometry file
    for idf in runlist_df["GEOMETRY_IDF"]:
        assert os.path.isfile(idf)
    
    # check for weather file
    weather_dir = os.path.join(db_path, WEATHER_DATA_DIR)
    for epw, ddy in zip(runlist_df["EPW"], runlist_df["DDY"]):
        assert os.path.isfile(os.path.join(weather_dir, epw)), f"EPW file \"{epw}\" could not be found in weather folder \"{weather_dir}\"."
        assert os.path.isfile(os.path.join(weather_dir, ddy)), f"DDY file \"{ddy}\" could not be found in weather folder \"{weather_dir}\"."
    
    # check construction list items
    for app_list in runlist_df["APPLIANCE_LIST"]:
        for app in app_list:
            assert app in construction_df["NAME"], f"Appliance \"{app}\" not found in construction database \"{os.path.join(db_path, CONSTRUCTION_DB_FILE_NAME)}\"."




