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

def Version(idf):

    idf.newidfobject('Version',
        Version_Identifier = 9.5
        )

def SimulationControl(idf):
    idf.newidfobject('SimulationControl',
        Do_Zone_Sizing_Calculation = 'Yes',
        Do_System_Sizing_Calculation = 'Yes',
        Do_Plant_Sizing_Calculation = 'No',
        Run_Simulation_for_Sizing_Periods = 'Yes',
        Run_Simulation_for_Weather_File_Run_Periods = 'Yes',
        Do_HVAC_Sizing_Simulation_for_Sizing_Periods = 'Yes',
        Maximum_Number_of_HVAC_Sizing_Simulation_Passes = 25
        )
    
def Building(idf,fileName):

    idf.newidfobject('Building',
        Name = str(fileName),
        North_Axis = 0,
        Terrain = 'City',
        Loads_Convergence_Tolerance_Value = 0.04,
        Temperature_Convergence_Tolerance_Value = 0.4,
        Solar_Distribution = 'FullInteriorAndExterior', 
        Maximum_Number_of_Warmup_Days = 25,
        Minimum_Number_of_Warmup_Days = 6
        )

def CO2Balance(idf):

    idf.newidfobject('ZoneAirContaminantBalance',
        Carbon_Dioxide_Concentration = 'Yes',
        Outdoor_Carbon_Dioxide_Schedule_Name = 'CO2_Schedule',
        Generic_Contaminant_Concentration = 'No'
        )
    
def Timestep(idf):

    idf.newidfobject('Timestep',
        Number_of_Timesteps_per_Hour = 4
        )

def RunPeriod(idf):
    idf.newidfobject('RunPeriod',
        Name = 'Annual',
        Begin_Month = 1,
        Begin_Day_of_Month = 1,
        #Begin_Year
        End_Month  = 12,
        End_Day_of_Month = 31,
        #,                         !- End Year
        #,                         !- Day of Week for Start Day
        Use_Weather_File_Holidays_and_Special_Days = 'Yes',
        Use_Weather_File_Daylight_Saving_Period = 'Yes',
        Apply_Weekend_Holiday_Rule = 'No',
        Use_Weather_File_Rain_Indicators = 'Yes',
        Use_Weather_File_Snow_Indicators = 'Yes',
        Treat_Weather_as_Actual = 'No'
        )
    
def GeometryRules(idf):

    idf.newidfobject('GlobalGeometryRules',
        Starting_Vertex_Position = 'UpperLeftCorner',
        Vertex_Entry_Direction = 'Counterclockwise',
        Coordinate_System = 'Relative'
        )