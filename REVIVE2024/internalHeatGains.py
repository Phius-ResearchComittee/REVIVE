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

def People(idf, occ):

    idf.newidfobject('People',
    Name = 'Zone Occupants',
    Zone_or_ZoneList_Name = 'Zone 1',
    Number_of_People_Schedule_Name = 'OccupantSchedule',
    Number_of_People_Calculation_Method = 'People',
    Number_of_People = occ,
    #,                         !- People per Zone Floor Area
    #,                         !- Zone Floor Area per Person
    #0.3,                      !- Fraction Radiant
    #autocalculate,            !- Sensible Heat Fraction
    Activity_Level_Schedule_Name = 'Occupant_Activity_Schedule',
    Carbon_Dioxide_Generation_Rate = 3.82e-08,
    Enable_ASHRAE_55_Comfort_Warnings = 'No',
    #ZoneAveraged,             !- Mean Radiant Temperature Calculation Type
    #,                         !- Surface NameAngle Factor List Name
    Work_Efficiency_Schedule_Name = 'Occupant_Eff_Schedule',
    Clothing_Insulation_Calculation_Method = 'ClothingInsulationSchedule',
    Clothing_Insulation_Calculation_Method_Schedule_Name = 'Occupant_Clothing_Schedule',
    Clothing_Insulation_Schedule_Name = 'Occupant_Clothing_Schedule',
    Air_Velocity_Schedule_Name = 'AirVelocitySch',
    Thermal_Comfort_Model_1_Type = 'Pierce'
    )

def LightsMELsAppliances(idf, PhiusLights, PhiusMELs, fridge, rangeElec, clothesDryer,clothesWasher,dishWasher):

    idf.newidfobject('Lights',
        Name = 'PhiusLights',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Phius_Lighting',
        Design_Level_Calculation_Method = 'LightingLevel',
        Lighting_Level = PhiusLights,
        Fraction_Radiant = 0.6,
        Fraction_Visible = 0.2,
        EndUse_Subcategory = 'InteriorLights'
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'PhiusMELs',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Phius_MELs',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = PhiusMELs,
        EndUse_Subcategory = 'MELs'
        # Fraction_Radiant = 1,
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'Fridge',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Always_On',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = fridge,
        Fraction_Radiant = 1,
        EndUse_Subcategory = 'Fridge'
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'Range',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BARangeSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = rangeElec,
        Fraction_Latent = 0.3,
        Fraction_Radiant = 0.4,
        EndUse_Subcategory = 'Range'
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'ClothesDryer',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BAClothesDryerSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = clothesDryer,
        Fraction_Latent = 0.05,
        Fraction_Radiant = 0.15,
        EndUse_Subcategory = 'ClothesDryer'
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'ClothesWasher',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BAClothesWasherSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = clothesWasher,
        Fraction_Latent = 0.0,
        Fraction_Radiant = 0.80,
        EndUse_Subcategory = 'ClothesWasher'
        )

    idf.newidfobject('ElectricEquipment',
        Name = 'Dishwasher',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BADishwasherSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = dishWasher,
        Fraction_Latent = 0.15,
        Fraction_Radiant = 0.60,
        EndUse_Subcategory = 'Dishwasher'
        )

    idf.newidfobject('Exterior:Lights',
        Name = 'PhiusExtLight',
        Schedule_Name = 'Always_On',
        Design_Level = 1,
        Control_Option = 'AstronomicalClock')

def SizingLoads(idf, sizingLoadSensible, sizingLoadLatent):
    idf.newidfobject('ElectricEquipment',
        Name = 'SizingSensible',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'SizingLoads',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = sizingLoadSensible)

    idf.newidfobject('ElectricEquipment',
        Name = 'SizingLatent',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'SizingLoads',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = sizingLoadLatent,
        Fraction_Latent = 1.0)

def ThermalMass(idf, icfa_M):

    idf.newidfobject('InternalMass',
        Name = 'Zone1 TM',
        Construction_Name = 'Thermal Mass', 
        Zone_or_ZoneList_Name = 'Zone 1',
        Surface_Area = icfa_M
        )
    
    idf.newidfobject('InternalMass',
        Name = 'Partitions',
        Construction_Name = 'Interior Wall', 
        Zone_or_ZoneList_Name = 'Zone 1',
        Surface_Area = icfa_M
        )