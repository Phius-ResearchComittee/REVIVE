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
    
    idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
        Name = 'WeatherMorph',
        EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
        Program_Name_1 = 'DBMorph',
        Program_Name_2 = 'DPMorph')
    
    idf.newidfobject('EnergyManagementSystem:Program',
        Name = 'DBMorph',
        Program_Line_1 = 'IF MorphOnOff == 1',
        Program_Line_2 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) + ' + str(MorphFactorDB1) + '*(@Sin (PI*Count/168))',
        Program_Line_3 = 'SET Count2 = Count + 0.25',
        Program_Line_4 = 'ELSEIF MorphOnOff == 2',
        Program_Line_5 = 'SET ODB2 = (@TodayOutDryBulbTemp Hour TimeStepNum) +' + str(MorphFactorDB2) + '*(@Sin (PI*Count/168))',
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
