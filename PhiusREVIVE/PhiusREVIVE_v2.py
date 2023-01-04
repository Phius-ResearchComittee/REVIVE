#=============================================================================================================================
# PhiusREVIVE Program Tool
# Updated 2022/12/13
# v22.1.2
#
#

# Copyright (c) 2022 Phius

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#==============================================================================================================================
# Outline
# 1. Dependencies
# 2. Simple GUI Setup

#==============================================================================================================================
# 1. Set up dependencies
#==============================================================================================================================

from pickle import TRUE
from this import d
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime as dt
import email.utils as eutils
import time
import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
# import PySimpleGUI as sg
from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system

import pprint
pp = pprint.PrettyPrinter()


#==============================================================================================================================
# 2.0 Function Definitions
#==============================================================================================================================


# This function builds E+ contstructions from different layers: 
def constructionBuilder(constructionName, constructionLayers):
    params = [x for x in constructionLayers]
    layers = {}
    count = 0
    for i,param in enumerate(params):
        count = count + 1
        layers['Layer_' + str(count)] = param

    layers.pop('Layer_1')
    idf1.newidfobject('Construction',
    Name = str(constructionName),
    Outside_Layer = str(constructionLayers[0]),
    **layers)

# This function creates a compact schedule from an hourly list of values: 
def hourSch(nameSch, hourlyValues):
    params = [x for x in hourlyValues]
    schValues = {}
    count = 2
    for i,param in enumerate(params):
        count = count + 1
        schValues['Field_' + str(count)] = ('Until: ' + str(i + 1) + ':00')
        count = count + 1
        schValues['Field_' + str(count)] = param
    idf1.newidfobject('Schedule:Compact',
    Name = str(nameSch),
    Schedule_Type_Limits_Name = 'Fraction',
    Field_1 = 'Through: 12/31',
    Field_2 = 'For: AllDays',
    **schValues)

# Not sure of the purposed of this one completely - AM to check 
def zeroSch(nameSch):
    idf1.newidfobject('Schedule:Compact',
        Name = str(nameSch),
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = 'For: AllOtherDays',
        Field_6 = 'Until: 24:00',
        Field_7 = 0
    ) 

#==============================================================================================================================
# 3.0 Option Databasing
#==============================================================================================================================

values = {}
envelopeOptions = ('Brick Wall', 'Ext_Door1', 'Thermal_Mass', 'Interior_Floor', 'Exterior_Slab_UnIns', 
    'Exterior_Slab_+_2in_EPS', 'Exterior_Wall', 'Interior_Wall', 'Exterior_Roof', 'Exterior_Door', 'Interior_Door', 'Exterior_Wall_+1in_EPS', 
    'Exterior_Wall_+1.625in_EPS', 'Exterior_Wall_+2in_EPS', 'Exterior_Wall_+4in_EPS', 'Exterior_Wall_+7.5in_EPS', 'Exterior_Wall_+6in_EPS', 
    'Exterior_Wall_+9in_EPS', 'Exterior_Wall_+14in_EPS', 'Exterior_Roof_R-30', 'Exterior_Roof_R-38', 'Exterior_Roof_R-49', 
    'Exterior_Roof_R-55', 'Exterior_Roof_R-60', 'Exterior_Roof_R-75', 'Exterior_Roof_R-100', 'P+B_UnIns', 'P+B_R-13', 'P+B_R-19', 
    'P+B_R-30', 'P+B_R-38', 'P+B_R-49')
mechOptions = ('PTHP', 'Furnace with DX Cooling')

#==============================================================================================================================
# 4.0 Streamlit
#==============================================================================================================================

image = Image.open('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/al_REVIVE_PILOT_logo.png')

st.set_page_config(
    page_title="PhiusREVIVE",
    page_icon="C:/Users/amitc/Documents/GitHub/Phius-REVIVE/Project Program/PhiusREVIVE/Phius-Logo-RGB__Color_Icon.ico",
    layout="wide",
    )
    
st.image(image) #, width=5)
st.title('Phius REVIVE Pilot Tool v2')

tab1, tab6, tab2, tab5, tab4, tab3 = st.tabs(['Linked Files', 'Simulation Control', 'Envelope Inputs', 'Internal Gain Inputs', 'Mechanical Inputs', 'Results'])

with st.form('Model Inputs'):
    run = st.form_submit_button('Run Analysis')
    with tab1:
        st.header('Linked Files')
        values['iddFile'] = st.text_input('IDD File Location', 'C:/EnergyPlusV9-5-0/Energy+.idd')
        values['StudyFolder'] = st.text_input('Study Folder Location', 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/test1')
        values['GEO'] =  st.text_input('Select IDF With Building Geometry', 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/PNNL_SF_Geometry.idf')
        values['DDY'] = st.text_input('Select DDY Location', 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/USA_IL_Chicago-Midway.AP.725340_TMY3.ddy')
        values['EPW'] = st.text_input('Select EPW File Location','C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/USA_IL_Chicago-Midway.AP.725340_TMY3.epw')
    with tab6:
        st.header('Simulation Control')
        values['BaseFileName'] = st.text_input('Test File Name','test3')
        controls1, controls2 = st.columns(2)
        with controls1:
            st.subheader('Outage 1')
            outage1start = st.date_input('Outage 1 Start', value=dt.date(2022,1,23)).strftime('%m/%d')    
            outage1end = st.date_input('Outage 1 End', value=dt.date(2022,2,5)).strftime('%m/%d')
        with controls2:
            st.subheader('Outage 2')
            outage2start = st.date_input('Outage 2 Start', value=dt.date(2022,7,23)).strftime('%m/%d')
            outage2end = st.date_input('Outage 2 End', value=dt.date(2022,8,5)).strftime('%m/%d')
    with tab2:
        st.header('Envelope Inputs')
        values['Occupants'] = st.number_input('Number of Occupants (# of Bedrooms + 1)', value=4)
        values['ICFA'] = st.number_input('ICFA [sf]',min_value=1, value=2128)
        values['PartitionRatio'] = st.number_input('Parition to ICFA Ratio', value = 1.0)
        st.subheader('Envelope Details')
        
        envelope1, envelope2 = st.columns(2)
        with envelope1:
            st.subheader('Baseline Case')
            Ext_Wall1_base = st.selectbox('Set Baseline Ext Wall 1', envelopeOptions)
            Ext_Roof1_base = st.selectbox('Set Baseline Ext Roof 1', envelopeOptions)
            Ext_Floor1_base = st.selectbox('Set Baseline Ext Floor 1', envelopeOptions)
            Ext_Door1_base = 'Ext_Door1'
            Ext_Window1_Base_Ufactor = (st.number_input('Set Baseline Ext Window 1 U-Factor', value=0.5))*5.678263337
            Ext_Window1_Base_SHGC = (st.number_input('Set Baseline Ext Window 1 SHGC', value=0.35))
            flowCoefficient = (st.number_input('Flow Coefficient Baseline', value=88.075, format= '%f') / 2118.87997275968)
            Int_Floor1 = 'Interior_Floor'
        with envelope2:
            st.subheader('Proposed Case')
            Ext_Wall1_prop = st.selectbox('Set Proposed Ext Wall 1', envelopeOptions)
            Ext_Roof1_prop = st.selectbox('Set Proposed Ext Roof 1', envelopeOptions)
            Ext_Floor1_prop = st.selectbox('Set Proposed Ext Floor 1', envelopeOptions)
            Ext_Window1_prop_Ufactor = (st.number_input('Set Proposed Ext Window 1 U-Factor', value=0.5))*5.678263337
            Ext_Window1_prop_SHGC = (st.number_input('Set Proposed Ext Window 1 SHGC', value=0.35))
            flowCoefficient_prop = (st.number_input('Flow Coefficient Proposed', value=20.125, format= '%f') / 2118.87997275968)
            Ext_Door1_prop = 'Brick Wall'
            Ext_Window1_prop = 'Brick Window'
    with tab5:
        st.header('Internal Heat Gains')
        ihg1, ihg2 = st.columns(2)
        with ihg1:
            fridge_base = st.number_input('Enter baseline refridgerator [kWh/yr]', value=445)
        with ihg2:
            fridge_prop = st.number_input('Enter proposed refridgerator [kWh/yr]', value=445)
    with tab4:
        st.header('Mechanical Inputs')
        mech1, mech2 = st.columns(2)

        with mech1:
            Mech_base = st.selectbox('Set baseline mechanical system', mechOptions)
            if Mech_base == 'PTHP':
                PTHP_HeatingCOP_base = st.number_input('Baseline nominal heating COP', 3.0, format= '%f')
                PTHP_CoolingCOP_base = st.number_input('Baseline cooling COP', 3.0, format= '%f')
        with mech2:
            Mech_prop = st.selectbox('Set proposed mechanical system', mechOptions)
            if Mech_prop == 'PTHP':
                PTHP_HeatingCOP_prop = st.number_input('Proposed nominal heating COP', value=3.0, format= '%f')
                PTHP_CoolingCOP_prop = st.number_input('Proposed nominal cooling COP', value=3.0, format= '%f')

    st.write('#### Simulation Progress:')
    prog_bar = st.progress(0)

    if run:
        iddfile = str(values['iddFile'])
        IDF.setiddname(iddfile)
        #==============================================================================================================================
        # 5.i Testing inputs
        #==============================================================================================================================
        BaseFileName = values['BaseFileName']
        studyFolder = values['StudyFolder']
        epwfile = str(values['EPW'])
        idfgName = str(values['GEO'])
        ddyName = values['DDY']
        fname2 = str(studyFolder) + "/"  + str(BaseFileName) + ".idf"

        os.chdir(str(studyFolder))

        icfa = values['ICFA']
        Nbr = (float(values['Occupants']) -1)
        operableArea_N = 1
        operableArea_S = 1
        operableArea_W = 1
        operableArea_E = 1
        halfHeight = 1.524
        ervSense = 0.75
        ervLatent = 0.4
        fridge = (445/(365*24)) # always on design load
        fracHighEff = 1.0
        PhiusLights = ((2 + 0.8 * (4 - 3 * fracHighEff / 3.7)*(455 + 0.8 * icfa) * 0.8) / 365) #power per day W use Phius calc
        PhiusMELs = (413 + 69*Nbr + 0.91*icfa)/365 #consumption per day per phius calc
        occ = values['Occupants']
        icfa = (float(values['ICFA'])/10.76391)
        PartitionRatio = float(values['PartitionRatio'])

        testingFile = str(studyFolder) + "/" + str(BaseFileName) + ".idf"
        testingFile_BA = str(studyFolder) + "/" + str(BaseFileName) + "_BA.idf"
        testingFile_BR = str(studyFolder) + "/" + str(BaseFileName) + "_BR.idf"
        testingFile_PA = str(studyFolder) + "/" + str(BaseFileName) + "_PA.idf"
        testingFile_PR = str(studyFolder) + "/" + str(BaseFileName) + "_PR.idf"

        open(str(testingFile_BA), 'w')
        idfg = IDF(str(idfgName))
        ddy = IDF(ddyName)
        idf1 = IDF(str(testingFile_BA))
        windowNames = []

        #==============================================================================================================================
        # 6. Importing from geometry file
        #==============================================================================================================================

        for zone in idfg.idfobjects['Zone']:
            idf1.copyidfobject(zone)

        for srf in idfg.idfobjects['BuildingSurface:Detailed']:
            idf1.copyidfobject(srf)

        count = -1
        for fen in idfg.idfobjects['FenestrationSurface:Detailed']:
            idf1.copyidfobject(fen)
            count += 1
            windows = idf1.idfobjects['FenestrationSurface:Detailed'][count]
            if windows.Surface_Type == 'Window':
                windowNames.append(windows.Name)

        # site shading

        for site in idfg.idfobjects['Shading:Site:Detailed']:
            idf1.copyidfobject(site)

        for bldg in idfg.idfobjects['Shading:Building:Detailed']:
            idf1.copyidfobject(bldg)

        # sizing data

        for bldg in ddy.idfobjects['SizingPeriod:DesignDay']:
            idf1.copyidfobject(bldg)

        zone = idf1.idfobjects['Zone'][0]
        zone.Floor_Area = (icfa) # * 0.09290304)

        idf1.saveas(str(testingFile))

        #==============================================================================================================================
        # 4. Build Base IDF
        #==============================================================================================================================

        # High level model information 
        idf1.newidfobject('Version',
            Version_Identifier = 9.5
            )

        idf1.newidfobject('SimulationControl',
            Do_Zone_Sizing_Calculation = 'Yes',
            Do_System_Sizing_Calculation = 'Yes',
            Do_Plant_Sizing_Calculation = 'No',
            Run_Simulation_for_Sizing_Periods = 'No',
            Run_Simulation_for_Weather_File_Run_Periods = 'Yes',
            Do_HVAC_Sizing_Simulation_for_Sizing_Periods = 'Yes',
            Maximum_Number_of_HVAC_Sizing_Simulation_Passes = 25
            )

        idf1.newidfobject('Building',
            Name = str(BaseFileName),
            North_Axis = 0,
            Terrain = 'City',
            Loads_Convergence_Tolerance_Value = 0.04,
            Temperature_Convergence_Tolerance_Value = 0.4,
            Solar_Distribution = 'FullInteriorAndExterior', 
            Maximum_Number_of_Warmup_Days = 25,
            Minimum_Number_of_Warmup_Days = 6
            )

        idf1.newidfobject('ZoneAirContaminantBalance',
            Carbon_Dioxide_Concentration = 'Yes',
            Outdoor_Carbon_Dioxide_Schedule_Name = 'CO2_Schedule',
            Generic_Contaminant_Concentration = 'No'
            )

        idf1.newidfobject('Timestep',
            Number_of_Timesteps_per_Hour = 4
            )

        idf1.newidfobject('RunPeriod',
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

        idf1.newidfobject('GlobalGeometryRules',
            Starting_Vertex_Position = 'UpperLeftCorner',
            Vertex_Entry_Direction = 'Counterclockwise',
            Coordinate_System = 'Relative'
            )

        #IHG

        idf1.newidfobject('People',
            Name = 'Zone Occupants',
            Zone_or_ZoneList_Name = 'Zone 1',
            Number_of_People_Schedule_Name = 'OUTAGE:Occupant_Schedule',
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
        #Need Phius Calcs for next few objects
        idf1.newidfobject('Lights',
            Name = 'PhiusLights',
            Zone_or_ZoneList_Name = 'Zone 1',
            Schedule_Name = 'Phius_Lighting',
            Design_Level_Calculation_Method = 'LightingLevel',
            Lighting_Level = PhiusLights,
            Fraction_Radiant = 0.6,
            Fraction_Visible = 0.2
            )

        idf1.newidfobject('ElectricEquipment',
            Name = 'Fridge',
            Zone_or_ZoneList_Name = 'Zone 1',
            Schedule_Name = 'Always_On',
            Design_Level_Calculation_Method = 'EquipmentLevel',
            Design_Level = fridge,
            Fraction_Radiant = 1,
            )

        idf1.newidfobject('ElectricEquipment',
            Name = 'PhiusMELs',
            Zone_or_ZoneList_Name = 'Zone 1',
            Schedule_Name = 'Always_On',
            Design_Level_Calculation_Method = 'EquipmentLevel',
            Design_Level = 100,
            Fraction_Radiant = 0.5,
            )

        idf1.newidfobject('ZoneInfiltration:FlowCoefficient',
            Name = 'Zone_Infiltration',
            Zone_Name = 'Zone 1',
            Schedule_Name = 'Always_On',
            Flow_Coefficient = flowCoefficient,
            Stack_Coefficient = 0.078,
            Wind_Coefficient = 0.17,
            Shelter_Factor = 0.9
            )

        #add ext lights below
        idf1.newidfobject('Exterior:Lights',
            Name = 'PhiusExtLight',
            Schedule_Name = 'Always_On',
            Design_Level = 1,
            Control_Option = 'AstronomicalClock')
        
        ##Constructions and materials
        ##Import from a library for future testing??

        # Thermal mass
        
        # FurnitureMass = idf1.idfobjects['InternalMass'][0]
        # FurnitureMass.Surface_Area = icfa
        # PartitionMass = idf1.idfobjects['InternalMass'][1]
        # PartitionMass.Surface_Area = (icfa * PartitionRatio)
        
        #basic materials
        idf1.newidfobject('Material',
            Name = 'M01_100mm_brick',
            Roughness = 'MediumRough',
            Thickness = 0.1016,
            Conductivity = 0.89,
            Density = 1920,
            Specific_Heat = 790
            )

        idf1.newidfobject('Material',
            Name = 'G05_25mm_wood',
            Roughness = 'MediumSmooth',
            Thickness = 0.0254,
            Conductivity = 0.15,
            Density = 608,
            Specific_Heat = 1630
            )

        idf1.newidfobject('Material',
            Name = 'F08_Metal_surface',
            Roughness = 'Smooth',
            Thickness = 0.0008,
            Conductivity = 45.28,
            Density = 7824,
            Specific_Heat = 500
            )

        idf1.newidfobject('Material',
            Name = 'I01_25mm_insulation_board',
            Roughness = 'MediumRough',
            Thickness = 0.0254,
            Conductivity = 0.03,
            Density = 43,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'I02_50mm_insulation_board',
            Roughness = 'MediumRough',
            Thickness = 0.0508,
            Conductivity = 0.03,
            Density = 43,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'G01a_19mm_gypsum_board',
            Roughness = 'MediumSmooth',
            Thickness = 0.019,
            Conductivity = 0.16,
            Density = 800,
            Specific_Heat = 1090
            )

        idf1.newidfobject('Material',
            Name = 'M11_100mm_lightweight_concrete',
            Roughness = 'MediumRough',
            Thickness = 0.1016,
            Conductivity = 0.53,
            Density = 1280,
            Specific_Heat = 840
            )

        idf1.newidfobject('Material',
            Name = 'F16_Acoustic_tile',
            Roughness = 'MediumSmooth',
            Thickness = 0.0191,
            Conductivity = 0.06,
            Density = 368,
            Specific_Heat = 590
            )

        idf1.newidfobject('Material',
            Name = 'M15_200mm_heavyweight_concrete',
            Roughness = 'MediumRough',
            Thickness = 0.2032,
            Conductivity = 1.95,
            Density = 2240,
            Specific_Heat = 900
            )

        idf1.newidfobject('Material',
            Name = 'M05_200mm_concrete_block',
            Roughness = 'MediumRough',
            Thickness = 0.1016,
            Conductivity = 1.11,
            Density = 800,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'Mass_wood',
            Roughness = 'MediumSmooth',
            Thickness = 0.065532,
            Conductivity = 0.15,
            Density = 608.701223809829,
            Specific_Heat = 1630
            )

        idf1.newidfobject('Material',
            Name = 'Foundation_EPS',
            Roughness = 'MediumSmooth',
            Thickness = 0.0508,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS',
            Roughness = 'MediumSmooth',
            Thickness = 0.0508,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'F11_Wood_siding',
            Roughness = 'MediumSmooth',
            Thickness = 0.0127,
            Conductivity = 0.09,
            Density = 592,
            Specific_Heat = 1170
            )
            
        idf1.newidfobject('Material',
            Name = 'R-11_3.5in_Wood_Stud',
            Roughness = 'VeryRough',
            Thickness = 0.0889,
            Conductivity = 0.05426246,
            Density = 19,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'Plywood_(Douglas_Fir)_-_12.7mm',
            Roughness = 'Smooth',
            Thickness = 0.0127,
            Conductivity = 0.12,
            Density = 540,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_1in',
            Roughness = 'MediumSmooth',
            Thickness = 0.0254,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_1.625in',
            Roughness = 'MediumSmooth',
            Thickness = 0.041275,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_2in',
            Roughness = 'MediumSmooth',
            Thickness = 0.0508,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_4in',
            Roughness = 'MediumSmooth',
            Thickness = 0.1016,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_6in',
            Roughness = 'MediumSmooth',
            Thickness = 0.1524,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_7.5in',
            Roughness = 'MediumSmooth',
            Thickness = 0.1905,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_9in',
            Roughness = 'MediumSmooth',
            Thickness = 0.1524,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'EPS_14in',
            Roughness = 'MediumSmooth',
            Thickness = 0.3556,
            Conductivity = 0.02884,
            Density = 29,
            Specific_Heat = 1210
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-19',
            Roughness = 'MediumRough',
            Thickness = 0.13716,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-30',
            Roughness = 'MediumRough',
            Thickness = 0.21844,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-38',
            Roughness = 'MediumRough',
            Thickness = 0.275844,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-49',
            Roughness = 'MediumRough',
            Thickness = 0.3556,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-55',
            Roughness = 'MediumRough',
            Thickness = 0.3991229,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-60',
            Roughness = 'MediumRough',
            Thickness = 0.3556,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-75',
            Roughness = 'MediumRough',
            Thickness = 0.54356,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'FG_Attic_R-100',
            Roughness = 'MediumRough',
            Thickness = 0.72644,
            Conductivity = 0.04119794,
            Density = 64,
            Specific_Heat = 960
            )

        idf1.newidfobject('Material',
            Name = 'ccSF_R-13',
            Roughness = 'Rough',
            Thickness = 0.05503418,
            Conductivity = 0.024033814,
            Density = 32,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'ccSF_R-19',
            Roughness = 'Rough',
            Thickness = 0.080433418,
            Conductivity = 0.024033814,
            Density = 32,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'ccSF_R-30',
            Roughness = 'Rough',
            Thickness = 0.127,
            Conductivity = 0.024033814,
            Density = 32,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'ccSF_R-38',
            Roughness = 'Rough',
            Thickness = 0.160866582,
            Conductivity = 0.024033814,
            Density = 32,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'ccSF_R-49',
            Roughness = 'Rough',
            Thickness = 0.207433418,
            Conductivity = 0.024033814,
            Density = 32,
            Specific_Heat = 920
            )

        idf1.newidfobject('Material',
            Name = 'StemWall_UnIns',
            Roughness = 'MediumRough',
            Thickness = 0.003175,
            Conductivity = 0.53,
            Density = 1280,
            Specific_Heat = 840
            )

        idf1.newidfobject('Material:AirGap',
            Name = 'F04_Wall_air_space_resistance',
            Thermal_Resistance = 0.15
            )

        idf1.newidfobject('Material:AirGap',
            Name = 'F05_Ceiling_air_space_resistance',
            Thermal_Resistance = 0.18
            )

        idf1.newidfobject('WindowMaterial:SimpleGlazingSystem',
            Name = 'Ext_Window1_Base',
            UFactor = Ext_Window1_Base_Ufactor,
            Solar_Heat_Gain_Coefficient = Ext_Window1_Base_SHGC
            )
        
        idf1.newidfobject('Construction',
            Name = 'Ext_Window1_Base',
            Outside_Layer = 'Ext_Window1_Base')

        #Base constructions:

        idf1.newidfobject('Construction',
            Name = 'Brick Wall',
            Outside_Layer = 'M01_100mm_brick'
            )

        idf1.newidfobject('Construction',
            Name = 'Ext_Door1',
            Outside_Layer = 'G05_25mm_wood'
            )

        idf1.newidfobject('Construction',
            Name = 'Thermal_Mass',
            Outside_Layer = 'G05_25mm_wood'
            )

        constructionBuilder('Interior_Floor', ['Plywood_(Douglas_Fir)_-_12.7mm', 'F05_Ceiling_air_space_resistance', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Slab_UnIns', ['M15_200mm_heavyweight_concrete'])
        constructionBuilder('Exterior_Slab_+_2in_EPS', ['EPS_2in', 'M15_200mm_heavyweight_concrete'])
        constructionBuilder('Exterior_Wall', ['F11_Wood_siding', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Interior_Wall', ['G01a_19mm_gypsum_board', 'F04_Wall_air_space_resistance', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof', ['FG_Attic_R-19', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Door', ['F08_Metal_surface', 'I02_50mm_insulation_board', 'F08_Metal_surface'])
        constructionBuilder('Interior_Door', ['G05_25mm_wood'])
        constructionBuilder('Exterior_Wall_+1in_EPS', ['F11_Wood_siding', 'EPS_1in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+1.625in_EPS', ['F11_Wood_siding', 'EPS_1.625in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+2in_EPS', ['F11_Wood_siding', 'EPS_2in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+4in_EPS', ['F11_Wood_siding', 'EPS_4in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+7.5in_EPS', ['F11_Wood_siding', 'EPS_7.5in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+6in_EPS', ['F11_Wood_siding', 'EPS_6in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+9in_EPS', ['F11_Wood_siding', 'EPS_9in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Wall_+14in_EPS', ['F11_Wood_siding', 'EPS_14in', 'Plywood_(Douglas_Fir)_-_12.7mm', 'R-11_3.5in_Wood_Stud', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-30', ['FG_Attic_R-30', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-38', ['FG_Attic_R-38', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-49', ['FG_Attic_R-49', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-55', ['FG_Attic_R-55', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-60', ['FG_Attic_R-60', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-75', ['FG_Attic_R-75', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('Exterior_Roof_R-100', ['FG_Attic_R-100', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G01a_19mm_gypsum_board'])
        constructionBuilder('P+B_UnIns', ['Plywood_(Douglas_Fir)_-_12.7mm', 'F05_Ceiling_air_space_resistance', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])
        constructionBuilder('P+B_R-13', ['Plywood_(Douglas_Fir)_-_12.7mm', 'ccSF_R-13', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])
        constructionBuilder('P+B_R-19', ['Plywood_(Douglas_Fir)_-_12.7mm', 'ccSF_R-19', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])
        constructionBuilder('P+B_R-30', ['Plywood_(Douglas_Fir)_-_12.7mm', 'ccSF_R-30', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])
        constructionBuilder('P+B_R-38', ['Plywood_(Douglas_Fir)_-_12.7mm', 'ccSF_R-38', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])
        constructionBuilder('P+B_R-49', ['Plywood_(Douglas_Fir)_-_12.7mm', 'ccSF_R-49', 'Plywood_(Douglas_Fir)_-_12.7mm', 'G05_25mm_wood'])

        ##Shade Materials
        idf1.newidfobject('WindowMaterial:Shade',
            Name = 'HighReflect',
            Solar_Transmittance = 0.1,
            Solar_Reflectance = 0.8,
            Visible_Transmittance = 0.1,
            Visible_Reflectance = 0.8,
            Infrared_Hemispherical_Emissivity = 0.8,
            Infrared_Transmittance = 0.1,
            Thickness = 0.005,
            Conductivity = 0.1,
            Shade_to_Glass_Distance = 0.05,
            Top_Opening_Multiplier = 0.5,
            Bottom_Opening_Multiplier = 0.5,
            LeftSide_Opening_Multiplier = 0.5,
            RightSide_Opening_Multiplier = 0.5,
            Airflow_Permeability = 0
            )

        #KIVA
        idf1.newidfobject('Foundation:Kiva',
            Name = 'Slab Details',
            # ,_________________________!-_Initial_Indoor_Air_Temperature
            # ,_________________________!-_Interior_Horizontal_Insulation_Material_Name
            # ,_________________________!-_Interior_Horizontal_Insulation_Depth
            # ,_________________________!-_Interior_Horizontal_Insulation_Width
            # ,_________________________!-_Interior_Vertical_Insulation_Material_Name
            # ,_________________________!-_Interior_Vertical_Insulation_Depth
            # ,_________________________!-_Exterior_Horizontal_Insulation_Material_Name
            # ,_________________________!-_Exterior_Horizontal_Insulation_Depth
            # ,_________________________!-_Exterior_Horizontal_Insulation_Width
            # =_$StemWall,______________!-_Exterior_Vertical_Insulation_Material_Name
            # 1.0668,___________________!-_Exterior_Vertical_Insulation_Depth
            # 0.1524,___________________!-_Wall_Height_Above_Grade
            # 1.0668,___________________!-_Wall_Depth_Below_Slab
            # ,_________________________!-_Footing_Wall_Construction_Name
            # M15_200mm_heavyweight_concrete,____!-_Footing_Material_Name
            Footing_Depth = 1.3716
            )

        idf1.newidfobject('SurfaceProperty:ExposedFoundationPerimeter',
            Surface_Name = 'Slab',
            Exposed_Perimeter_Calculation_Method = 'ExposedPerimeterFraction',
            #0,________________________!-_Total_Exposed_Perimeter
            Exposed_Perimeter_Fraction = 1.0,
            Surface_Segment_1_Exposed = 'Yes'
            )

        #Operable Windows
        idf1.newidfobject('ZoneVentilation:WindandStackOpenArea',
            Name = 'OperableWindows-N',
            Zone_Name = 'Zone 1',
            Opening_Area = operableArea_N,
            Opening_Area_Fraction_Schedule_Name = 'WindowFraction2',
            Opening_Effectiveness = 'autocalculate',
            Effective_Angle = 0,
            Height_Difference = halfHeight,
            Discharge_Coefficient_for_Opening = 'autocalculate',
            Minimum_Indoor_Temperature = 15,
            Maximum_Indoor_Temperature = 100,
            Delta_Temperature = -100,
            Minimum_Outdoor_Temperature = -100,
            Maximum_Outdoor_Temperature = 100,
            Maximum_Wind_Speed = 10
            )

        ## Sizing settings
        idf1.newidfobject('DesignSpecification:OutdoorAir',
            Name = 'SZ_DSOA_Zone_1',
            Outdoor_Air_Method = 'Flow/Zone',
            Outdoor_Air_Flow_per_Person = 7.08000089E-03,
            Outdoor_Air_Flow_per_Zone = 0.01179868608
            )

        idf1.newidfobject('DesignSpecification:ZoneAirDistribution',
            Name = 'SZ_DSZAD_Zone_1',
            Zone_Air_Distribution_Effectiveness_in_Cooling_Mode = 1,
            Zone_Air_Distribution_Effectiveness_in_Heating_Mode = 1
            )

        idf1.newidfobject('Sizing:Zone',
            Zone_or_ZoneList_Name = 'Zone 1',
            Zone_Cooling_Design_Supply_Air_Temperature_Input_Method = 'SupplyAirTemperature',
            Zone_Cooling_Design_Supply_Air_Temperature = 12.8,
            Zone_Cooling_Design_Supply_Air_Temperature_Difference = 11.11,
            Zone_Heating_Design_Supply_Air_Temperature_Input_Method = 'SupplyAirTemperature',
            Zone_Heating_Design_Supply_Air_Temperature = 50,
            Zone_Heating_Design_Supply_Air_Temperature_Difference = 30,
            Zone_Cooling_Design_Supply_Air_Humidity_Ratio = 0.008,
            Zone_Heating_Design_Supply_Air_Humidity_Ratio = 0.008,
            Design_Specification_Outdoor_Air_Object_Name = 'SZ_DSOA_Zone_1',
            Cooling_Design_Air_Flow_Method = 'DesignDay',
            Heating_Design_Air_Flow_Method = 'DesignDay',
            Design_Specification_Zone_Air_Distribution_Object_Name = 'SZ_DSZAD_Zone_1'
            )

        # idf1.newidfobject('Sizing:System',
        #    AirLoop_Name = 'HP_MiniSplit'
            # Sensible,_________________!-_Type_of_Load_to_Size_On
            # autosize,_________________!-_Design_Outdoor_Air_Flow_Rate
            # 1,________________________!-_Central_Heating_Maximum_System_Air_Flow_Ratio
            # 7,________________________!-_Preheat_Design_Temperature
            # 0.008,____________________!-_Preheat_Design_Humidity_Ratio
            # 11,_______________________!-_Precool_Design_Temperature
            # 0.008,____________________!-_Precool_Design_Humidity_Ratio
            # 12.8,_____________________!-_Central_Cooling_Design_Supply_Air_Temperature
            # 50,_______________________!-_Central_Heating_Design_Supply_Air_Temperature
            # NonCoincident,____________!-_Type_of_Zone_Sum_to_Use
            # No,_______________________!-_100_Outdoor_Air_in_Cooling
            # No,_______________________!-_100_Outdoor_Air_in_Heating
            # 0.008,____________________!-_Central_Cooling_Design_Supply_Air_Humidity_Ratio
            # 0.008,____________________!-_Central_Heating_Design_Supply_Air_Humidity_Ratio
            # DesignDay,________________!-_Cooling_Supply_Air_Flow_Rate_Method
            # 0,________________________!-_Cooling_Supply_Air_Flow_Rate
            # ,_________________________!-_Cooling_Supply_Air_Flow_Rate_Per_Floor_Area
            # ,_________________________!-_Cooling_Fraction_of_Autosized_Cooling_Supply_Air_Flow_Rate
            # ,_________________________!-_Cooling_Supply_Air_Flow_Rate_Per_Unit_Cooling_Capacity
            # DesignDay,________________!-_Heating_Supply_Air_Flow_Rate_Method
            # 0,________________________!-_Heating_Supply_Air_Flow_Rate
            # ,_________________________!-_Heating_Supply_Air_Flow_Rate_Per_Floor_Area
            # ,_________________________!-_Heating_Fraction_of_Autosized_Heating_Supply_Air_Flow_Rate
            # ,_________________________!-_Heating_Fraction_of_Autosized_Cooling_Supply_Air_Flow_Rate
            # ,_________________________!-_Heating_Supply_Air_Flow_Rate_Per_Unit_Heating_Capacity
            # ZoneSum,__________________!-_System_Outdoor_Air_Method
            # 1,________________________!-_Zone_Maximum_Outdoor_Air_Fraction
            # CoolingDesignCapacity,____!-_Cooling_Design_Capacity_Method
            # autosize,_________________!-_Cooling_Design_Capacity
            # ,_________________________!-_Cooling_Design_Capacity_Per_Floor_Area
            # ,_________________________!-_Fraction_of_Autosized_Cooling_Design_Capacity
            # HeatingDesignCapacity,____!-_Heating_Design_Capacity_Method
            # autosize,_________________!-_Heating_Design_Capacity
            # ,_________________________!-_Heating_Design_Capacity_Per_Floor_Area
            # ,_________________________!-_Fraction_of_Autosized_Heating_Design_Capacity
            # OnOff;____________________!-_Central_Cooling_Capacity_Control_Method
        #    )


        #HVAC System Controls

        idf1.newidfobject('ZoneControl:Humidistat',
            Name = 'Zone_1_Humidistat',
            Zone_Name = 'Zone 1',
            Humidifying_Relative_Humidity_Setpoint_Schedule_Name = 'Humidity_Setpoint'
            )

        idf1.newidfobject('ZoneControl:Thermostat',
            Name = 'Zone_1_Thermostat',
            Zone_or_ZoneList_Name = 'Zone 1',
            Control_Type_Schedule_Name = 'HVAC_Always_4',
            Control_1_Object_Type = 'ThermostatSetpoint:DualSetpoint',
            Control_1_Name = 'HP_Thermostat_Dual_SP_Control'
            )

        idf1.newidfobject('ThermostatSetpoint:DualSetpoint',
            Name = 'HP_Thermostat_Dual_SP_Control',
            Heating_Setpoint_Temperature_Schedule_Name = 'Phius_68F',
            Cooling_Setpoint_Temperature_Schedule_Name = 'Phius_77F'
            )

        ## Mechanical Zone Connections

        idf1.newidfobject('ZoneHVAC:EquipmentList',
            Name = 'Zone_1_Equipment',
            Load_Distribution_Scheme = 'SequentialLoad',
            Zone_Equipment_1_Object_Type = 'ZoneHVAC:EnergyRecoveryVentilator',
            Zone_Equipment_1_Name = 'ERV1',
            Zone_Equipment_1_Cooling_Sequence = 2,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence = 2,
            Zone_Equipment_2_Object_Type = 'ZoneHVAC:PackagedTerminalHeatPump',
            Zone_Equipment_2_Name = 'Zone1PTHP',
            Zone_Equipment_2_Cooling_Sequence = 1,
            Zone_Equipment_2_Heating_or_NoLoad_Sequence = 1
            #Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name = 
            #Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name = 
            )

        idf1.newidfobject('ZoneHVAC:EquipmentConnections',
            Zone_Name = 'Zone 1',
            Zone_Conditioning_Equipment_List_Name = 'Zone_1_Equipment',
            Zone_Air_Inlet_Node_or_NodeList_Name = 'Zone_1_Inlets',
            Zone_Air_Exhaust_Node_or_NodeList_Name = 'Zone_1_Exhausts',
            Zone_Air_Node_Name = 'Zone_1_Zone_Air_Node',
            Zone_Return_Air_Node_or_NodeList_Name = 'Zone_1_Returns'
            )

        idf1.newidfobject('NodeList',
            Name = 'Zone_1_Inlets',
            Node_1_Name = 'Zone_1_ERV_Supply',
            Node_2_Name = 'Zone1PTHPAirOutletNode'
            )

        idf1.newidfobject('NodeList',
            Name = 'Zone_1_Returns',
            Node_1_Name = 'Zone_1_Return'
            )

        idf1.newidfobject('NodeList',
            Name = 'Zone_1_Exhausts',
            Node_1_Name = 'Zone_1_ERV_Exhaust',
            Node_2_Name = 'Zone1PTHPAirInletNode'
            )

        #### ERV

        idf1.newidfobject('ZoneHVAC:EnergyRecoveryVentilator',
            Name = 'ERV1',
            Availability_Schedule_Name = 'ERV_Avail',
            Heat_Exchanger_Name = 'ERV_Core',
            Supply_Air_Flow_Rate = '0.047',
            Exhaust_Air_Flow_Rate = '0.047',
            Supply_Air_Fan_Name = 'ERV_Supply_Fan',
            Exhaust_Air_Fan_Name = 'ERV_Exhaust_Fan'
            )

        idf1.newidfobject('Fan:OnOff',
            Name = 'ERV_Supply_Fan',
            Availability_Schedule_Name = 'Always_On',
            Fan_Total_Efficiency = 0.6,
            Pressure_Rise = 249.088957139263,
            Maximum_Flow_Rate = 'autosize',
            Motor_Efficiency = 0.8,
            Motor_In_Airstream_Fraction = 1,
            Air_Inlet_Node_Name = 'ERV_Core_Sup_Out',
            Air_Outlet_Node_Name = 'Zone_1_ERV_Supply',
            EndUse_Subcategory = 'ERV_Fan'
            )

        idf1.newidfobject('Fan:OnOff',
            Name = 'ERV_Exhaust_Fan',
            Availability_Schedule_Name = 'Always_On',
            Fan_Total_Efficiency = 0.6,
            Pressure_Rise = 249.088957139263,
            Maximum_Flow_Rate = 'autosize',
            Motor_Efficiency = 0.8,
            Motor_In_Airstream_Fraction = 1,
            Air_Inlet_Node_Name = 'ERV_Core_Exh_Out',
            Air_Outlet_Node_Name = 'Zone_1_ERV_Exhaust',
            EndUse_Subcategory = 'ERV_Fan'
            )

        idf1.newidfobject('HeatExchanger:AirToAir:SensibleAndLatent',
            Name = 'ERV_Core',
            Availability_Schedule_Name = 'Always_On',
            Nominal_Supply_Air_Flow_Rate = 0.047,
            Sensible_Effectiveness_at_100_Heating_Air_Flow = ervSense,
            Latent_Effectiveness_at_100_Heating_Air_Flow = ervLatent,
            Sensible_Effectiveness_at_75_Heating_Air_Flow = ervSense,
            Latent_Effectiveness_at_75_Heating_Air_Flow = ervLatent,
            Sensible_Effectiveness_at_100_Cooling_Air_Flow = ervSense,
            Latent_Effectiveness_at_100_Cooling_Air_Flow = ervLatent,
            Sensible_Effectiveness_at_75_Cooling_Air_Flow = ervSense,
            Latent_Effectiveness_at_75_Cooling_Air_Flow = ervLatent,
            Supply_Air_Inlet_Node_Name = 'OA_1',
            Supply_Air_Outlet_Node_Name = 'ERV_Core_Sup_Out',
            Exhaust_Air_Inlet_Node_Name = 'Zone_1_ERV_Exhaust',
            Exhaust_Air_Outlet_Node_Name = 'ERV_Core_Exh_Out',
            Supply_Air_Outlet_Temperature_Control = 'No',
            Heat_Exchanger_Type = 'Plate',
            Frost_Control_Type = 'ExhaustAirRecirculation',
            Threshold_Temperature = -5,
            Initial_Defrost_Time_Fraction = 0.083,
            Rate_of_Defrost_Time_Fraction_Increase = 0.012,
            Economizer_Lockout = 'Yes'
            )

        idf1.newidfobject('OutdoorAir:Node',
            Name = 'OA_1',
            Height_Above_Ground = 3.048
            )
        idf1.newidfobject('OutdoorAir:Node',
            Name = 'OA_2',
            Height_Above_Ground = 3.048
            )

        ##Heat Pump
        idf1.newidfobject('ZoneHVAC:PackagedTerminalHeatPump',
            Name = 'Zone1PTHP',
            Availability_Schedule_Name = 'PTHP_Avail',
            Air_Inlet_Node_Name = 'Zone1PTHPAirInletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPAirOutletNode',
            # OutdoorAir:Mixer,________!-_Outdoor_Air_Mixer_Object_Type
            # Zone1PTHPOAMixer,________!-_Outdoor_Air_Mixer_Name
            Cooling_Supply_Air_Flow_Rate = 'autosize',
            Heating_Supply_Air_Flow_Rate = 'autosize',
            # No_Load_Supply_Air_Flow_Rate_{m3/s}
            Cooling_Outdoor_Air_Flow_Rate = 'autosize',
            Heating_Outdoor_Air_Flow_Rate = 'autosize',
            # No_Load_Outdoor_Air_Flow_Rate_{m3/s}
            Supply_Air_Fan_Object_Type = 'Fan:SystemModel',
            Supply_Air_Fan_Name = 'Zone1PTHPFan',
            Heating_Coil_Object_Type = 'Coil:Heating:DX:SingleSpeed',
            Heating_Coil_Name = 'Zone1PTHPDXHeatCoil',
            #Heating_Convergence_Tolerance_{dimensionless}
            Cooling_Coil_Object_Type = 'Coil:Cooling:DX:SingleSpeed',
            Cooling_Coil_Name = 'Zone1PTHPDXCoolCoil',
            #Cooling_Convergence_Tolerance_{dimensionless}
            Supplemental_Heating_Coil_Object_Type = 'Coil:Heating:Electric',
            Supplemental_Heating_Coil_Name = 'Zone1PTHPSupHeater',
            Maximum_Supply_Air_Temperature_from_Supplemental_Heater = 50,
            Maximum_Outdoor_DryBulb_Temperature_for_Supplemental_Heater_Operation = 10,
            Fan_Placement = 'BlowThrough'
            #ConstantFanSch;__________!-_Supply_Air_Fan_Operating_Mode_Schedule_Name')
            )

        idf1.newidfobject('Fan:SystemModel',
            Name = 'Zone1PTHPFan',
            Availability_Schedule_Name = 'PTHP_Avail',
            Air_Inlet_Node_Name = 'Zone1PTHPAirInletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPFanOutletNode',
            Design_Maximum_Air_Flow_Rate = 'autosize',
            Speed_Control_Method = 'Continuous',
            Electric_Power_Minimum_Flow_Rate_Fraction = 0.0,
            Design_Pressure_Rise = 0.75,
            Motor_Efficiency = 0.9,
            Motor_In_Air_Stream_Fraction = 1.0,
            Design_Electric_Power_Consumption = 'autosize',
            Design_Power_Sizing_Method = 'TotalEfficiencyAndPressure',
            # Electric_Power_Per_Unit_Flow_Rate_{W/(m3/s)}
            # Electric_Power_Per_Unit_Flow_Rate_Per_Unit_Pressure_{W/((m3/s)-Pa)}
            Fan_Total_Efficiency = 0.5,
            Electric_Power_Function_of_Flow_Fraction_Curve_Name = 'CombinedPowerAndFanEff'
            )

        idf1.newidfobject('Coil:Heating:Electric',
            Name = 'Zone1PTHPSupHeater',
            Availability_Schedule_Name = 'PTHP_Avail',
            Efficiency = 1.0,
            Nominal_Capacity = 'autosize',
            Air_Inlet_Node_Name = 'Zone1PTHPDXHeatCoilOutletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPAirOutletNode'
            )

        idf1.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = 'Zone1PTHPDXCoolCoil',
            Availability_Schedule_Name = 'PTHP_Avail',
            Gross_Rated_Total_Cooling_Capacity = 'autosize',
            Gross_Rated_Sensible_Heat_Ratio = 0.75,
            Gross_Rated_Cooling_COP = 3.0,  # Change to var for future shit
            Rated_Air_Flow_Rate = 'autosize',
            Air_Inlet_Node_Name = 'Zone1PTHPFanOutletNode',
            Air_Outlet_Node_Name  = 'Zone1PTHPDXCoolCoilOutletNode',
            Total_Cooling_Capacity_Function_of_Temperature_Curve_Name = 'HPACCoolCapFT',
            Total_Cooling_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACCoolCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACPLFFPLR'
            )

        idf1.newidfobject('Coil:Heating:DX:SingleSpeed',
            Name = 'Zone1PTHPDXHeatCoil',
            Availability_Schedule_Name = 'PTHP_Avail',
            Gross_Rated_Heating_Capacity = 'autosize',
            Gross_Rated_Heating_COP = 3.0, #change to var for future
            Rated_Air_Flow_Rate  ='autosize',
            # Rated_Supply_Fa,n_Power_Per_Volume_Flow_Rate_{W/(m3/s)}
            Air_Inlet_Node_Name = 'Zone1PTHPDXCoolCoilOutletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPDXHeatCoilOutletNode',
            Heating_Capacity_Function_of_Temperature_Curve_Name = 'HPACHeatCapFT',
            Heating_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACHeatEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACCOOLPLFFPLR',
            # Defrost_Energy_Input_Ratio_Function_of_Temperature_Curve_Name
            Minimum_Outdoor_DryBulb_Temperature_for_Compressor_Operation = 0.0, #future var
            #Outdoor_Dry-Bulb_Temperature_to_Turn_On_Compressor_{C}
            Maximum_Outdoor_DryBulb_Temperature_for_Defrost_Operation = 5.0,
            Crankcase_Heater_Capacity = 200.0,
            Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater_Operation = 10.0,
            Defrost_Strategy = 'Resistive',
            Defrost_Control = 'TIMED',
            Defrost_Time_Period_Fraction = 0.166667,
            Resistive_Defrost_Heater_Capacity = 'autosize'
            )

        # Curves
        idf1.newidfobject('Curve:Cubic',
            Name = 'CombinedPowerAndFanEff',
            Coefficient1_Constant = 0.0,
            Coefficient2_x = 0.027411,
            Coefficient3_x2 = 0.008740,
            Coefficient4_x3 = 0.969563,
            Minimum_Value_of_x = 0.5,
            Maximum_Value_of_x = 1.5,
            Minimum_Curve_Output = 0.01,
            Maximum_Curve_Output = 1.5
            )

        idf1.newidfobject('Curve:Quadratic',
            Name = 'HPACCoolCapFFF',
            Coefficient1_Constant = 0.8,
            Coefficient2_x = 0.2,
            Coefficient3_x2 = 0.0,
            Minimum_Value_of_x = 0.5,
            Maximum_Value_of_x = 1.5
            )

        idf1.newidfobject('Curve:Quadratic',
            Name = 'HPACEIRFFF',
            Coefficient1_Constant = 1.1552,
            Coefficient2_x = -0.1808,
            Coefficient3_x2  =0.0256,
            Minimum_Value_of_x = 0.5,
            Maximum_Value_of_x = 1.5
            )
        idf1.newidfobject('Curve:Quadratic',
            Name = 'HPACPLFFPLR',
            Coefficient1_Constant = 0.85,
            Coefficient2_x = 0.15,
            Coefficient3_x2 = 0.0,
            Minimum_Value_of_x = 0.0,
            Maximum_Value_of_x = 1.0
            )
        idf1.newidfobject('Curve:Quadratic',
            Name = 'HPACHeatEIRFFF',
            Coefficient1_Constant = 1.3824,
            Coefficient2_x = -0.4336,
            Coefficient3_x2 = 0.0512,
            Minimum_Value_of_x = 0.0,
            Maximum_Value_of_x = 1.0
            )
        idf1.newidfobject('Curve:Quadratic',
            Name = 'HPACCOOLPLFFPLR',
            Coefficient1_Constant = 0.75,
            Coefficient2_x = 0.25,
            Coefficient3_x2 = 0.0,
            Minimum_Value_of_x = 0.0,
            Maximum_Value_of_x = 1.0
            )
        idf1.newidfobject('Curve:Cubic',
            Name = 'HPACHeatCapFT',
            Coefficient1_Constant = 0.758746,
            Coefficient2_x = 0.027626,
            Coefficient3_x2 = 0.000148716,
            Coefficient4_x3 = 0.0000034992,
            Minimum_Value_of_x = -20.0,
            Maximum_Value_of_x = 20.0,
            # Minimum_Curve_Output
            # Maximum_Curve_Output
            Input_Unit_Type_for_X = 'Temperature',
            Output_Unit_Type = 'Dimensionless'
            )
        idf1.newidfobject('Curve:Cubic',
            Name = 'HPACHeatCapFFF',
            Coefficient1_Constant = 0.84,
            Coefficient2_x = 0.16,
            Coefficient3_x2 = 0.0,
            Coefficient4_x3 = 0.0,
            Minimum_Value_of_x = 0.5,
            Maximum_Value_of_x = 1.5
            )

        idf1.newidfobject('Curve:Cubic',
            Name = 'HPACHeatEIRFT',
            Coefficient1_Constant = 1.19248,
            Coefficient2_x = -0.0300438,
            Coefficient3_x2 = 0.00103745,
            Coefficient4_x3 = -0.000023328,
            Minimum_Value_of_x = -20.0,
            Maximum_Value_of_x = 20.0,
            # Minimum_Curve_Output
            # Maximum_Curve_Output
            Input_Unit_Type_for_X = 'Temperature',
            Output_Unit_Type = 'Dimensionless'
            )

        idf1.newidfobject('Curve:Cubic',
            Name = 'FanEffRatioCurve',
            Coefficient1_Constant = 0.33856828,
            Coefficient2_x = 1.72644131,
            Coefficient3_x2 = -1.49280132,
            Coefficient4_x3 = 0.42776208,
            Minimum_Value_of_x = 0.5,
            Maximum_Value_of_x = 1.5,
            Minimum_Curve_Output = 0.3,
            Maximum_Curve_Output = 1.0
            )

        idf1.newidfobject('Curve:Exponent',
            Name = 'FanPowerRatioCurve',
            Coefficient1_Constant = 0.0,
            Coefficient2_Constant = 1.0,
            Coefficient3_Constant = 3.0,
            Minimum_Value_of_x = 0.0,
            Maximum_Value_of_x = 1.5,
            Minimum_Curve_Output = 0.01,
            Maximum_Curve_Output = 1.5
            )

        idf1.newidfobject('Curve:Biquadratic',
            Name = 'HPACCoolCapFT',
            Coefficient1_Constant = 0.942587793,
            Coefficient2_x = 0.009543347,
            Coefficient3_x2 = 0.000683770,
            Coefficient4_y = -0.011042676,
            Coefficient5_y2 = 0.000005249,
            Coefficient6_xy = -0.000009720,
            Minimum_Value_of_x = 12.77778,
            Maximum_Value_of_x = 23.88889,
            Minimum_Value_of_y = 18.0,
            Maximum_Value_of_y = 46.11111,
            # Minimum_Curve_Output
            # Maximum_Curve_Output
            Input_Unit_Type_for_X = 'Temperature',
            Input_Unit_Type_for_Y = 'Temperature',
            Output_Unit_Type = 'Dimensionless'
            )

        idf1.newidfobject('Curve:Biquadratic',
            Name = 'HPACEIRFT',
            Coefficient1_Constant = 0.342414409,
            Coefficient2_x = 0.034885008,
            Coefficient3_x2 = -0.000623700,
            Coefficient4_y = 0.004977216,
            Coefficient5_y2 = 0.000437951,
            Coefficient6_xy = -0.000728028,
            Minimum_Value_of_x = 12.77778,
            Maximum_Value_of_x = 23.88889,
            Minimum_Value_of_y = 18.0,
            Maximum_Value_of_y = 46.11111,
            # Minimum_Curve_Output
            # Maximum_Curve_Output
            Input_Unit_Type_for_X ='Temperature',
            Input_Unit_Type_for_Y ='Temperature',
            Output_Unit_Type = 'Dimensionless'
            )

        ### Outputs

        idf1.newidfobject('Output:VariableDictionary',
            Key_Field = 'IDF')

        idf1.newidfobject('Output:Table:SummaryReports',
            Report_1_Name = 'AllSummary')

        idf1.newidfobject('Output:Table:TimeBins',
            Key_Value = '*',
            Variable_Name = 'Zone Air Temperature',
            Interval_Start = -40,
            Interval_Size = 42,
            Interval_Count = 1,
            Variable_Type = 'Temperature'
            )

        idf1.newidfobject('OutputControl:Table:Style',
            Column_Separator = 'HTML',
            Unit_Conversion = 'InchPound'
            )

        idf1.newidfobject('Output:SQLite',
            Option_Type = 'SimpleAndTabular',
            Unit_Conversion_for_Tabular_Data = 'InchPound'
            )

        outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature']
        meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity']
        for x in outputVars:
            idf1.newidfobject('Output:Variable',
            Key_Value = '*',
            Variable_Name = str(x),
            Reporting_Frequency = 'hourly'
            )

        for x in meterVars:
            idf1.newidfobject('Output:Meter:MeterFileOnly',
            Key_Name = str(x),
            Reporting_Frequency = 'Monthly'
            )
        
        # Change Constructions
        count = -1
        for srf in idf1.idfobjects['BuildingSurface:Detailed']:
            count += 1
            surface = idf1.idfobjects['BuildingSurface:Detailed'][count]
            if surface.Construction_Name == 'Ext_Wall1':
                surface.Construction_Name = str(Ext_Wall1_base)
            if surface.Construction_Name == 'Ext_Roof1':
                surface.Construction_Name = str(Ext_Roof1_base)
            if surface.Construction_Name == 'Ext_Floor1':
                surface.Construction_Name = str(Ext_Floor1_base)
            if surface.Construction_Name == 'Ext_Door1':
                surface.Construction_Name = str(Ext_Door1_base)
            if surface.Construction_Name == 'Int_Floor1':
                surface.Construction_Name = str(Int_Floor1)

        count = -1
        for fen in idf1.idfobjects['FenestrationSurface:Detailed']:
            count += 1
            window = idf1.idfobjects['FenestrationSurface:Detailed'][count]
            if window.Construction_Name == 'Ext_Window1':
                window.Construction_Name = 'Ext_Window1_Base'


        idf1.saveas(str(testingFile))

        #==============================================================================================================================
        # 4. Basline building annual simulation
        #==============================================================================================================================

        idf1 = IDF(str(testingFile)) 

        #Schedules
        SchName_Lighting = 'Phius_Lighting'
        SchValues_Lighting = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

        SchName_MELs = 'Phius_MELs'
        SchValues_MELs = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

        hourSch(SchName_Lighting, SchValues_Lighting)

        hourSch(SchName_MELs, SchValues_MELs)

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Number')

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Any Number')

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Fraction')

        idf1.newidfobject('Schedule:Constant',
            Name = 'WindowFraction2',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'HVAC_ALWAYS_4',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 4
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Phius_68F',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 20
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Phius_77F',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 25
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'HUMIDITY_SETPOINT',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 60
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'AirVelocitySch',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0.16
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Always_On',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 1
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Always Off',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Activity_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 120
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Eff_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Clothing_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 04/30',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = 'Through: 09/30',
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 0.3,
            Field_9 = 'Through: 12/31',
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'CO2_Schedule',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 500
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'OUTAGE:Occupant_Schedule',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'ERV_Avail',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 1
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'PTHP_Avail',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 1
            )

        idf1.saveas(str(testingFile_BA))
 
        prog_bar.progress(25)

        idf = IDF(str(testingFile_BA), epwfile)
        idf.run(readvars=True)
        prog_bar.progress(50)   

        # ====================================================================================================================
        # X.X Baseline building annual simulation ouptuts
        # ====================================================================================================================
        
        with tab3:
            st.header('Results')
            monthly = pd.read_csv(str(studyFolder) + '\eplusmtr.csv')
            st.dataframe(monthly)
            # st.bar_chart(data=monthly)
            st.header('Resilience Summary')
           
            results = []
            HeatingSET = []
            Caution = []
            ExtremeCaution = []
            Danger = []
            ExtremeDanger = []
            Below2C = []
            eui = []

            fname = (str(studyFolder) + '/eplustbl.htm')
            #results.append(fname)
            filehandle = open(fname, 'r').read()

            ltables = readhtml.lines_table(filehandle) # reads the tables with their titles
            #st.write(htables[1][1])

        for ltable in ltables:
            if 'Site and Source Energy' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                eui = float(ltable[1][1][2])

        # =======================================================================================================================================================
        # X.X Baseline Thermal Resilience
        # =======================================================================================================================================================

        idf1 = IDF(str(testingFile))

        # Schedules for outage simulation
        SchName_Lighting = 'Phius_Lighting'
        SchValues_Lighting = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

        SchName_MELs = 'Phius_MELs'
        SchValues_MELs = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

        zeroSch(SchName_Lighting)

        zeroSch(SchName_MELs)

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Number')

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Any Number')

        idf1.newidfobject('ScheduleTypeLimits',
            Name = 'Fraction')

        idf1.newidfobject('Schedule:Constant',
            Name = 'WindowFraction2',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'HVAC_ALWAYS_4',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 4
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Phius_68F',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 20
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Phius_77F',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 25
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'HUMIDITY_SETPOINT',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 60
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'AirVelocitySch',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0.16
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Always_On',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 1
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'Always Off',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Activity_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 120
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Eff_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'Occupant_Clothing_Schedule',
            Schedule_Type_Limits_Name = 'Any Number',
            Field_1 = 'Through: 04/30',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = 'Through: 09/30',
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 0.3,
            Field_9 = 'Through: 12/31',
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'CO2_Schedule',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 500
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'OUTAGE:Occupant_Schedule',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = 'Through: 12/31',
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1
            )

        idf1.newidfobject('Schedule:Constant',
            Name = 'ERV_Avail',
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 1
            )

        idf1.newidfobject('Schedule:Compact',
            Name = 'PTHP_Avail',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = ('Through: ' + str(outage1start)),
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = ('Through: ' + str(outage1end)),
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 0.0,
            Field_9 = ('Through: ' + str(outage2start)),
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0,
            Field_13 = ('Through: ' + str(outage2end)),
            Field_14 = 'For: AllDays',
            Field_15 = 'Until: 24:00',
            Field_16 = 0.0,
            Field_17 = 'Through: 12/31',
            Field_18 = 'For: AllDays',
            Field_19 = 'Until: 24:00',
            Field_20 = 1.0
            )

        idf1.saveas(str(testingFile_BR))
        idf = IDF(str(testingFile_BR), epwfile)
        idf.run(readvars=True)
        prog_bar.progress(80)

        st.header('Resilience Summary')

        fname = (str(studyFolder) + '/eplustbl.htm')
        filehandle = open(fname, 'r').read()
        ltables = readhtml.lines_table(filehandle) # reads the tables with their titles

        for ltable in ltables:
            if 'Site and Source Energy' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                eui = float(ltable[1][1][2])

        for ltable in ltables:
            if 'Time Bin Results' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                Below2C = float(ltable[1][39][2])
                
        for ltable in ltables:
            if 'Heating SET Hours' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                HeatingSET = float(ltable[1][1][1])

        for ltable in ltables:
            if 'Heat Index Hours' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                Caution = float(ltable[1][1][2])
                ExtremeCaution = float(ltable[1][1][3])
                Danger = float(ltable[1][1][4])
                ExtremeDanger = float(ltable[1][1][5])

        col1, col2, col3 = st.columns(3)

        st.metric(label= 'EUI [kBtu/sf]', value=eui)
        with col1:
            st.metric(label= 'Hours below 2°C', value=Below2C)
            st.metric(label= 'SET hours below 12.2°C', value=HeatingSET)

        with col2:
            st.metric(label= 'Caution', value=Caution)
            st.metric(label= 'Extreme Caution', value=ExtremeCaution)

        with col3:
            st.metric(label= 'Danger', value=Danger)
            st.metric(label= 'Extreme Danger', value=ExtremeDanger)

        filehandle = (str(studyFolder) + '\eplusout.csv')
        hourly = pd.read_csv(filehandle)

        outage1start = dt.datetime(2020, 1,23)
        outage1end = dt.datetime(2020, 2,8)

        hourly.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
        hourly[['Date2','Time']] = hourly.DateTime.str.split(expand=True)
        hourly['Date'] = hourly['Date2'].map(str) + '/' + str(2020)
        hourly['Time'] = (pd.to_numeric(hourly['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourly['Time'].str[2:]
        hourly['DateTime'] = hourly['Date'] + ' ' + hourly['Time']
        hourly['DateTime'] = pd.to_datetime(hourly['DateTime'])

        endWarmup = int((hourly[hourly['DateTime'] == '2020-01-01 00:00:00'].index.values))
        dropWarmup = [*range(0, endWarmup,1)]

        hourly = hourly.drop(index = dropWarmup)
        hourly = hourly.reset_index()

        mask = (hourly['DateTime'] >= outage1start) & (hourly['DateTime'] <= outage1end)

        hourlyHeat = hourly.loc[mask]

        print(outage1start.strftime('%m/%d'))
        st.header('Outage 1 Hourly Plot')
        st.line_chart(hourlyHeat, x='DateTime', y=['ZONE 1:Zone Air Temperature [C](Hourly)', 'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'])

        prog_bar.progress(100)
            