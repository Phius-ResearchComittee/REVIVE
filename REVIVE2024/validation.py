# native imports
import os
import json
from datetime import datetime

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
missing_item_prompt = lambda missing_item : f"Cannot find {missing_item} in specified database directory."
missing_column_prompt = lambda missing_col, file : f"Column \"{missing_col}\" missing from file \"{file}\". Please make sure column exists and is named properly."
missing_field_prompt = lambda missing_field : f"Field \"{missing_field}\" is required."
wrong_file_prompt = lambda item_name, wrong_path : f"{item_name} \"{wrong_path}\" does not exist. Please use the file browser to select path."
rl_missing_item_prompt = lambda rl_file, missing_item, location : f"Problem in runlist \"{rl_file}\": {missing_item} not found in {location}. Please make sure runlist was generated using the designated database."
rl_missing_value_prompt = lambda rl_file, col : f"Problem in runlist \"{rl_file}\": Required column \"{col}\" is missing one or more values."
rl_misc_prompt = lambda rl_file, prompt : f"Problem in runlist \"{rl_file}\": {prompt}"
rl_numeric_prompt = lambda rl_file, numeric_col : f"Problem in runlist \"{rl_file}\": All values in column \"{numeric_col}\" must be a numeric input."
rl_boolean_prompt = lambda rl_file, bool_col : f"Problem in runlist \"{rl_file}\": All values in column \"{bool_col}\" must be either 1 (True) or 0 (False)."


# define functions
def validate_database_content(req_cols_path, db_path):
    validate_database_exists(db_path)
    validate_database_structure(db_path)
    validate_database_file_structures(req_cols_path, db_path)


def validate_database_exists(db_path):
    # prelim: ensure the file path exists
    assert os.path.isdir(db_path), wrong_file_prompt("Directory path", db_path)
    

def validate_database_structure(db_path):
    
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
    assert os.path.isfile(rl_path), wrong_file_prompt("Runlist path", rl_path)


def validate_runlist_structure(req_cols_path, rl_path):
    # make sure runlist is valid csv
    try:
        df = pd.read_csv(rl_path)
    except:
        raise AssertionError(invalid_csv_prompt(rl_path))

    # load the column requirements
    with open(req_cols_path, "r") as fp:
        content = json.load(fp)
    req_cols = content["Runlist"]
    present_cols = df.columns

    # compare columns
    for col in req_cols:
        assert col in present_cols, rl_misc_prompt(rl_path, f"Column {col} missing, runlist may be out of date.")
    for col in present_cols:
        assert col in req_cols, rl_misc_prompt(rl_path, f"Column {col} is not allowed, please remove it from runlist.")


def validate_runlist_inputs(rl_path, db_path):
    # infer database file paths
    construction_db_path = os.path.join(db_path, CONSTRUCTION_DB_FILE_NAME)
    carbon_db_path = os.path.join(db_path, P_CARBON_CORRECTION_DB_FILE_NAME)
    np_carbon_db_path = os.path.join(db_path, NP_CARBON_CORRECTION_DB_FILE_NAME)
    country_emissions_db_path = os.path.join(db_path, COUNTRY_EMISSIONS_DB_FILE_NAME)
    hourly_emissions_db_path = os.path.join(db_path, HOURLY_EMISSIONS_FILE_NAME)
    materials_db_path = os.path.join(db_path, MATERIALS_DB_FILE_NAME)
    window_db_path = os.path.join(db_path, WINDOW_DB_FILE_NAME)

    # load items from databases
    runlist_df = pd.read_csv(rl_path)
    construction_list = pd.read_csv(construction_db_path, index_col="Name").index.tolist()
    carbon_list = pd.read_csv(carbon_db_path, index_col="Name").index.tolist()
    np_carbon_list = pd.read_csv(np_carbon_db_path, index_col="Name").index.tolist()
    country_list = pd.read_csv(country_emissions_db_path, index_col="COUNTRY").index.tolist()
    grid_regions_list = pd.read_csv(hourly_emissions_db_path).columns
    materials_list = pd.read_csv(materials_db_path, index_col="NAME").index.tolist()
    window_list = pd.read_csv(window_db_path, index_col="NAME").index.tolist()

    # make labels for error prompts
    label_maker = lambda db_type, db_path : f"{db_type} database \"{db_path}\""
    construction_db_label = label_maker("construction", construction_db_path)
    carbon_db_label = label_maker("carbon", carbon_db_path)
    np_carbon_db_label = label_maker("non-performance carbon", np_carbon_db_path)
    country_emissions_db_label = label_maker("country emissions", country_emissions_db_path)
    hourly_emissions_db_label = label_maker("hourly emissions", hourly_emissions_db_path)
    materials_db_label = label_maker("materials", materials_db_path)
    window_db_label = label_maker("window", window_db_path)

    # ensure all required columns are filled out
    not_empty = lambda x : not pd.isna(x) and str(x).strip()
    optional_columns = ["GAS_PRICE_[$/THERM]", "APPLIANCE_LIST",
                        "EXT_WINDOW_2", "EXT_WINDOW_3",
                        "FOUNDATION_INTERFACE_2", "FOUNDATION_INSULATION_2",
                        "FOUNDATION_PERIMETER_2", "FOUNDATION_INSULATION_DEPTH_2",
                        "FOUNDATION_INTERFACE_3", "FOUNDATION_INSULATION_3",
                        "FOUNDATION_PERIMETER_3", "FOUNDATION_INSULATION_DEPTH_3",
                        "EXT_WALL_2_NAME", "EXT_ROOF_2_NAME", "EXT_DOOR_2_NAME",
                        "INT_FLOOR_2_NAME","EXT_FLOOR_2_NAME",
                        "EXT_WALL_3_NAME", "EXT_ROOF_3_NAME", "EXT_DOOR_3_NAME",
                        "INT_FLOOR_3_NAME","EXT_FLOOR_3_NAME",
                        "PERF_CARBON_MEASURES", "NON_PERF_CARBON_MEASURES",
                        "HEATING_COP", "COOLING_COP",
                        "VENT_SYSTEM_TYPE"]
    for col in [c for c in runlist_df.columns if c not in optional_columns]:
        for cell in runlist_df[col]:
            assert not_empty(cell), rl_missing_value_prompt(rl_path, col)

    for _, row in runlist_df.iterrows():

        # case name (avoid strange characters)
        is_legal_char = lambda x : x.isalnum() or x in "_- "
        case_name = row["CASE_NAME"]
        for c in case_name:
            assert is_legal_char(c), rl_misc_prompt(rl_path, "Case names may contain letters, numbers, underscores, dashes, or spaces only.")
        
        # check for geometry file
        idf = row["GEOMETRY_IDF"]
        assert os.path.isfile(idf), rl_misc_prompt(rl_path, f"Geometry file \"{idf}\" not found in current working directory.")
        
        # check for weather file
        weather_dir = os.path.join(db_path, WEATHER_DATA_DIR)
        epw, ddy = row["EPW"], row["DDY"]
        assert os.path.isfile(os.path.join(weather_dir, epw)), rl_misc_prompt(rl_path, f"EPW file \"{epw}\" could not be found in weather folder \"{weather_dir}\".")
        assert os.path.isfile(os.path.join(weather_dir, ddy)), rl_misc_prompt(rl_path, f"DDY file \"{ddy}\" could not be found in weather folder \"{weather_dir}\".")
        
        # check all numerical inputs
        numeric_cols = ["ELEC_PRICE_[$/kWh]","SELLBACK_PRICE_[$/kWh]","ANNUAL_ELEC_CHARGE",
                        "GAS_PRICE_[$/THERM]","ANNUAL_GAS_CHARGE",
                        "MorphFactorDB1","MorphFactorDP1",
                        "MorphFactorDB2","MorphFactorDP2",
                        "PV_SIZE_[W]","PV_TILT","PV_AZIMUTH",
                        "CHI_VALUE","INFILTRATION_RATE",
                        "Operable_Area_N","Operable_Area_E",
                        "Operable_Area_W","Operable_Area_S",
                        "SENSIBLE_RECOVERY_EFF","LATENT_RECOVERY_EFF",
                        "ENVELOPE_LABOR_FRACTION",
                        "ANALYSIS_DURATION"]
        for col in numeric_cols:
            try:
                _ = float(row[col])
            except ValueError:
                raise AssertionError(rl_numeric_prompt(rl_path, col))
            
        # check all boolean inputs
        boolean_cols = ["NATURAL_GAS",
                        "NAT_VENT_AVAIL",
                        "SHADING_AVAIL",
                        "DEMAND_COOLING_AVAIL"]
        for col in boolean_cols:
            assert str(row[col]).strip() in ["1", "0"], rl_boolean_prompt(rl_path, col)
        
        # appliances
        app_list = row["APPLIANCE_LIST"]
        app_list = app_list.split(",") if not pd.isna(app_list) else []
        for app in [a.strip() for a in app_list]:
            assert app in construction_list, rl_missing_item_prompt(rl_path, f"Appliance \"{app}\"", construction_db_label)
    
        # water heater fuel
        dhw_fuel = row["WATER_HEATER_FUEL"]
        prefixed_fuel = f"DHW_{dhw_fuel}"
        assert prefixed_fuel in construction_list, rl_missing_item_prompt(rl_path, f"Fuel type \"{prefixed_fuel}\"", construction_db_label)
    
        # mechanical system
        mech_sys = row["MECH_SYSTEM_TYPE"]
        assert mech_sys in construction_list, rl_missing_item_prompt(rl_path, f"Mechanical system \"{mech_sys}\"", construction_db_label)

        # int/ext items
        items = (row.filter(like="EXT_") + row.filter(like="INT_")).dropna()
        for item in [i for i in items if str(i).strip()]:
            assert item in construction_list, rl_missing_item_prompt(rl_path, f"Envelope item \"{item}\"", construction_db_label)
        
        # outages
        outage_type = row["1ST_OUTAGE"]
        assert outage_type in ["HEATING", "COOLING"], rl_misc_prompt(rl_path, "Values in column \"1ST_OUTAGE\" must be either \"HEATING\" or \"COOLING\".")

        date_format = "%d-%b"
        for date in row.filter(like="OUTAGE_"):
            try:
                datetime.strptime(date, date_format)
            except ValueError:
                raise AssertionError(rl_misc_prompt(rl_path, "Outage dates must be in format \"dd-MMM\" (i.e. \"5-Jan\")."))
        outage1_delta = datetime.strptime(row["OUTAGE_1_END"], date_format) - datetime.strptime(row["OUTAGE_1_START"], date_format)
        outage2_delta = datetime.strptime(row["OUTAGE_2_END"], date_format) - datetime.strptime(row["OUTAGE_2_START"], date_format)
        assert outage1_delta.days >= 7, rl_misc_prompt(rl_path, "Outages must be seven days in length.")
        assert outage2_delta.days >= 7, rl_misc_prompt(rl_path, "Outages must be seven days in length.")

        # carbon corrections
        p_carbons = row["PERF_CARBON_MEASURES"]
        np_carbons = row["NON_PERF_CARBON_MEASURES"]
        p_carbons = p_carbons.split(",") if not pd.isna(p_carbons) else []
        np_carbons = np_carbons.split(",") if not pd.isna(np_carbons) else []
        for p, np in zip([p.strip() for p in p_carbons], [np.split() for np in np_carbons]):
            assert p in carbon_list, rl_missing_item_prompt(rl_path, f"Carbon correction measure \"{p}\"", carbon_db_label)
            assert np in np_carbon_list, rl_missing_item_prompt(rl_path, f"Non-performance carbon correction measure \"{np}\"", np_carbon_db_label)

        # country
        country = row["ENVELOPE_COUNTRY"].strip()
        assert country in country_list, rl_missing_item_prompt(rl_path, f"Country \"{country}\"", country_emissions_db_label)

        # grid region
        grid_region = row["GRID_REGION"].strip()
        assert grid_region in grid_regions_list, rl_missing_item_prompt(rl_path, f"Grid region \"{grid_region}\"", hourly_emissions_db_label)

        # foundations
        interfaces = row.filter(like="FOUNDATION_INTERFACE").dropna()
        for interf in [i for i in interfaces if str(i).strip()]:
            choices = ["Slab", "Crawlspace", "Basement"]
            assert interf in choices, rl_misc_prompt(rl_path, f"Entries in \"FOUNDATION_INTERFACE\" columns must be one of {str(choices)}.")
        
        insulations = row.filter(regex=r"^FOUNDATION_INSULATION(?!.*DEPTH).*$").dropna()
        for insu in [i for i in insulations if str(i).strip()]:
            assert insu in materials_list, rl_missing_item_prompt(rl_path, f"Foundation insulation \"{insu}\"", materials_db_label)
        
        # windows
        windows = row.filter(like="EXT_WINDOW").dropna()
        for window in [w[len("WINDOW_"):] for w in windows if str(w).strip()]:
            assert window in window_list, rl_missing_item_prompt(rl_path, f"Window \"{window}\"", window_db_label)
