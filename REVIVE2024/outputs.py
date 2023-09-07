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
import PySimpleGUI as sg
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system

def SimulationOutputs(idf):

    idf.newidfobject('Output:VariableDictionary',
        Key_Field = 'IDF')

    idf.newidfobject('Output:Table:SummaryReports',
        Report_1_Name = 'AllSummary')

    idf.newidfobject('Output:Table:TimeBins',
        Key_Value = '*',
        Variable_Name = 'Zone Air Temperature',
        Interval_Start = -40,
        Interval_Size = 42,
        Interval_Count = 1,
        Variable_Type = 'Temperature'
        )

    idf.newidfobject('OutputControl:Table:Style',
        Column_Separator = 'HTML',
        Unit_Conversion = 'InchPound'
        )

    idf.newidfobject('Output:SQLite',
        Option_Type = 'SimpleAndTabular',
        Unit_Conversion_for_Tabular_Data = 'InchPound'
        )

    outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature', 'Exterior Lights Electricity Energy', 
                'Zone Ventilation Mass Flow Rate', 'Schedule Value', 'Electric Equipment Electricity Energy',
                'Facility Total Purchased Electricity Energy']
    meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity', 'ElectricityNet:Facility',
                'NaturalGas:Facility'] 
    for x in outputVars:
        idf.newidfobject('Output:Variable',
        Key_Value = '*',
        Variable_Name = str(x),
        Reporting_Frequency = 'hourly'
        )

    for x in meterVars:
        idf.newidfobject('Output:Meter:MeterFileOnly',
        Key_Name = str(x),
        Reporting_Frequency = 'Monthly'
        )
