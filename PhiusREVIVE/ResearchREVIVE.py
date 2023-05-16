#=============================================================================================================================
# PhiusREVIVE Research Tool
# Updated 2023/03/23
# v23.0.0
#
#

# Copyright (c) 2023 Phius

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
# import PySimpleGUI as sg
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system

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

# This function builds out custom materials and base materials in the file:
def materialBuilder(name, rough, thick, conduct, dense, heatCap):
    idf1.newidfobject('Material',
        Name = str(name),
        Roughness = str(rough),
        Thickness = thick,
        Conductivity = conduct,
        Density = dense,
        Specific_Heat = heatCap
        )

# This function creates a compact schedule from an hourly list of values: 
def hourSch(nameSch, hourlyValues):
    params = [x for x in hourlyValues]
    schValues = {}
    count = 5
    for i,param in enumerate(params):
        count = count + 1
        schValues['Field_' + str(count)] = ('Until: ' + str(i + 1) + ':00')
        count = count + 1
        schValues['Field_' + str(count)] = param
    idf1.newidfobject('Schedule:Compact',
    Name = str(nameSch),
    Schedule_Type_Limits_Name = 'Fraction',
    Field_1 = 'Through: 12/31',
    Field_2 = 'For: SummerDesignDay WinterDesignDay',
    Field_3 = 'Until: 24:00',
    Field_4 = 0,
    Field_5 = 'For: AllOtherDays',
    **schValues)

# This function creates a version of the hourly schedules with ZERO as the basline
def zeroSch(nameSch):
    idf1.newidfobject('Schedule:Compact',
        Name = str(nameSch),
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = 'For: AllOtherDays',
        Field_6 = 'Until: 24:00',
        Field_7 = 0
    ) 

# This function creates line item costs
def costBuilder(name, type, lineItemType, itemName, objEndUse, costEach, costArea):
    idf1.newidfobject('ComponentCost:LineItem',
        Name = name,
        Type = type,
        Line_Item_Type = lineItemType,
        Item_Name = itemName,
        Object_EndUse_Key = objEndUse,
        Cost_per_Each = costEach,
        Cost_per_Area = costArea
        )

#ADORB
def adorb(analysisPeriod, annualElec, annualGas, annualCO2, dirMR, emCO2, eTrans):
    results = pd.DataFrame(columns=['pv_dirEn', 'pv_opCO2', 'pv_dirMR', 'pv_emCO2', 'pv_eTrans'])
    years = range(analysisPeriod)
    pv = []
    r2 = []
    pc= 0.25
    # Dependencies and databasing
    # NatEmiss = pd.read_csv('NatlEmission.csv')

    k_dirEn = 0.02
    k_opCarb = 0.075
    k_dirMR = 0.02
    k_emCarb = 0
    k_sysTran = 0.02

    # annual sum of all high level sub routines, run those first then run 
    for i in years:
        c_dirMR = []
        year = i+1
        
        # Direct energy costs
        pv_dirEn = (annualElec+ annualGas)/((1+k_dirEn)**year)

        # Cost of operational carbon
        c_opCarb = annualCO2 * pc
        pv_opCO2 = c_opCarb/((1+k_opCarb)**year)

        # Cost of embodied carbon

        # For Level 1 embodied carbon calc (national emissions intensity based):

        # Right now there is no decarbonization glide path applied to embodied emissions (i.e. of recurring equipment replacements).

        # C_emCarb_y = (emMat_y + emLbr_y)*Pc
        # emMat_y is the embodied emissions due of the material items in year y [kg]
        # emLbr_y is the embodied emissions due to domestic / installation labor of the items in year y [kg]

        # emMat_y = sum, over the project retrofit and maintenance items, of emMat_item_y
        # emMat_item_y is the embodied emissions of the material item [kg].

        # emMat_item_y = C_dirMR_item_y * (1-LF_item_y) * EF(CoO_item_y)
        # LF_item_y is the fraction of install labor in C_dirMR_item_y [fraction 0 to 1].
        # EF(country) is the national emission factor of a country [kg/$].
        # CoO_item_y is the country of origin for the item occurring in year y.

        # EF(country) = CO2_country / GDP_country * 1000
        # CO2_country is the annual CO2e emissions from the country [Megatons].
        # GDP_country is the annual gross domestic product of the country [USD millions].

        # EF, CO2 and GDP data for the top 15 US trading partners is shown in Table 1.

        # emLbr_y = sum, over the project retrofit and maintenance items, of emLbr_item_y
        # emLbr_item_y is the embodied emissions due to labor, of the item occurring in year y.

        # emLbr_item_y = C_dirMR_item_y * LF_item_y * EF(COPL)
        # COPL is the country of the project location / building site.


        c_emCO2 = []
        for row in emCO2:
            if row[1] == i:
                c_emCO2.append(0.75*(row[0]/((1+k_emCarb)**year)))
            else:
                c_emCO2.append(0)
        pv_emCO2 = sum(c_emCO2)

        # Cost of direct maint / retrofit
        for row in dirMR:
            # c_dirMR = []
            if row[1] == i:
                c_dirMR.append(row[0]/((1+k_dirMR)**year))
            else:
                c_dirMR.append(0)
        pv_dirMR = sum(c_dirMR)

        # Cost of energy transition
        
        # TCF_y is the transition cost factor for year y. [$/Watt.yr]
        ytt = 30
        NTC = 4.5e12 # for US
        NNCI = 1600 # for US
        NTCF = NTC / (NNCI * 1e9)

        if year > ytt:
            TCF_y = 0 
        else:
            TCF_y = NTCF / ytt 	#linear transition

        C_eTran_y = TCF_y * eTrans

        pv_eTrans = (C_eTran_y)/((1+k_sysTran)**year)

        pv.append((pv_dirEn + pv_opCO2 + pv_dirMR + pv_emCO2 + pv_eTrans))
        newRow = {'pv_dirEn':pv_dirEn, 'pv_opCO2':pv_opCO2, 'pv_dirMR':pv_dirMR, 'pv_emCO2':pv_emCO2, 'pv_eTrans':pv_eTrans}
        results = results.append(newRow, ignore_index=True)
    results.to_csv(str(BaseFileName) + '_ADORBresults.csv')

    df = results

    df2 = pd.DataFrame()
    df2['pv_dirEn'] = df['pv_dirEn'].cumsum()
    df2['pv_dirMR'] = df['pv_dirMR'].cumsum()
    df2['pv_opCO2'] = df['pv_opCO2'].cumsum()
    df2['pv_emCO2'] = df['pv_emCO2'].cumsum()
    df2['pv_eTrans'] = df['pv_eTrans'].cumsum()

    # df2.plot(kind='area', xlabel='Years', ylabel='Cummulative Present Value [$]', title='ADORB COST', figsize=(6.5,8.5))
    fig = df2.plot(kind='area', xlabel='Years', ylabel='Cummulative Present Value [$]', ylim=[0,225000], title=(str(BaseFileName) + '_ADORB COST'), figsize=(16,9)).get_figure()
    fig.savefig(str(studyFolder) + "/" + str(BaseFileName) + '_ADORB.png')

    pv_dirEn_tot = df['pv_dirEn'].sum()
    pv_dirMR_tot = df['pv_dirMR'].sum()
    pv_opCO2_tot = df['pv_opCO2'].sum()
    pv_emCO2_tot = df['pv_emCO2'].sum()
    pv_eTrans_tot = df['pv_eTrans'].sum()

    return sum(pv), pv_dirEn_tot, pv_dirMR_tot, pv_opCO2_tot, pv_emCO2_tot,pv_eTrans_tot

        # PV_i = sum over y from 1 to N of C_i_y / (1+k_i^y) , where
        # C_i  is the Cost, of cost component i [$].
        # k_i is the discount rate for cost component i [fraction 0 to 1].
        # k_dirEnr = 0.02
        # k_opCarb = 0
        # k_dirMR = 0.02
        # k_emCarb = 0
        # y is the year, counting from the current year = 1, that is, the future calendar year minus the previous calendar year.

#==============================================================================================================================
# 3.0 File Management
#==============================================================================================================================

iddfile = 'C:\EnergyPlusV9-5-0\Energy+.idd' # str(input('Path to EnergyPlus IDD file: '))
runListPath = 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/test2/runs.csv' # str(input('Select runs.csv'))
studyFolder = 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/test2' # str(input('Path to folder for study inputs: '))
idfgName = 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/PNNL_SF_Geometry.idf' # str(input('Path to EnergyPlus IDF file with building geometry: '))
emissionsDatabase = ('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/test2/Hourly Emission Rates.csv')
runList = pd.read_csv(str(runListPath))
totalRuns = runList.shape[0]
batchName = str(input('Name for the batch of files to be created: '))

os.chdir(str(studyFolder))
IDF.setiddname(iddfile)

ResultsTable = pd.DataFrame(columns=["Run Name","SET ≤ 12.2°C Hours (F)","Hours < 2°C [hr]","Caution (> 26.7, ≤ 32.2°C) [hr]","Extreme Caution (> 32.2, ≤ 39.4°C) [hr]",
                                         "Danger (> 39.4, ≤ 51.7°C) [hr]","Extreme Danger (> 51.7°C) [hr]", 'EUI','Peak Electric Demand [W]',
                                         'Heating Battery Size [kWh]', 'Cooling Battery Size [kWh]', 'Total ADORB Cost [$]','First Year Electric Cost [$]',
                                         'First Year Gas Cost [$]','First Cost [$]','pv_dirEn_tot','pv_dirMR_tot','pv_opCO2_tot','pv_emCO2_tot',
                                         'pv_eTrans_tot'])

# sum(pv), pv_dirEn_tot, pv_dirMR_tot, pv_opCO2_tot, pv_emCO2_tot,pv_eTrans_tot

for case in range(totalRuns):
    runCount = case
    BaseFileName = (batchName + '_' + runList['CASE_NAME'][runCount])
    caseName = runList['CASE_NAME'][runCount]

    print('Running: ' + str(BaseFileName))

    # testingFile = str(studyFolder) + "/" + str(BaseFileName) + ".idf"
    testingFile_BA = str(studyFolder) + "/" + str(BaseFileName) + "_BA.idf"
    testingFile_BR = str(studyFolder) + "/" + str(BaseFileName) + "_BR.idf"
    passIDF = str(studyFolder) + "/" + str(BaseFileName) + "_PASS.idf"

    #==============================================================================================================================
    # 4.0 Variable Assignment
    #==============================================================================================================================

    epwFile = runList['EPW'][runCount]
    ddyName = runList['DDY'][runCount]

    icfa = runList['ICFA'][runCount]
    icfa_M  =icfa*0.09290304
    Nbr = runList['BEDROOMS'][runCount]
    occ = (runList['BEDROOMS'][runCount] + 1)
    operableArea_N = ((runList['Operable_Area_N'][runCount])*0.09290304)
    operableArea_S = ((runList['Operable_Area_S'][runCount])*0.09290304)
    operableArea_W = ((runList['Operable_Area_W'][runCount])*0.09290304)
    operableArea_E = ((runList['Operable_Area_E'][runCount])*0.09290304)
    halfHeight = 1.524
    ervSense = 0
    ervLatent = 0

    # IHG Calc 

    fridge = (445/(8760))*1000 # always on design load
    fracHighEff = 1.0
    PhiusLights = (0.2 + 0.8*(4 - 3*fracHighEff)/3.7)*(455 + 0.8*icfa) * 0.8 * 1000 * (1/365) #power per day W use Phius calc
    # PhiusLights = (((2 + 0.8*(4 - 3*fracHighEff/3.7)))*(455 + 0.8*icfa)*0.8)/365)*1000 #power per day W use Phius calc
    PhiusMELs = ((413 + 69*Nbr + 0.91*icfa)/365)*1000*0.8 #consumption per day per phius calc
    rangeElec = ((331 + 39*Nbr)/365)*1000
    clothesDryer = ((12.4*(164+46.5*Nbr)*1.18/3.01*(2.874/0.817-704/392)/(0.2184*(4.5*4.08+0.24)))/365)*1000
    clothesWasher = (120/365)*1000
    dishWasher = (((86.3 + (47.73 / (215 / 269)))/215) * ((88.4 + 34.9*Nbr)*(12/12))*(1/365)*1000)
    
    # DHW Calc per BA
    DHW_ClothesWasher = 2.3 + 0.78*Nbr
    DHW_Dishwasher = 2.26 + 0.75*Nbr
    DHW_Shower = 0.83*(14 + 1.17*Nbr)
    DHW_Bath = 0.83*(3.5+1.17*Nbr)
    DHW_Sinks = 0.83*(12.5+4.16*Nbr)
    DHW_CombinedGPM = (DHW_ClothesWasher + DHW_Dishwasher + DHW_Shower + DHW_Bath + DHW_Sinks)*4.381E-8

    # Sizing loads from ASHRAE 1199-RP

    G_0s = 136  #in W
    G_0l = 20  #in W
    G_cfs = 2.2  #in W
    G_cfl = 0.22  #in W
    G_ocs = 22  #in W
    G_ocl = 12  #in W

    sizingLoadSensible = G_0s + G_cfs*icfa_M + G_ocs*occ
    sizingLoadLatent = G_0l + G_cfl*icfa_M + G_ocl*occ

    # Envelope

    flowCoefficient = runList['FLOW_COEFFICIENT [SI]'][runCount]
    Ext_Window1_Ufactor = runList['EXT_WINDOW_1_U-FACTOR'][runCount]
    Ext_Window1_SHGC = runList['EXT_WINDOW_1_SHGC'][runCount]

    Ext_Wall1 = runList['EXT_WALL_1_NAME'][runCount]
    Ext_Roof1 = runList['EXT_ROOF_1_NAME'][runCount]
    Ext_Floor1 = runList['EXT_FLOOR_1_NAME'][runCount]
    Ext_Door1 = runList['EXT_DOOR_1_NAME'][runCount]
    Int_Floor1 = runList['INT_FLOOR_1_NAME'][runCount]

    # Schedule Based Inputs 
    outage1start = runList['OUTAGE_1_START'][runCount]
    outage1end = runList['OUTAGE_1_END'][runCount]
    outage2start = runList['OUTAGE_2_START'][runCount]
    outage2end = runList['OUTAGE_2_END'][runCount]
    outage1type = runList['1ST_OUTAGE'][runCount]

    if outage1type == 'HEATING':
        heatingOutageStart = outage1start
        heatingOutageEnd = outage1end
        coolingOutageStart = outage2start
        coolingOutageEnd = outage2end
    else:
        heatingOutageStart = outage2start
        heatingOutageEnd = outage2end
        coolingOutageStart = outage1start
        coolingOutageEnd = outage1end 

    # Controls 
    NatVentType  = str(runList['NAT_VENT_TYPE'][runCount])
    NatVentAvail = runList['NAT_VENT_AVAIL'][runCount]
    shadingAvail = runList['SHADING_AVAIL'][runCount]
    demandCoolingAvail = runList['DEMAND_COOLING_AVAIL'][runCount]

    # Mechanical Inputs
    natGasPresent = runList['NATURAL_GAS'][runCount]
    dhwFuel = runList['WATER_HEATER_FUEL'][runCount]
    mechSystemType = runList['MECH_SYSTEM_TYPE'][runCount]

    gridRegion = runList['GRID_REGION'][runCount]

    #==============================================================================================================================
    # 4. Base IDF
    #==============================================================================================================================

    open(str(testingFile_BR), 'w')
    idfg = IDF(str(idfgName))
    ddy = IDF(ddyName)
    idf1 = IDF(str(testingFile_BR))

    # Copy in geometry from input file

    for zone in idfg.idfobjects['Zone']:
        idf1.copyidfobject(zone)

    for srf in idfg.idfobjects['BuildingSurface:Detailed']:
        idf1.copyidfobject(srf)

    count = -1
    windowNames = []
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
    zone.Floor_Area = (icfa_M)

    # High level model information
     
    idf1.newidfobject('Version',
        Version_Identifier = 9.5
        )

    idf1.newidfobject('SimulationControl',
        Do_Zone_Sizing_Calculation = 'Yes',
        Do_System_Sizing_Calculation = 'Yes',
        Do_Plant_Sizing_Calculation = 'No',
        Run_Simulation_for_Sizing_Periods = 'Yes',
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

    # IHG

    idf1.newidfobject('People',
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
    
    idf1.newidfobject('Lights',
        Name = 'PhiusLights',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Phius_Lighting',
        Design_Level_Calculation_Method = 'LightingLevel',
        Lighting_Level = PhiusLights,
        Fraction_Radiant = 0.6,
        Fraction_Visible = 0.2,
        EndUse_Subcategory = 'InteriorLights'
        )
    
    idf1.newidfobject('ElectricEquipment',
        Name = 'PhiusMELs',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Phius_MELs',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = PhiusMELs,
        EndUse_Subcategory = 'MELs'
        # Fraction_Radiant = 1,
        )

    idf1.newidfobject('ElectricEquipment',
        Name = 'Fridge',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'Always_On',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = fridge,
        Fraction_Radiant = 1,
        EndUse_Subcategory = 'Fridge'
        )
    
    idf1.newidfobject('ElectricEquipment',
        Name = 'Range',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BARangeSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = rangeElec,
        Fraction_Latent = 0.3,
        Fraction_Radiant = 0.4,
        EndUse_Subcategory = 'Range'
        )
    
    idf1.newidfobject('ElectricEquipment',
        Name = 'ClothesDryer',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BAClothesDryerSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = clothesDryer,
        Fraction_Latent = 0.05,
        Fraction_Radiant = 0.15,
        EndUse_Subcategory = 'ClothesDryer'
        )
    
    idf1.newidfobject('ElectricEquipment',
        Name = 'ClothesWasher',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BAClothesWasherSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = clothesWasher,
        Fraction_Latent = 0.0,
        Fraction_Radiant = 0.80,
        EndUse_Subcategory = 'ClothesWasher'
        )
    
    idf1.newidfobject('ElectricEquipment',
        Name = 'Dishwasher',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'BADishwasherSchedule',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = dishWasher,
        Fraction_Latent = 0.15,
        Fraction_Radiant = 0.60,
        EndUse_Subcategory = 'Dishwasher'
        )

    idf1.newidfobject('ElectricEquipment',
        Name = 'SizingSensible',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'SizingLoads',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = sizingLoadSensible)

    idf1.newidfobject('ElectricEquipment',
        Name = 'SizingLatent',
        Zone_or_ZoneList_Name = 'Zone 1',
        Schedule_Name = 'SizingLoads',
        Design_Level_Calculation_Method = 'EquipmentLevel',
        Design_Level = sizingLoadLatent,
        Fraction_Latent = 1.0)

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

    # Thermal Mass
    idf1.newidfobject('InternalMass',
        Name = 'Zone1 TM',
        Construction_Name = 'Thermal Mass', 
        Zone_or_ZoneList_Name = 'Zone 1',
        Surface_Area = icfa_M
        )
    
    idf1.newidfobject('InternalMass',
        Name = 'Partitions',
        Construction_Name = 'Interior Wall', 
        Zone_or_ZoneList_Name = 'Zone 1',
        Surface_Area = icfa_M
        )

    # Base materials 
    materialBuilder('M01 100mm brick', 'MediumRough', 0.1016, 0.89, 1920, 790)
    materialBuilder('G05 25mm wood', 'MediumSmooth', 0.0254, 0.15, 608, 1630)
    materialBuilder('F08 Metal surface', 'Smooth', 0.0008, 45.28, 7824, 500)
    materialBuilder('I01 25mm insulation board', 'MediumRough', 0.0254, 0.03, 43, 1210)
    materialBuilder('I02 50mm insulation board', 'MediumRough', 0.0508, 0.03, 43, 1210)
    materialBuilder('G01a 19mm gypsum board', 'MediumSmooth', 0.019, 0.16, 800, 1090)
    materialBuilder('M11 100mm lightweight concrete', 'MediumRough', 0.1016, 0.53, 1280, 840)
    materialBuilder('F16 Acoustic tile', 'MediumSmooth', 0.0191, 0.06, 368, 590)
    materialBuilder('M15 200mm heavyweight concrete', 'MediumRough', 0.2032, 1.95, 2240, 900)
    materialBuilder('M05 200mm concrete block', 'MediumRough', 0.1016, 1.11, 800, 920)
    materialBuilder('Mass wood', 'MediumSmooth', 0.065532, 0.15, 608.701223809829, 1630)
    materialBuilder('Foundation EPS', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
    materialBuilder('EPS', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
    materialBuilder('F11 Wood siding', 'MediumSmooth', 0.0127, 0.09, 592, 1170)
    materialBuilder('R-11 3.5in Wood Stud', 'VeryRough', 0.0889, 0.05426246, 19, 960)
    materialBuilder('Plywood (Douglas Fir) - 12.7mm', 'Smooth', 0.0127, 0.12, 540, 1210)
    materialBuilder('EPS 1in', 'MediumSmooth', 0.0254, 0.02884, 29, 1210)
    materialBuilder('EPS 1.625in', 'MediumSmooth', 0.041275, 0.02884, 29, 1210)
    materialBuilder('EPS 2in', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
    materialBuilder('EPS 4in', 'MediumSmooth', 0.1016, 0.02884, 29, 1210 )
    materialBuilder('EPS 6in', 'MediumSmooth', 0.1524, 0.02884, 29, 1210)
    materialBuilder('EPS 7.5in', 'MediumSmooth', 0.1905, 0.02884, 29, 1210)
    materialBuilder('EPS 9in', 'MediumSmooth', 0.1524, 0.02884, 29, 1210)
    materialBuilder('EPS 14in', 'MediumSmooth', 0.3556, 0.02884, 29, 1210)
    materialBuilder('FG Attic R-19', 'MediumRough', 0.13716, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-30', 'MediumRough', 0.21844, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-38', 'MediumRough', 0.275844, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-49', 'MediumRough', 0.3556, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-55', 'MediumRough', 0.3991229, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-60', 'MediumRough', 0.3556, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-75', 'MediumRough', 0.54356, 0.04119794, 64, 960)
    materialBuilder('FG Attic R-100', 'MediumRough', 0.72644, 0.04119794, 64, 960)
    materialBuilder('ccSF R-13', 'Rough', 0.05503418, 0.024033814, 32, 920)
    materialBuilder('ccSF R-19', 'Rough', 0.080433418, 0.024033814, 32, 920)
    materialBuilder('ccSF R-30', 'Rough', 0.127, 0.024033814, 32, 920)
    materialBuilder('ccSF R-38', 'Rough', 0.160866582, 0.024033814, 32, 920)
    materialBuilder('ccSF R-49', 'Rough', 0.207433418, 0.024033814, 32, 920)
    materialBuilder('StemWall UnIns', 'MediumRough', 0.003175, 0.53, 1280, 840)

    # Special materials: 

    idf1.newidfobject('Material:AirGap',
        Name = 'F04 Wall air space resistance',
        Thermal_Resistance = 0.15
        )

    idf1.newidfobject('Material:AirGap',
        Name = 'F05 Ceiling air space resistance',
        Thermal_Resistance = 0.18
        )

    idf1.newidfobject('WindowMaterial:SimpleGlazingSystem',
        Name = 'ExteriorWindow1',
        UFactor = (Ext_Window1_Ufactor*5.678),
        Solar_Heat_Gain_Coefficient = Ext_Window1_SHGC
        )

    idf1.newidfobject('Construction',
        Name = 'ExteriorWindow1',
        Outside_Layer = 'ExteriorWindow1')
    
    # Shade Materials:

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
    
    idf1.newidfobject('WindowMaterial:Shade',
        Name = 'MEDIUM REFLECT - MEDIUM TRANS SHADE',
        Solar_Transmittance = 0.4,
        Solar_Reflectance = 0.5,
        Visible_Transmittance = 0.4,
        Visible_Reflectance = 0.5,
        Infrared_Hemispherical_Emissivity = 0.9,
        Infrared_Transmittance = 0,
        Thickness = 0.005,
        Conductivity = 0.1,
        Shade_to_Glass_Distance = 0.05,
        Top_Opening_Multiplier = 0.5,
        Bottom_Opening_Multiplier = 0.5,
        LeftSide_Opening_Multiplier = 0.5,
        RightSide_Opening_Multiplier = 0.5,
        Airflow_Permeability = 0)

    idf1.newidfobject('WindowMaterial:Shade',
        Name = 'HIGH REFLECT - LOW TRANS SHADE',
        Solar_Transmittance = 0.1,
        Solar_Reflectance = 0.8,
        Visible_Transmittance = 0.1,
        Visible_Reflectance = 0.8,
        Infrared_Hemispherical_Emissivity = 0.9,
        Infrared_Transmittance = 0,
        Thickness = 0.005,
        Conductivity = 0.1,
        Shade_to_Glass_Distance = 0.05,
        Top_Opening_Multiplier = 0.5,
        Bottom_Opening_Multiplier = 0.5,
        LeftSide_Opening_Multiplier = 0.5,
        RightSide_Opening_Multiplier = 0.5,
        Airflow_Permeability = 0)
    
    # Shading controls minus schedules: 

    runs = windowNames
    params = [x for x in runs]
    values = {}
    for i,param in enumerate(params):
        values['Fenestration_Surface_' + str(i+1) + '_Name'] = param
    idf1.newidfobject('WindowShadingControl',
    Name = 'Shading Control',
    Zone_Name = 'Zone 1',
    Shading_Control_Sequence_Number = 1,
    Shading_Type = 'ExteriorShade',
    Shading_Control_Type = 'OnIfHighSolarOnWindow',
    Schedule_Name = 'ShadingAvailable',
    Setpoint = 100,
    Shading_Control_Is_Scheduled = 'Yes',
    Glare_Control_Is_Active = 'No',
    Shading_Device_Material_Name = 'HIGH REFLECT - LOW TRANS SHADE',
    Type_of_Slat_Angle_Control_for_Blinds = 'FixedSlatAngle',
    Multiple_Surface_Control_Type = 'Sequential',
    **values)

    # Operable Windows:

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

    idf1.newidfobject('ZoneVentilation:WindandStackOpenArea',
        Name = 'OperableWindows-E',
        Zone_Name = 'Zone 1',
        Opening_Area = operableArea_E,
        Opening_Area_Fraction_Schedule_Name = 'WindowFraction2',
        Opening_Effectiveness = 'autocalculate',
        Effective_Angle = 90,
        Height_Difference = halfHeight,
        Discharge_Coefficient_for_Opening = 'autocalculate',
        Minimum_Indoor_Temperature = 15,
        Maximum_Indoor_Temperature = 100,
        Delta_Temperature = -100,
        Minimum_Outdoor_Temperature = -100,
        Maximum_Outdoor_Temperature = 100,
        Maximum_Wind_Speed = 10
        )

    idf1.newidfobject('ZoneVentilation:WindandStackOpenArea',
        Name = 'OperableWindows-S',
        Zone_Name = 'Zone 1',
        Opening_Area = operableArea_S,
        Opening_Area_Fraction_Schedule_Name = 'WindowFraction2',
        Opening_Effectiveness = 'autocalculate',
        Effective_Angle = 180,
        Height_Difference = halfHeight,
        Discharge_Coefficient_for_Opening = 'autocalculate',
        Minimum_Indoor_Temperature = 15,
        Maximum_Indoor_Temperature = 100,
        Delta_Temperature = -100,
        Minimum_Outdoor_Temperature = -100,
        Maximum_Outdoor_Temperature = 100,
        Maximum_Wind_Speed = 10
        )

    idf1.newidfobject('ZoneVentilation:WindandStackOpenArea',
        Name = 'OperableWindows-W',
        Zone_Name = 'Zone 1',
        Opening_Area = operableArea_W,
        Opening_Area_Fraction_Schedule_Name = 'WindowFraction2',
        Opening_Effectiveness = 'autocalculate',
        Effective_Angle = 270,
        Height_Difference = halfHeight,
        Discharge_Coefficient_for_Opening = 'autocalculate',
        Minimum_Indoor_Temperature = 15,
        Maximum_Indoor_Temperature = 100,
        Delta_Temperature = -100,
        Minimum_Outdoor_Temperature = -100,
        Maximum_Outdoor_Temperature = 100,
        Maximum_Wind_Speed = 10
        )

    # Base constructions:

    constructionBuilder('Brick Wall', ['M01 100mm brick'])
    constructionBuilder('Ext_Door1',['G05 25mm wood'])
    constructionBuilder('Thermal Mass',['G05 25mm wood'])
    constructionBuilder('Interior Floor', ['Plywood (Douglas Fir) - 12.7mm', 'F05 Ceiling air space resistance', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Slab UnIns', ['M15 200mm heavyweight concrete'])
    constructionBuilder('Exterior Slab + 2in EPS', ['EPS 2in', 'M15 200mm heavyweight concrete'])
    constructionBuilder('Exterior Wall', ['F11 Wood siding', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Interior Wall', ['G01a 19mm gypsum board', 'F04 Wall air space resistance', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof', ['FG Attic R-19', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Door', ['F08 Metal surface', 'I02 50mm insulation board', 'F08 Metal surface'])
    constructionBuilder('Interior Door', ['G05 25mm wood'])
    constructionBuilder('Exterior Wall +1in EPS', ['F11 Wood siding', 'EPS 1in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +1.625in EPS', ['F11 Wood siding', 'EPS 1.625in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +2in EPS', ['F11 Wood siding', 'EPS 2in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +4in EPS', ['F11 Wood siding', 'EPS 4in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +7.5in EPS', ['F11 Wood siding', 'EPS 7.5in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +6in EPS', ['F11 Wood siding', 'EPS 6in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +9in EPS', ['F11 Wood siding', 'EPS 9in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Wall +14in EPS', ['F11 Wood siding', 'EPS 14in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-30', ['FG Attic R-30', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-38', ['FG Attic R-38', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-49', ['FG Attic R-49', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-55', ['FG Attic R-55', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-60', ['FG Attic R-60', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-75', ['FG Attic R-75', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('Exterior Roof R-100', ['FG Attic R-100', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
    constructionBuilder('P+B UnIns', ['Plywood (Douglas Fir) - 12.7mm', 'F05 Ceiling air space resistance', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
    constructionBuilder('P+B R-13', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-13', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
    constructionBuilder('P+B R-19', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-19', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
    constructionBuilder('P+B R-30', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-30', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
    constructionBuilder('P+B R-38', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-38', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
    constructionBuilder('P+B R-49', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-49', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])

    # Change Constructions:
    
    count = -1
    for srf in idf1.idfobjects['BuildingSurface:Detailed']:
        count += 1
        surface = idf1.idfobjects['BuildingSurface:Detailed'][count]
        if surface.Construction_Name == 'Ext_Wall1':
            surface.Construction_Name = str(Ext_Wall1)
        if surface.Construction_Name == 'Ext_Roof1':
            surface.Construction_Name = str(Ext_Roof1)
        if surface.Construction_Name == 'Ext_Floor1':
            surface.Construction_Name = str(Ext_Floor1)
        if surface.Construction_Name == 'Ext_Door1':
            surface.Construction_Name = str(Ext_Door1)
        if surface.Construction_Name == 'Int_Floor1':
            surface.Construction_Name = str(Int_Floor1)

    count = -1
    for fen in idf1.idfobjects['FenestrationSurface:Detailed']:
        count += 1
        window = idf1.idfobjects['FenestrationSurface:Detailed'][count]
        if window.Construction_Name == 'Ext_Window1':
            window.Construction_Name = 'ExteriorWindow1'

    # KIVA foundation inteface:

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

    # Sizing settings:
    
    idf1.newidfobject('DesignSpecification:OutdoorAir',
        Name = 'SZ_DSOA_Zone_1',
        Outdoor_Air_Method = 'Flow/Person',
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
        Design_Specification_Zone_Air_Distribution_Object_Name = 'SZ_DSZAD_Zone_1',
        Zone_Heating_Sizing_Factor = 2,
        Zone_Cooling_Sizing_Factor = 1.5
        )
    
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

    # Mechanical Zone Connections

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
        Node_2_Name = 'Zone1MECHAirOutletNode'
        )

    idf1.newidfobject('NodeList',
        Name = 'Zone_1_Returns',
        Node_1_Name = 'Zone_1_Return'
        )

    idf1.newidfobject('NodeList',
        Name = 'Zone_1_Exhausts',
        Node_1_Name = 'Zone_1_ERV_Exhaust',
        Node_2_Name = 'Zone1MECHAirInletNode'
        )

    # Heat Pump:
    if mechSystemType == 'PTHP':

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

        idf1.newidfobject('ZoneHVAC:PackagedTerminalHeatPump',
            Name = 'Zone1PTHP',
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = 'Zone1MECHAirInletNode',
            Air_Outlet_Node_Name = 'Zone1MECHAirOutletNode',
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
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = 'Zone1MECHAirInletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPFanOutletNode',
            Design_Maximum_Air_Flow_Rate = 'autosize',
            Speed_Control_Method = 'Continuous',
            Electric_Power_Minimum_Flow_Rate_Fraction = 0.0,
            Design_Pressure_Rise = 160,
            Motor_Efficiency = 0.9,
            Motor_In_Air_Stream_Fraction = 1.0,
            Design_Electric_Power_Consumption = 'autosize',
            Design_Power_Sizing_Method = 'TotalEfficiencyAndPressure',
            # Electric_Power_Per_Unit_Flow_Rate_{W/(m3/s)}
            # Electric_Power_Per_Unit_Flow_Rate_Per_Unit_Pressure_{W/((m3/s)-Pa)}
            Fan_Total_Efficiency = 0.5,
            Electric_Power_Function_of_Flow_Fraction_Curve_Name = 'CombinedPowerAndFanEff'
            )

        idf1.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = 'Zone1PTHPDXCoolCoil',
            Availability_Schedule_Name = 'MechAvailable',
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
            Availability_Schedule_Name = 'MechAvailable',
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
            Crankcase_Heater_Capacity = 0,
            Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater_Operation = 10.0,
            Defrost_Strategy = 'Resistive',
            Defrost_Control = 'TIMED',
            Defrost_Time_Period_Fraction = 0.166667,
            Resistive_Defrost_Heater_Capacity = 'autosize'
            )

        idf1.newidfobject('Coil:Heating:Electric',
            Name = 'Zone1PTHPSupHeater',
            Availability_Schedule_Name = 'MechAvailable',
            Efficiency = 1.0,
            Nominal_Capacity = 'autosize',
            Air_Inlet_Node_Name = 'Zone1PTHPDXHeatCoilOutletNode',
            Air_Outlet_Node_Name = 'Zone1MECHAirOutletNode'
            )
        
    if mechSystemType == 'GasFurnaceDXAC':

        idf1.newidfobject('ZoneHVAC:EquipmentList',
            Name = 'Zone_1_Equipment',
            Load_Distribution_Scheme = 'SequentialLoad',
            Zone_Equipment_1_Object_Type = 'ZoneHVAC:EnergyRecoveryVentilator',
            Zone_Equipment_1_Name = 'ERV1',
            Zone_Equipment_1_Cooling_Sequence = 2,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence = 2,
            Zone_Equipment_2_Object_Type = 'AirLoopHVAC:UnitarySystem',
            Zone_Equipment_2_Name = 'GasHeatDXACFurnace',
            Zone_Equipment_2_Cooling_Sequence = 1,
            Zone_Equipment_2_Heating_or_NoLoad_Sequence = 1
            #Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name = 
            #Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name = 
            )
           
        idf1.newidfobject('AirLoopHVAC:UnitarySystem',
            Name = 'GasHeatDXACFurnace',
            Control_Type = 'Load',
            Controlling_Zone_or_Thermostat_Location  ='Zone 1',
            Dehumidification_Control_Type = 'None',
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = 'Zone1MECHAirInletNode',
            Air_Outlet_Node_Name = 'Zone1MECHAirOutletNode',
            Supply_Fan_Object_Type = 'Fan:OnOff',
            Supply_Fan_Name = 'FurnaceBlower',
            Fan_Placement = 'BlowThrough',
            Heating_Coil_Object_Type = 'Coil:Heating:Fuel',
            Heating_Coil_Name = 'Furnace Heating Coil 1',
            Cooling_Coil_Object_Type = 'Coil:Cooling:DX:SingleSpeed',
            Cooling_Coil_Name = 'Furnace ACDXCoil 1',
            Cooling_Supply_Air_Flow_Rate = 'autosize',
            Heating_Supply_Air_Flow_Rate = 'autosize',
            No_Load_Supply_Air_Flow_Rate = 0,
            Maximum_Supply_Air_Temperature = 50,
            )

        idf1.newidfobject('Coil:Heating:Fuel',
            Name = 'Furnace Heating Coil 1',
            Availability_Schedule_Name = 'MechAvailable',
            Fuel_Type = 'NaturalGas',
            Burner_Efficiency = 0.8,
            Nominal_Capacity = 'autosize',
            Air_Inlet_Node_Name = 'Heating Coil Air Inlet Node',
            Air_Outlet_Node_Name = 'Zone1MECHAirOutletNode',
            )
        
        idf1.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = 'Furnace ACDXCoil 1',
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Total_Cooling_Capacity = 'autosize',
            Gross_Rated_Sensible_Heat_Ratio = 0.75,
            Gross_Rated_Cooling_COP = 3.0,  # Change to var for future shit
            Rated_Air_Flow_Rate = 'autosize',
            Air_Inlet_Node_Name = 'DX Cooling Coil Air Inlet Node',
            Air_Outlet_Node_Name  = 'Heating Coil Air Inlet Node',
            Total_Cooling_Capacity_Function_of_Temperature_Curve_Name = 'HPACCoolCapFT',
            Total_Cooling_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACCoolCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACPLFFPLR'
            )

        idf1.newidfobject('Fan:OnOff',
            Name = 'FurnaceBlower',
            Availability_Schedule_Name = 'MechAvailable',
            Fan_Total_Efficiency = 0.7,
            Pressure_Rise = 225,
            Maximum_Flow_Rate = 2,
            Motor_Efficiency = 0.9,
            Motor_In_Airstream_Fraction = 1.0,
            Air_Inlet_Node_Name = 'Zone1MECHAirInletNode',
            Air_Outlet_Node_Name = 'DX Cooling Coil Air Inlet Node'
            )

        # idf1.newidfobject('AirTerminal:SingleDuct:ConstantVolume:NoReheat',
        #     Name = 'Zone1DirectAir',
        #     Availability_Schedule_Name = 'MechAvailable',
        #     Air_Inlet_Node_Name = 'Air Loop Outlet Node',
        #     Air_Outlet_Node_Name = 'Zone1MECHAirOutletNode',
        #     Maximum_Air_Flow_Rate = 2
        #     )

    # DHW
    
    idf1.newidfobject('WaterHeater:Mixed',
        Name = 'ElectricWaterHeater_50Gal',
        Tank_Volume = 0.1892706,
        Setpoint_Temperature_Schedule_Name = 'DHW_122F',
        # Deadband Temperature Difference
        Maximum_Temperature_Limit = 82.2222,
        Heater_Control_Type = 'MODULATE',
        Heater_Maximum_Capacity = 11712,
        Heater_Minimum_Capacity = 0,
        # Heater Ignition Minimum Flow Rate {m3/s}
        # Heater Ignition Delay {s}
        Heater_Fuel_Type = str(dhwFuel),
        Heater_Thermal_Efficiency = 0.95,
        # Part Load Factor Curve Name
        Off_Cycle_Parasitic_Fuel_Consumption_Rate = 10,
        Off_Cycle_Parasitic_Fuel_Type = 'ELECTRICITY',
        Off_Cycle_Parasitic_Heat_Fraction_to_Tank = 0,
        On_Cycle_Parasitic_Fuel_Consumption_Rate = 30,
        On_Cycle_Parasitic_Fuel_Type = 'ELECTRICITY',
        On_Cycle_Parasitic_Heat_Fraction_to_Tank = 0,
        Ambient_Temperature_Indicator = 'ZONE',
        # Ambient Temperature Schedule Name
        Ambient_Temperature_Zone_Name = 'Zone 1',
        # Ambient Temperature Outdoor Air Node Name
        Off_Cycle_Loss_Coefficient_to_Ambient_Temperature = 2.36,
        # Off Cycle Loss Fraction to Zone
        # On Cycle Loss Coefficient to Ambient Temperature {W/K}
        # On Cycle Loss Fraction to Zone
        Peak_Use_Flow_Rate = DHW_CombinedGPM,
        Use_Flow_Rate_Fraction_Schedule_Name = 'CombinedDHWSchedule'
        # Cold Water Supply Temperature Schedule Name
        )

    # Renewables

    idf1.newidfobject('DemandManagerAssignmentList',
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

    idf1.newidfobject('DemandManager:Thermostats',
        Name = 'Set Backs',
        Availability_Schedule_Name = 'Demand Control Cooling', 
        Reset_Control = 'Fixed',
        Minimum_Reset_Duration = 30,
        Maximum_Heating_Setpoint_Reset = 20,
        Maximum_Cooling_Setpoint_Reset = 28.8888888888889,
        # Reset_Step_Change = ,
        Selection_Control = 'All',
        # Rotation_Duration = ,
        Thermostat_1_Name = 'Zone_1_Thermostat')

    idf1.newidfobject('Generator:PVWatts',
        Name = '3 kW PV',
        PVWatts_Version = 5,
        DC_System_Capacity = 3000,
        Module_Type = 'Standard',
        Array_Type = 'FixedOpenRack',
        System_Losses = 0.14,
        Array_Geometry_Type = 'TiltAzimuth',
        Tilt_Angle = 57,
        Azimuth_Angle = 180,
        # Surface_Name = ,
        Ground_Coverage_Ratio = 0.4)

    idf1.newidfobject('ElectricLoadCenter:Inverter:PVWatts',
        Name = 'PV Inverter',
        DC_to_AC_Size_Ratio = 1.1,
        Inverter_Efficiency = 0.96)

    idf1.newidfobject('ElectricLoadCenter:Generators',
        Name = 'PV',
        Generator_1_Name = '3 kW PV',
        Generator_1_Object_Type = 'Generator:PVWatts',
        Generator_1_Rated_Electric_Power_Output = 3000,
        Generator_1_Availability_Schedule_Name = 'Always_On')
        # Generator_1_Rated_Thermal_to_Electrical_Power_Ratio = )

    idf1.newidfobject('ElectricLoadCenter:Storage:Simple',
        Name = 'Simple Battery',
        Availability_Schedule_Name = 'Always_On',
        Zone_Name = 'Zone 1',
        Radiative_Fraction_for_Zone_Heat_Gains = 0.9,
        Nominal_Energetic_Efficiency_for_Charging = 0.9,
        Nominal_Discharging_Energetic_Efficiency = 0.9,
        Maximum_Storage_Capacity = 10800000,
        # Maximum_Power_for_Discharging = ,
        # Maximum_Power_for_Charging = ,
        Initial_State_of_Charge = 10800000)

    idf1.newidfobject('ElectricLoadCenter:Transformer',
        Name = 'Transformer',
        Availability_Schedule_Name = 'Always_On',
        Transformer_Usage = 'LoadCenterPowerConditioning',
        Zone_Name = 'Zone 1',
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

    idf1.newidfobject('ElectricLoadCenter:Distribution',
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

    idf1.newidfobject('ElectricLoadCenter:Storage:Converter',
        Name = 'Converter',
        Availability_Schedule_Name = 'Always_On',
        Power_Conversion_Efficiency_Method = 'SimpleFixed',
        Simple_Fixed_Efficiency = 0.95)

    # Curves: 

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

    # Costs
    costBuilder('Wall 1', '','Construction', 'Exterior Wall +1in EPS','','',13.77915008)
    costBuilder('Wall 2', '','Construction', 'Exterior Wall +1.625in EPS','','',16.79333916)
    costBuilder('Wall 3', '','Construction', 'Exterior Wall +2in EPS','','',18.62338253)
    costBuilder('Wall 4', '','Construction', 'Exterior Wall +4in EPS','','',25.40530796)
    costBuilder('Wall 5', '','Construction', 'Exterior Wall +6in EPS','','',34.55552481)
    costBuilder('Wall 6', '','Construction', 'Exterior Wall +9in EPS','','',46.93522996)
    costBuilder('Wall 7', '','Construction', 'Exterior Wall +14in EPS','','',63.6209195100001)

    costBuilder('Roof 1', '','Construction', 'Exterior Roof R-30','','',7.96607114000001)
    costBuilder('Roof 2', '','Construction', 'Exterior Roof R-49','','',8.39666958000001)
    costBuilder('Roof 3', '','Construction', 'Exterior Roof R-60','','',21.529922)
    costBuilder('Roof 4', '','Construction', 'Exterior Roof R-75','','',39.39975726)
    costBuilder('Roof 5', '','Construction', 'Exterior Roof R-100','','',69.3263488400001)

    # costBuilder('Roof 5', '','Construction', 'Exterior Roof R-100','','',69.3263488400001)

    costBuilder('Window 1', '','Construction', 'ExteriorWindow1','','',(147*math.exp(0.23*Ext_Window1_Ufactor)))


    # ============================================================================
    # Pass IDF 
    # ============================================================================
    
    idf1.saveas(str(passIDF))

    # ============================================================================
    # Resilience Specific
    # ============================================================================

    idf1 = IDF(str(passIDF))

    # ERV

    idf1.newidfobject('ZoneHVAC:EnergyRecoveryVentilator',
        Name = 'ERV1',
        Availability_Schedule_Name = 'ERVAvailable',
        Heat_Exchanger_Name = 'ERV_Core',
        Supply_Air_Flow_Rate = (0.00235973725*occ),
        Exhaust_Air_Flow_Rate = (0.00235973725*occ),
        Supply_Air_Fan_Name = 'ERV_Supply_Fan',
        Exhaust_Air_Fan_Name = 'ERV_Exhaust_Fan'
        )

    idf1.newidfobject('Fan:OnOff',
        Name = 'ERV_Supply_Fan',
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = 'ERV_Core_Sup_Out',
        Air_Outlet_Node_Name = 'Zone_1_ERV_Supply',
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf1.newidfobject('Fan:OnOff',
        Name = 'ERV_Exhaust_Fan',
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = 'ERV_Core_Exh_Out',
        Air_Outlet_Node_Name = 'Zone_1_ERV_Exhaust',
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf1.newidfobject('HeatExchanger:AirToAir:SensibleAndLatent',
        Name = 'ERV_Core',
        Availability_Schedule_Name = 'ERVAvailable',
        Nominal_Supply_Air_Flow_Rate = 0.047,
        Sensible_Effectiveness_at_100_Heating_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Heating_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Heating_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Heating_Air_Flow = (ervLatent * 1.1),
        Sensible_Effectiveness_at_100_Cooling_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Cooling_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Cooling_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Cooling_Air_Flow =  (ervLatent * 1.1),
        Supply_Air_Inlet_Node_Name = 'OA_1',
        Supply_Air_Outlet_Node_Name = 'ERV_Core_Sup_Out',
        Exhaust_Air_Inlet_Node_Name = 'Zone_1_ERV_Exhaust',
        Exhaust_Air_Outlet_Node_Name = 'ERV_Core_Exh_Out',
        Supply_Air_Outlet_Temperature_Control = 'No',
        Heat_Exchanger_Type = 'Plate',
        Frost_Control_Type = 'ExhaustAirRecirculation',
        Threshold_Temperature = -10,
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


    # Outputs

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

    outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature', 'Exterior Lights Electricity Energy', 
                'Zone Ventilation Mass Flow Rate', 'Schedule Value', 'Electric Equipment Electricity Energy',
                'Facility Total Purchased Electricity Energy']
    meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity', 'ElectricityNet:Facility',
                 'NaturalGas:Facility'] 
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

    # Schedules for outage simulation:

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Number')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Any Number')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Fraction')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'On/Off')

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
        Name = 'DHW_122F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 2
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
        Name = 'OccupantSchedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1
        )

    idf1.newidfobject('Schedule:Constant',
        Name = 'ERVAvailable',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )

    idf1.newidfobject('Schedule:Compact',
        Name = 'MechAvailable',
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

    idf1.newidfobject('Schedule:Compact',
        Name = 'NatVent',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0,
        Field_8 = ('Through: ' + str(coolingOutageEnd)),
        Field_9 = 'For: SummerDesignDay',
        Field_10 = 'Until: 24:00',
        Field_11 = 0,
        Field_12 = 'For: AllOtherDays',
        Field_13  ='Until: 24:00',
        Field_14 = NatVentAvail,
        Field_15 = 'Through: 12/31', 
        Field_16 = 'For: AllDays',
        Field_17 = 'Until: 24:00',
        Field_18 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'SchNatVent',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0,
        Field_8 = ('Through: ' + str(coolingOutageEnd)),
        Field_9 = 'For: SummerDesignDay',
        Field_10 = 'Until: 24:00',
        Field_11 = 0,
        Field_12 = 'For: AllOtherDays',
        Field_13  ='Until: 24:00',
        Field_14 = NatVentAvail,
        Field_15 = 'Through: 12/31', 
        Field_16 = 'For: AllDays',
        Field_17 = 'Until: 24:00',
        Field_18 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'OutageCooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 0,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 1)

    idf1.newidfobject('Schedule:Compact',
        Name = 'Demand Control Cooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = demandCoolingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'ShadingAvailable',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = shadingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'SizingLoads',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0)
    # Zero Schedules 

    zeroSch('BARangeSchedule')
    zeroSch('Phius_Lighting')
    zeroSch('Phius_MELs')
    zeroSch('CombinedDHWSchedule')
    zeroSch('BAClothesDryerSchedule')
    zeroSch('BAClothesWasherSchedule')
    zeroSch('BADishwasherSchedule')

    # Resilience Controls

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'IWB',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'Zone_1_Zone_Air_Node',
        OutputVariable_or_OutputMeter_Name = 'System Node Wetbulb Temperature')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'OWB',
        OutputVariable_or_OutputMeter_Index_Key_Name ='*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Wetbulb Temperature')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'IDB',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'Zone 1',
        OutputVariable_or_OutputMeter_Name = 'Zone Air Temperature')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'ODB',
        OutputVariable_or_OutputMeter_Index_Key_Name ='*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Drybulb Temperature')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'NatVentAvail',
        OutputVariable_or_OutputMeter_Index_Key_Name = str(NatVentType),
        OutputVariable_or_OutputMeter_Name = 'Schedule Value')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'Clock',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'PhiusExtLight',
        OutputVariable_or_OutputMeter_Name = 'Exterior Lights Electricity Energy')

    idf1.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'PV',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'ELC',
        OutputVariable_or_OutputMeter_Name = 'Electric Load Center Produced Electricity Energy')

    idf1.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'WindowEconomizer',
        Actuated_Component_Unique_Name = 'WindowFraction2',
        Actuated_Component_Type = 'Schedule:Constant',
        Actuated_Component_Control_Type = 'Schedule Value')

    idf1.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'DC_Coolings',
        Actuated_Component_Unique_Name = 'Demand Control Cooling',
        Actuated_Component_Type = 'Schedule:Compact',
        Actuated_Component_Control_Type = 'Schedule Value')

    idf1.newidfobject('EnergyManagementSystem:ProgramCallingManager',
        Name = 'CO2Caller',
        EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
        Program_Name_1 = 'SummerVentDB')

    idf1.newidfobject('EnergyManagementSystem:Program',
        Name = 'SummerVentWB',
        Program_Line_1 = 'IF IWB> 1+ OWB && NatVentAvail > 0 && Clock > 0',
        Program_Line_2 = 'SET WindowEconomizer = 1',
        Program_Line_3 = 'SET DC_Coolings = 0',
        Program_Line_4 = 'ELSE',
        Program_Line_5 = 'SET WindowEconomizer = 0',
        Program_Line_6 = 'ENDIF')

    idf1.newidfobject('EnergyManagementSystem:Program',
        Name = 'SummerVentDB',
        Program_Line_1 = 'IF IDB> 1+ ODB && NatVentAvail > 0 && Clock > 0',
        Program_Line_2 = 'SET WindowEconomizer = 1',
        Program_Line_3 = 'SET DC_Coolings = 0',
        Program_Line_4 = 'ELSE',
        Program_Line_5 = 'SET WindowEconomizer = 0',
        Program_Line_6 = 'ENDIF')

    # Program_Line_1 = 'IF IWB> 1+ OWB AND NatVentAvail > 0 AND Clock == 0',

    # ==================================================================================================================================
    # Run Resilience Simulation and Collect Results
    # ==================================================================================================================================

    # add the index in from the for loop for the number of runs to make this table happen faster

    idf1.saveas(str(testingFile_BR))
    idf = IDF(str(testingFile_BR), str(epwFile))
    idf.run(readvars=True)

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


    # Resilience Graphs

    filehandle = (str(studyFolder) + '\eplusout.csv')
    hourly = pd.read_csv(filehandle)

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

    heatingOutageStart1 = datetime.datetime.strptime((str(heatingOutageStart) + '/' + str(2020)), '%m/%d/%Y') + datetime.timedelta(hours=24)
    coolingOutageStart1 = datetime.datetime.strptime((str(coolingOutageStart) + '/' + str(2020)), '%m/%d/%Y') + datetime.timedelta(hours=24)
    heatingOutageEnd1 = datetime.datetime.strptime((str(heatingOutageEnd) + '/' + str(2020)), '%m/%d/%Y') + datetime.timedelta(hours=23)
    coolingOutageEnd1 = datetime.datetime.strptime((str(coolingOutageEnd) + '/' + str(2020)), '%m/%d/%Y') + datetime.timedelta(hours=23)

    maskh = (hourly['DateTime'] >= heatingOutageStart1) & (hourly['DateTime'] <= heatingOutageEnd1)
    maskc = (hourly['DateTime'] >= coolingOutageStart1) & (hourly['DateTime'] <= coolingOutageEnd1)

    hourlyHeat = hourly.loc[maskh]
    hourlyCool = hourly.loc[maskc]

    x = hourlyHeat['DateTime']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, sharey=True,constrained_layout=False)
    fig.suptitle((str(caseName) + '_Heating Outage Resilience'), fontsize='x-large')
    ax1.plot(x,hourlyHeat["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"], label="Site Dry Bulb [C]", linestyle='dashed')
    ax1.plot(x,hourlyHeat["ZONE 1:Zone Air Temperature [C](Hourly)"], label="Zone Dry Bulb [C]")
    ax2.plot(x,hourlyHeat['ZONE 1:Zone Air Relative Humidity [%](Hourly)'], label=("Zone RH"))
    ax1.grid(True)
    ax1.set_ylabel('Temperature [C]')
    ax1.legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax2.legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax2.grid(True)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Relative Humidity [%]')

    plt.savefig(str(studyFolder) + "/" + str(BaseFileName) + "_Heating Outage Resilience Graphs.png", dpi=300)

    x = hourlyCool['DateTime']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, sharey=True,constrained_layout=False)
    fig.suptitle((str(caseName) + '_Cooling Outage Resilience'), fontsize='x-large')
    ax1.plot(x,hourlyCool["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"], label="Site Dry Bulb [C]", linestyle='dashed')
    ax1.plot(x,hourlyCool["ZONE 1:Zone Air Temperature [C](Hourly)"], label="Zone Dry Bulb [C]")
    ax2.plot(x,hourlyCool['ZONE 1:Zone Air Relative Humidity [%](Hourly)'], label=("Zone RH"))
    ax1.grid(True)
    ax1.set_ylabel('Temperature [C]')
    ax1.legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax2.legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax2.grid(True)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Relative Humidity [%]')

    plt.savefig(str(studyFolder) + "/" + str(BaseFileName) + "_Cooling Outage Resilience Graphs.png", dpi=300)

    # Battery Sizing
    heatingBattery = (hourlyHeat['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778
    coolingBattery = (hourlyCool['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778

    # hourlyHeat.to_csv(str(studyFolder) + "/" + str(BaseFileName) + "_hourlyHeat.csv")
    # hourlyCool.to_csv(str(studyFolder) + "/" + str(BaseFileName) + "_hourlyCool.csv")

    # Save HTML and CSV outputs
    reportHTML = (str(studyFolder) +'\eplustbl.htm')
    reportCSV = (str(studyFolder) + '\eplusout.csv')
    reportSQL= (str(studyFolder) + '\eplusout.sql')
    reportHTML2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BR_eplustbl.htm')
    reportCSV2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BR_eplusout.csv')
    reportSQL2= (str(studyFolder) + "/" + str(BaseFileName)  + '_BR_eplusout.sql')


    if os.path.exists(reportCSV2):
        os.remove(reportCSV2)
    
    if os.path.exists(reportHTML2):
        os.remove(reportHTML2)

    if os.path.exists(reportSQL2):
        os.remove(reportSQL2)

    os.rename(reportHTML,reportHTML2)
    os.rename(reportCSV,reportCSV2)
    os.rename(reportSQL,reportSQL2)

    # ============================================================================
    # Annual Specific
    # ============================================================================

    idf1 = IDF(str(passIDF))

    # ERV

    idf1.newidfobject('ZoneHVAC:EnergyRecoveryVentilator',
        Name = 'ERV1',
        Availability_Schedule_Name = 'ERVAvailable',
        Heat_Exchanger_Name = 'ERV_Core',
        Supply_Air_Flow_Rate = (0.00707921175*occ),
        Exhaust_Air_Flow_Rate = (0.00707921175*occ),
        Supply_Air_Fan_Name = 'ERV_Supply_Fan',
        Exhaust_Air_Fan_Name = 'ERV_Exhaust_Fan'
        )

    idf1.newidfobject('Fan:OnOff',
        Name = 'ERV_Supply_Fan',
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = 'ERV_Core_Sup_Out',
        Air_Outlet_Node_Name = 'Zone_1_ERV_Supply',
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf1.newidfobject('Fan:OnOff',
        Name = 'ERV_Exhaust_Fan',
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = 'ERV_Core_Exh_Out',
        Air_Outlet_Node_Name = 'Zone_1_ERV_Exhaust',
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf1.newidfobject('HeatExchanger:AirToAir:SensibleAndLatent',
        Name = 'ERV_Core',
        Availability_Schedule_Name = 'ERVAvailable',
        Nominal_Supply_Air_Flow_Rate = 0.047,
        Sensible_Effectiveness_at_100_Heating_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Heating_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Heating_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Heating_Air_Flow = (ervLatent * 1.1),
        Sensible_Effectiveness_at_100_Cooling_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Cooling_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Cooling_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Cooling_Air_Flow =  (ervLatent * 1.1),
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
    
    # Annual Outputs

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

    outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature', 'Exterior Lights Electricity Energy', 
                'Zone Ventilation Mass Flow Rate', 'Schedule Value', 'Electric Equipment Electricity Energy',
                'Facility Total Purchased Electricity Energy']
    meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity', 'ElectricityNet:Facility',
                 'NaturalGas:Facility']  
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

    # Schedules for Annual simulation: 

    SchName_Lighting = 'Phius_Lighting'
    SchValues_Lighting = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

    SchName_MELs = 'Phius_MELs'
    SchValues_MELs = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

    SchName_DHW = 'CombinedDHWSchedule'
    SchValues_DHW = [0.006, 0.003, 0.001, 0.001, 0.003, 0.022, 0.075, 0.079, 0.076, 0.067, 0.061, 0.048, 0.042, 0.037, 0.037, 0.033, 0.044, 0.058, 0.069, 0.065, 0.059, 0.048, 0.042, 0.023]

    SchName_Range = 'BARangeSchedule'
    SchValues_Range = [0.007,0.007,0.004,0.004,0.007,0.011,0.025,0.042,0.046,0.048,0.042,0.05,0.057,0.046,0.057,0.044,0.092,0.15,0.117,0.06,0.035,0.025,0.016,0.011]    

    SchName_ClothesDryer = 'BAClothesDryerSchedule'
    SchValues_ClothesDryer = [0.01,0.006,0.004,0.002,0.004,0.006,0.016,0.032,0.048,0.068,0.078,0.081,0.074,0.067,0.057,0.061,0.055,0.054,0.051,0.051,0.052,0.054,0.044,0.024]  

    SchName_ClothesWasher = 'BAClothesWasherSchedule'
    SchValues_ClothesWasher = [0.009,0.007,0.004,0.004,0.007,0.011,0.022,0.049,0.073,0.086,0.084,0.075,0.067,0.06,0.049,0.052,0.05,0.049,0.049,0.049,0.049,0.047,0.032,0.017]  

    SchName_Dishwasher = 'BADishwasherSchedule'
    SchValues_Dishwasher = [0.015,0.007,0.005,0.003,0.003,0.01,0.02,0.031,0.058,0.065,0.056,0.048,0.041,0.046,0.036,0.038,0.038,0.049,0.087,0.111,0.09,0.067,0.044,0.031]

    SchName_Occupant = 'OccupantSchedule'
    SchValues_Occupant = [0.015,0.007,0.005,0.003,0.003,0.01,0.02,0.031,0.058,0.065,0.056,0.048,0.041,0.046,0.036,0.038,0.038,0.049,0.087,0.111,0.09,0.067,0.044,0.031]

    hourSch(SchName_Lighting, SchValues_Lighting)
    hourSch(SchName_MELs, SchValues_MELs)
    hourSch(SchName_DHW, SchValues_DHW)
    hourSch(SchName_Range, SchValues_Range)
    hourSch(SchName_ClothesDryer, SchValues_ClothesDryer)
    hourSch(SchName_ClothesWasher, SchValues_ClothesWasher)
    hourSch(SchName_Dishwasher, SchValues_Dishwasher)
    hourSch(SchName_Occupant, SchValues_Occupant)

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Number')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Any Number')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'Fraction')

    idf1.newidfobject('ScheduleTypeLimits',
        Name = 'On/Off')

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
        Name = 'DHW_122F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 50
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

    idf1.newidfobject('Schedule:Constant',
        Name = 'ERVAvailable',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )
    
    # idf1.newidfobject('Schedule:Compact',
    #     Name = 'ERVAvailable',
    #     Schedule_Type_Limits_Name = 'Fraction',
    #     Field_1 = 'Through 12/31',
    #     Field_2 = 'For: AllDays',
    #     Field_3 = 'Until: 18:00',
    #     Field_4 = 0.0,
    #     Field_5 = 'Until: 19:30',
    #     Field_6 = 1.0,
    #     Field_7 = 'Until: 24:00',
    #     Field_8 = 0.0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'MechAvailable',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1.0,
        )

    idf1.newidfobject('Schedule:Compact',
        Name = 'OutageCooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 1,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 1)

    idf1.newidfobject('Schedule:Compact',
        Name = 'Demand Control Cooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 0,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'ShadingAvailable',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = shadingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf1.newidfobject('Schedule:Compact',
        Name = 'SizingLoads',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0)

    # Annual Result Collection

    idf1.saveas(str(testingFile_BA))
    idf = IDF(str(testingFile_BA), str(epwFile))
    idf.run(readvars=True)

    filehandle = (str(studyFolder) + '\eplusout.csv')
    filehandleMTR = (str(studyFolder) + '\eplusmtr.csv')
    hourly = pd.read_csv(filehandle)
    monthlyMTR= pd.read_csv(filehandleMTR)

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

    fname = (str(studyFolder) + '/eplustbl.htm')
    filehandle = open(fname, 'r').read()
    ltables = readhtml.lines_table(filehandle) # reads the tables with their titles

    for ltable in ltables:
        if 'Site and Source Energy' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
            eui = float(ltable[1][1][2])

    for ltable in ltables:
        if 'Annual and Peak Values - Electricity' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
            peakElec = float(ltable[1][1][4])

    if 'BASE' in str(BaseFileName):
        firstCost = 0
    else:
        for ltable in ltables:
            if 'Construction Cost Estimate Summary' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                firstCost = (float(ltable[1][9][2])*1.8)

    # Save HTML and CSV outputs
    reportHTML = (str(studyFolder) +'\eplustbl.htm')
    reportCSV = (str(studyFolder) + '\eplusout.csv')
    reportSQL= (str(studyFolder) + '\eplusout.sql')
    reportHTML2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BA_eplustbl.htm')
    reportCSV2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BA_eplusout.csv')
    reportSQL2= (str(studyFolder) + "/" + str(BaseFileName)  + '_BA_eplusout.sql')

    if os.path.exists(reportCSV2):
        os.remove(reportCSV2)
    
    if os.path.exists(reportHTML2):
        os.remove(reportHTML2)

    if os.path.exists(reportSQL2):
        os.remove(reportSQL2)

    os.rename(reportHTML,reportHTML2)
    os.rename(reportCSV,reportCSV2)
    os.rename(reportSQL,reportSQL2)

    # ===============================================================================================================
    # ADORB
    # ===============================================================================================================
    # Inputs
    laborFraction = 0.4
    emCO2_firstCost = firstCost*laborFraction*0.3

    MWH = hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)']*0.0000000002778
    hourlyEmissions = pd.read_csv(emissionsDatabase)
    emissions = hourlyEmissions[str(gridRegion)]
    
    CO2_Elec = sum(MWH*emissions)

    gasPrice = 0.64 #$/therm

    if natGasPresent == 1:
        monthlyMTR = monthlyMTR.drop(index=[0,1,2,3,4,5,6,7])
        annualGas = (((sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*gasPrice)+(40*12))
        CO2_gas = (sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*12.7
    else:
        CO2_gas = 0
        annualGas = 0

    # Future above to be better integrated

    duration = 70
    elecPrice = 0.1324 #$/kWh
    annualElec = ((hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum()*0.0000002778*elecPrice)+144)
    
    annualCO2 = CO2_Elec + CO2_gas
    dirMR = [(firstCost,1),(8500,20),(8500,40),(8500,60)]
    emCO2 = [(emCO2_firstCost,1),((8500*laborFraction*0.3),20),((8500*laborFraction*0.3),40),((8500*laborFraction*0.3),60)] 
    eTrans = peakElec

    
    final = adorb(duration, annualElec, annualGas, annualCO2, dirMR, emCO2, eTrans)

    adorbCost = final[0]
    pv_dirEn_tot = final[1]
    pv_dirMR_tot = final[2]
    pv_opCO2_tot = final[3]
    pv_emCO2_tot = final[4]
    pv_eTrans_tot = final[5]

    # ===============================================================================================================
    # Final Result Collection
    # ===============================================================================================================

    ResultsTable = ResultsTable.append({'Run Name':runList['CASE_NAME'][runCount],
                                        'SET ≤ 12.2°C Hours (F)':HeatingSET,
                                        "Hours < 2°C [hr]":Below2C,
                                        "Caution (> 26.7, ≤ 32.2°C) [hr]":Caution,
                                        "Extreme Caution (> 32.2, ≤ 39.4°C) [hr]":ExtremeCaution,
                                        "Danger (> 39.4, ≤ 51.7°C) [hr]":Danger,
                                        "Extreme Danger (> 51.7°C) [hr]":ExtremeDanger,
                                        'EUI':eui,
                                        'Peak Electric Demand [W]':peakElec,
                                        'Heating Battery Size [kWh]':heatingBattery, 
                                        'Cooling Battery Size [kWh]':coolingBattery,
                                        'First Year Electric Cost [$]':annualElec,
                                        'First Year Gas Cost [$]':annualGas,
                                        'First Cost [$]':firstCost,
                                        'Total ADORB Cost [$]':adorbCost,
                                        'pv_dirEn_tot':pv_dirEn_tot,
                                        'pv_dirMR_tot':pv_dirMR_tot,
                                        'pv_opCO2_tot':pv_opCO2_tot,
                                        'pv_emCO2_tot':pv_emCO2_tot,
                                        'pv_eTrans_tot':pv_eTrans_tot}, ignore_index=True)



# sum(pv), pv_dirEn_tot, pv_dirMR_tot, pv_opCO2_tot, pv_emCO2_tot,pv_eTrans_tot


ResultsTable.to_csv(str(studyFolder) + "/" + str(batchName) + "_ResultsTable.csv")

print('Runs Successful!')