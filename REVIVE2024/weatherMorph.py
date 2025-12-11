# This file contains functions for building envelope building
# Updated 2023.08.23

from pickle import TRUE
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime
import email.utils as eutils
import time
import math
# import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system
import re
import pandas as pd
import numpy as np
import math
import psychrolib


def WeatherMorphSine(idf, outage1start, outage1end, outage2start, outage2end,
                     MorphFactorDB1, MorphFactorDP1, MorphFactorDB2, MorphFactorDP2):
    
    if MorphFactorDB1 != 0:
        Morph1 = 1
    else:
        Morph1 = 0

    if MorphFactorDB2 != 0:
        Morph2 = 2
    else:
        Morph2 = 0


    idf.newidfobject('Schedule:Compact',
        Name = 'Weather Morph',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = ('Through: ' + str(outage1start)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0.0,
        Field_5 = ('Through: ' + str(outage1end)),
        Field_6 = 'For: SummerDesignDay WinterDesignDay',
        Field_7 = 'Until: 24:00',
        Field_8 = 0.0,
        Field_9 = 'For: AllOtherDays',
        Field_10 = 'Until: 24:00',
        Field_11 = Morph1,
        Field_12 = ('Through: ' + str(outage2start)),
        Field_13 = 'For: AllDays',
        Field_14 = 'Until: 24:00',
        Field_15 = 0.0,
        Field_16 = ('Through: ' + str(outage2end)),
        Field_17 = 'For: SummerDesignDay WinterDesignDay',
        Field_18 = 'Until: 24:00',
        Field_19 = 0.0,
        Field_20 = 'For: AllOtherDays',
        Field_21 = 'Until: 24:00',
        Field_22 = Morph2,
        Field_23 = 'Through: 12/31',
        Field_24 = 'For: AllDays',
        Field_25 = 'Until: 24:00',
        Field_26 = 0.0
        )
    
    idf.newidfobject('Schedule:Constant',
        Name = 'Count',
        Schedule_Type_Limits_Name = 'AnyNumber',
        Hourly_Value = 0
        )

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'MorphOnOff',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'Weather Morph',
        OutputVariable_or_OutputMeter_Name = 'Schedule Value')
    
    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'Count',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'Count',
        OutputVariable_or_OutputMeter_Name = 'Schedule Value')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'ODP',
        OutputVariable_or_OutputMeter_Index_Key_Name = '*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Dewpoint Temperature')
        
    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'ODB2',
        Actuated_Component_Unique_Name = 'Environment',
        Actuated_Component_Type = 'Weather Data',
        Actuated_Component_Control_Type = 'Outdoor Dry Bulb')

    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'Count2',
        Actuated_Component_Unique_Name = 'Count',
        Actuated_Component_Type = 'Schedule:Constant',
        Actuated_Component_Control_Type = 'Schedule Value')

    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'ODP2',
        Actuated_Component_Unique_Name = 'Environment',
        Actuated_Component_Type = 'Weather Data',
        Actuated_Component_Control_Type = 'Outdoor Dew Point')
    
    # Classic Morphing Protocol

    # idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
    #     Name = 'WeatherMorph',
    #     EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
    #     Program_Name_1 = 'DBMorph',
    #     Program_Name_2 = 'DPMorph')
    
    # idf.newidfobject('EnergyManagementSystem:Program',
    #     Name = 'DBMorph',
    #     Program_Line_1 = 'IF MorphOnOff == 1',
    #     Program_Line_2 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) + ' + str(MorphFactorDB1) + '*(@Sin (PI*Count/168))',
    #     Program_Line_3 = 'SET Count2 = Count + 0.25',
    #     Program_Line_4 = 'ELSEIF MorphOnOff == 2',
    #     Program_Line_5 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) +' + str(MorphFactorDB2) + '*(@Sin (PI*Count/168))',
    #     Program_Line_6 = 'SET Count2 = Count + 0.25',
    #     Program_Line_7 = 'ELSE',
    #     Program_Line_8 = 'SET ODB2 = Null',
    #     Program_Line_9 = 'SET Count2 = 0',
    #     Program_Line_10 = 'ENDIF',
    #     Program_Line_11 = 'RETURN')

    # idf.newidfobject('EnergyManagementSystem:Program',
    #     Name = 'DPMorph',
    #     Program_Line_1 = 'IF MorphOnOff == 1',
    #     Program_Line_2 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) + ' + str(MorphFactorDP1) + '*(@Sin (PI*Count/168))',
    #     Program_Line_3 = 'SET Count2 = Count + 0.25',
    #     Program_Line_4 = 'ELSEIF MorphOnOff == 2',
    #     Program_Line_5 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) +' + str(MorphFactorDP2) + '*(@Sin (PI*Count/168))',
    #     Program_Line_6 = 'SET Count2 = Count + 0.25',
    #     Program_Line_7 = 'ELSE',
    #     Program_Line_8 = 'SET ODP2 = Null',
    #     Program_Line_9 = 'SET Count2 = 0',
    #     Program_Line_10 = 'ENDIF',
    #     Program_Line_11 = 'RETURN')
    
    # Peaked Morphing Protocol

    idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
        Name = 'WeatherMorph',
        EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
        Program_Name_1 = 'DBMorph',
        Program_Name_2 = 'DPMorph')
    
    idf.newidfobject('EnergyManagementSystem:Program',
        Name = 'DBMorph',
        Program_Line_1 = 'IF MorphOnOff == 1',
        Program_Line_2 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) + ' + str(MorphFactorDB1) + '*(2 * @Sin (PI*Count/168))',
        Program_Line_3 = 'SET Count2 = Count + 0.25',
        Program_Line_4 = 'ELSEIF MorphOnOff == 2',
        Program_Line_5 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) +' + str(MorphFactorDB2) + '*(2 * @Sin (PI*Count/168))',
        Program_Line_6 = 'SET Count2 = Count + 0.25',
        Program_Line_7 = 'ELSE',
        Program_Line_8 = 'SET ODB2 = Null',
        Program_Line_9 = 'SET Count2 = 0',
        Program_Line_10 = 'ENDIF',
        Program_Line_11 = 'RETURN')

    idf.newidfobject('EnergyManagementSystem:Program',
        Name = 'DPMorph',
        Program_Line_1 = 'IF MorphOnOff == 1',
        Program_Line_2 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) + ' + str(MorphFactorDP1) + '*(@Sin (PI*Count/168))',
        Program_Line_3 = 'SET Count2 = Count + 0.25',
        Program_Line_4 = 'ELSEIF MorphOnOff == 2',
        Program_Line_5 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) +' + str(MorphFactorDP2) + '*(@Sin (PI*Count/168))',
        Program_Line_6 = 'SET Count2 = Count + 0.25',
        Program_Line_7 = 'ELSE',
        Program_Line_8 = 'SET ODP2 = Null',
        Program_Line_9 = 'SET Count2 = 0',
        Program_Line_10 = 'ENDIF',
        Program_Line_11 = 'RETURN')
    
    # Peaked Morphing Protocol with constant RH

    # idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
    #     Name = 'WeatherMorph',
    #     EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
    #     Program_Name_1 = 'DBMorph',
    #     Program_Name_2 = 'DPMorph')
    
    # idf.newidfobject('EnergyManagementSystem:Program',
    #     Name = 'DBMorph',
    #     Program_Line_1 = 'IF MorphOnOff == 1',
    #     Program_Line_2 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) + ' + str(MorphFactorDB1) + '*(2 * @Sin (PI*Count/168))',
    #     Program_Line_3 = 'SET Count2 = Count + 0.25',
    #     Program_Line_4 = 'ELSEIF MorphOnOff == 2',
    #     Program_Line_5 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) +' + str(MorphFactorDB2) + '*(2 * @Sin (PI*Count/168))',
    #     Program_Line_6 = 'SET Count2 = Count + 0.25',
    #     Program_Line_7 = 'ELSE',
    #     Program_Line_8 = 'SET ODB2 = Null',
    #     Program_Line_9 = 'SET Count2 = 0',
    #     Program_Line_10 = 'ENDIF',
    #     Program_Line_11 = 'RETURN')

    # idf.newidfobject('EnergyManagementSystem:Program',
    #     Name = 'DPMorph',
    #     Program_Line_1 = 'IF MorphOnOff == 1',
    #     Program_Line_2 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) + ' + str(MorphFactorDP1) + '*(@Sin (PI*Count/168))',
    #     Program_Line_2 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) + ' + str(MorphFactorDB1) + '*(2 * @Sin (PI*Count/168))',
    #     Program_Line_3 = 'SET Count2 = Count + 0.25',
    #     Program_Line_4 = 'ELSEIF MorphOnOff == 2',
    #     Program_Line_5 = 'SET ODP2 = (@TodayOutDewPointTemp Hour TimeStepNum) +' + str(MorphFactorDP2) + '*(@Sin (PI*Count/168))',
    #     Program_Line_6 = 'SET Count2 = Count + 0.25',
    #     Program_Line_7 = 'ELSE',
    #     Program_Line_8 = 'SET ODP2 = Null',
    #     Program_Line_9 = 'SET Count2 = 0',
    #     Program_Line_10 = 'ENDIF',
    #     Program_Line_11 = 'RETURN')
    

        

def ComputeWeatherMorphFactors(epw_csv, summer_outage_start, winter_outage_start, elevation,
                               summer_treturn_wb, summer_treturn_db, winter_treturn_wb, winter_treturn_db):
    
    psychrolib.SetUnitSystem(psychrolib.SI)

    pressure = psychrolib.GetStandardAtmPressure(elevation)

    summer_treturn_dp = psychrolib.GetTDewPointFromTWetBulb(summer_treturn_db, summer_treturn_wb, pressure)
    winter_treturn_dp = psychrolib.GetTDewPointFromTWetBulb(winter_treturn_db, winter_treturn_wb, pressure)

    # count how many lines of header using regex
    with open(epw_csv, "r") as fp:
        pattern = r"Date.*\nDate.*\n"
        all_content = fp.read()
        split_set = re.split(pattern, all_content)
        num_preceding_lines = len(str(split_set[0]).splitlines())+1

    # load in the dataframe skipping the header rows
    print(f"Skipping {num_preceding_lines} rows...")
    df = pd.read_csv(epw_csv, skiprows=num_preceding_lines, encoding="latin1")

    # strip arbitrary year from date format
    df["Date"] = df["Date"].str[5:]

    # assign date/hour to multiindex
    df = df.set_index(['Date', 'HH:MM'])
    df.index = df.index.set_levels([
        pd.to_datetime(df.index.levels[0], format="%m/%d").strftime("%m/%d"), # to properly zero-pad the date
        df.index.levels[1]])
    df = df.sort_index()

    # get db and dp data for all time
    morph_df = df[["Dry Bulb Temperature {C}","Dew Point Temperature {C}"]]

    # construct date ranges
    # TODO: CHECK FOR WRAP AROUND YEARS
    summer_outage_start = pd.to_datetime(summer_outage_start, format="%d-%b")
    summer_outage_dates = [(summer_outage_start + pd.Timedelta(days=n)).strftime("%m/%d") for n in range(7)]
    winter_outage_start = pd.to_datetime(winter_outage_start, format="%d-%b")
    winter_outage_dates = [(winter_outage_start + pd.Timedelta(days=n)).strftime("%m/%d") for n in range(7)]

    # select new dataframes for date range
    summer_outage_df = morph_df.loc[morph_df.index.get_level_values(0).isin(summer_outage_dates)]
    winter_outage_df = morph_df.loc[morph_df.index.get_level_values(0).isin(winter_outage_dates)]

    # establish dataframes are correct
    num_outage_hours = 168
    assert len(summer_outage_df)==num_outage_hours, f"Summer outage should be of length {num_outage_hours} hours. Received {len(summer_outage_df)} hours."
    assert len(winter_outage_df)==num_outage_hours, f"Winter outage should be of length {num_outage_hours} hours. Received {len(winter_outage_df)} hours."

    # compute the phase adjustment for every hour
    phase_adj = [math.pi * h / num_outage_hours for h in range(num_outage_hours)]

    # compute the iteratively morphed week and return delta
    def iterative_delta(t_return, tx_week, x_fn):
        """
        t_return: n-year return extreme values of db or dewpoint
        tw_week: original hourly db or dewpoint values from outage week
        x_fn: function to apply to morphed week - max for summer and min for winter
        """
        # iterative constants
        k_relax = 0.1
        tolerance = 0.01
        
        # initial values
        delta = t_return - (sum(tx_week)/len(tx_week))
        morphed_week = tx_week + delta*np.sin(phase_adj)
        x = x_fn(morphed_week)

        # perform the iterative calculation
        counter = 0
        while abs(t_return - x) >= tolerance:
            if counter >= 100:
                print("Max iterations reached!")
                break
            counter += 1
            delta += k_relax * (t_return - x)
            morphed_week = tx_week + delta*np.sin(phase_adj)
            x = x_fn(morphed_week)

        # report iterative stats and return the computed delta
        print(f"Final iteration count: {counter} iterations")
        return delta


    summer_db_factor = iterative_delta(
        summer_treturn_db,
        summer_outage_df["Dry Bulb Temperature {C}"],
        max)

    summer_dp_factor = iterative_delta(
        summer_treturn_dp, 
        summer_outage_df["Dew Point Temperature {C}"], 
        max)

    winter_db_factor = iterative_delta(
        winter_treturn_db,
        winter_outage_df["Dry Bulb Temperature {C}"],
        min)

    winter_dp_factor = iterative_delta(
        winter_treturn_dp, 
        winter_outage_df["Dew Point Temperature {C}"], 
        min)
    
    return round(summer_db_factor,2), round(summer_dp_factor,2), round(winter_db_factor,2), round(winter_dp_factor, 2)
