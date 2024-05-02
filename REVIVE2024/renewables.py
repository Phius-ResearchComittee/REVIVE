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

def Renewables(idf, ZoneName, PV_SIZE, PV_TILT):

    idf.newidfobject('DemandManagerAssignmentList',
        Name = 'Demand Limiting',
        Meter_Name = 'ElectricityNet:Facility',
        Demand_Limit_Schedule_Name = 'Always Off',
        Demand_Limit_Safety_Fraction = 0.95,
        # Billing_Period_Schedule_Name = ,
        # Peak_Period_Schedule_Name = ,
        Demand_Window_Length = 10,
        Demand_Manager_Priority = 'All', 
        DemandManager_1_Object_Type = 'DemandManager:Thermostats',
        DemandManager_1_Name = 'Set backs') 

    idf.newidfobject('DemandManager:Thermostats',
        Name = 'Set Backs',
        Availability_Schedule_Name = 'Demand Control Cooling', 
        Reset_Control = 'Fixed',
        Minimum_Reset_Duration = 30,
        Maximum_Heating_Setpoint_Reset = 20,
        Maximum_Cooling_Setpoint_Reset = 27,
        # Reset_Step_Change = ,
        Selection_Control = 'All',
        # Rotation_Duration = ,
        Thermostat_1_Name = 'Zone_1_Thermostat')

    idf.newidfobject('Generator:PVWatts',
        Name = 'PV Array',
        PVWatts_Version = 5,
        DC_System_Capacity = PV_SIZE,
        Module_Type = 'Standard',
        Array_Type = 'FixedOpenRack',
        System_Losses = 0.14,
        Array_Geometry_Type = 'TiltAzimuth',
        Tilt_Angle = PV_TILT,
        Azimuth_Angle = 180,
        # Surface_Name = ,
        Ground_Coverage_Ratio = 0.4)

    idf.newidfobject('ElectricLoadCenter:Inverter:PVWatts',
        Name = 'PV Inverter',
        DC_to_AC_Size_Ratio = 1.1,
        Inverter_Efficiency = 0.96)

    idf.newidfobject('ElectricLoadCenter:Generators',
        Name = 'PV',
        Generator_1_Name = 'PV Array',
        Generator_1_Object_Type = 'Generator:PVWatts',
        Generator_1_Rated_Electric_Power_Output = 3000,
        Generator_1_Availability_Schedule_Name = 'Always_On')
        # Generator_1_Rated_Thermal_to_Electrical_Power_Ratio = )

    idf.newidfobject('ElectricLoadCenter:Storage:Simple',
        Name = 'Simple Battery',
        Availability_Schedule_Name = 'Always_On',
        Zone_Name = str(ZoneName),
        Radiative_Fraction_for_Zone_Heat_Gains = 0.9,
        Nominal_Energetic_Efficiency_for_Charging = 0.9,
        Nominal_Discharging_Energetic_Efficiency = 0.9,
        Maximum_Storage_Capacity = 10800000,
        # Maximum_Power_for_Discharging = ,
        # Maximum_Power_for_Charging = ,
        Initial_State_of_Charge = 10800000)

    idf.newidfobject('ElectricLoadCenter:Transformer',
        Name = 'Transformer',
        Availability_Schedule_Name = 'Always_On',
        Transformer_Usage = 'LoadCenterPowerConditioning',
        Zone_Name = str(ZoneName),
        # Radiative_Fraction = ,
        # Rated_Capacity = ,
        Phase = 3,
        Conductor_Material = 'Aluminum',
        Full_Load_Temperature_Rise = 150,
        Fraction_of_Eddy_Current_Losses = 0.1,
        Performance_Input_Method = 'RatedLosses',
        # Rated_No_Load_Loss = ,
        # Rated_Load_Loss = ,
        Nameplate_Efficiency = 0.98,
        Per_Unit_Load_for_Nameplate_Efficiency = 0.35,
        Reference_Temperature_for_Nameplate_Efficiency = 75,
        # Per_Unit_Load_for_Maximum_Efficiency = ,
        Consider_Transformer_Loss_for_Utility_Cost = 'Yes')

    idf.newidfobject('ElectricLoadCenter:Distribution',
        Name = 'ELC',
        Generator_List_Name = 'PV',
        Generator_Operation_Scheme_Type = 'Baseload',
        Generator_Demand_Limit_Scheme_Purchased_Electric_Demand_Limit = 0,
        # Generator_Track_Schedule_Name_Scheme_Schedule_Name = ,
        # Generator_Track_Meter_Scheme_Meter_Name = ,
        Electrical_Buss_Type = 'AlternatingCurrentWithStorage',
        Inverter_Name = 'PV Inverter',
        Electrical_Storage_Object_Name = 'Simple Battery',
        # Transformer_Object_Name = ,
        Storage_Operation_Scheme = 'FacilityDemandLeveling',
        Storage_Control_Track_Meter_Name = 'ElectricityNet:Facility',
        Storage_Converter_Object_Name = 'Converter',
        Maximum_Storage_State_of_Charge_Fraction = 1,
        Minimum_Storage_State_of_Charge_Fraction = 0.2,
        # Design_Storage_Control_Charge_Power = ,
        # Storage_Charge_Power_Fraction_Schedule_Name = ,
        # Design_Storage_Control_Discharge_Power = ,
        # Storage_Discharge_Power_Fraction_Schedule_Name = ,
        Storage_Control_Utility_Demand_Target = 3500,
        Storage_Control_Utility_Demand_Target_Fraction_Schedule_Name = 'OutageCooling')

    idf.newidfobject('ElectricLoadCenter:Storage:Converter',
        Name = 'Converter',
        Availability_Schedule_Name = 'Always_On',
        Power_Conversion_Efficiency_Method = 'SimpleFixed',
        Simple_Fixed_Efficiency = 0.95)