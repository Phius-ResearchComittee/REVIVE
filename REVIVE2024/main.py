#=============================================================================================================================
# PhiusREVIVE Research Tool
# Updated 2024/03/04
# v24.2.0
#
#

# Copyright (c) 2024 Phius

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
import datetime as dt
from datetime import datetime
import email.utils as eutils
from statistics import mean
import time
import math
import csv
# import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
from joblib import Parallel, delayed
import PySimpleGUI as sg
# from PIL import Image, ImageTk
import os
import gc
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
import sys
from os import system
import pylatex

from pylatex import Document, PageStyle, Head, MiniPage, Foot, LargeText, \
    MediumText, LineBreak, simple_page_number
from pylatex.utils import bold
from pylatex import Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat
from pylatex.utils import italic

#==============================================================================================================================
# 2.0 Custom modules
#==============================================================================================================================

from envelope import *
from simControl import *
from schedules import *
from adorb import *
from internalHeatGains import *
from hvac import * # type: ignore
from renewables import *
from outputs import *
from weatherMorph import *

#==============================================================================================================================
# 3.0 GUI Interface
#==============================================================================================================================
sg.theme('LightBlue2')

tab0_layout =  [[sg.Text('Welcome')],
                [sg.Text('Please follow the steps below to test thermal resilience of the building:')],
                [sg.Text('1. Assigned EnergPlus IDD File Location')],
                [sg.Text('2. Assign a Study Folder Path. This tool will generate many files in this directory, including models and results')],
                [sg.Text('3. Assign IDF file path for geometry inputs. Please reference full guide for naming conventions')],
                [sg.Text('4. Assign run list path. Please reference full guide for naming conventions')],
                [sg.Text('5. Assign Database folder path')],
                [sg.Text('6. Assign a batch name. This will be on all files so it will be easily searchable')],
                [sg.Text('7. Check Generate PDF if you PDF summaries are needed. This feature is currently not fully tested')],
                [sg.Text('8. Check Delete Unecessary Files to clean up the study folder after runs are completed')],
                [sg.Text('9. Press LOAD. Confirm the number of cases matches the run list')],
                [sg.Text('10. Press RUN ANALYSIS to start. A popup will show progress, and a second popup will appear to confirm completition')],
                ]

tab1_layout =   [[sg.Text('Batch Name:', size =(15, 1)),sg.InputText('Name your batch of files', key='batchName')],
                [sg.Text('IDD File Location:', size =(15, 1)),sg.InputText("C:\EnergyPlusV9-5-0\Energy+.idd", key='iddFile'), sg.FileBrowse()],
                [sg.Text('Study Folder:', size =(15, 1)),sg.InputText('C:/REVIVE v24.1.0/Parametric Runs Results', key='studyFolder'), sg.FolderBrowse()],
                # [sg.Text('Geometry IDF:', size =(15, 1)),sg.InputText('C:/REVIVE v24.1.0/Databases/Sample Geometry/PNNL_SF_Geometry.idf', key='GEO'), sg.FileBrowse()],
                [sg.Text('Run List Location:', size =(15, 1)),sg.InputText("C:/REVIVE v24.1.0/Parametric Run List/PRL_2024-01-30.csv", key='runList'), sg.FileBrowse()],
                [sg.Text('Database Folder Location:', size =(15, 1)),sg.InputText('C:/REVIVE v24.1.0/Databases', key='dataBases'), sg.FolderBrowse()]
                ]

tab2_layout =   [[sg.Text('Parallel Processes:', size =(10, 1)),sg.OptionMenu([1,2,4,8,12,16,20,24,28,32], default_value='4', key='PARALLEL')],
                 [sg.Checkbox('Generate PDF?', size=(25, 1), default=False,key='genPDF')],
                 [sg.Checkbox('Generate Graphs Files?', size=(25, 1), default=False,key='GenerateGraphs')],
                 [sg.Checkbox('Delete Unecessary Files?', size=(25, 1), default=True,key='DeleteFiles')]
                ]

tab3_layout =   [[sg.Text('Year 1 ADORB Results:', size =(20, 1)),sg.InputText(key='Year1ADORB'), sg.FileBrowse()],
                 [sg.Text('Year 1 ADORB Start:', size =(20, 1)),sg.InputText(key='Year1ADORBstart')],
                 [sg.Text('Year 2 ADORB Results:', size =(20, 1)),sg.InputText(key='Year2ADORB'), sg.FileBrowse()],
                 [sg.Text('Year 2 ADORB Start:', size =(20, 1)),sg.InputText(key='Year2ADORBstart')],
                 [sg.Text('Year 3 ADORB Results:', size =(20, 1)),sg.InputText(key='Year3ADORB'), sg.FileBrowse()],
                 [sg.Text('Year 3 ADORB Start:', size =(20, 1)),sg.InputText(key='Year3ADORBstart')],
                 [sg.Button('CALC ADORB')]
                ]

layout1 = [
    # [sg.Image(r'C:\Users\amitc_crl\OneDrive\Documents\GitHub\REVIVE\REVIVE2024\al_REVIVE_PILOT_logo.png')],
            [sg.TabGroup(
            [[sg.Tab('Start', tab0_layout,),
            sg.Tab('Project Inputs', tab1_layout,),
            sg.Tab('Run Settings', tab2_layout,),
            sg.Tab('3 Phase ADORB', tab3_layout,),]])],
            [sg.Button('LOAD'), sg.Button('RUN ANALYSIS'), sg.Button('EXIT')]]  

window = sg.Window('Phius REVIVE 2024 Analysis Tool v24.2.0',layout1, default_element_size=(125, 125), grab_anywhere=True)

#==============================================================================================================================
# 3.0 Functions
#==============================================================================================================================

def divide_chunks(l, n): 
      
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n] 

#==============================================================================================================================
# 3.0 File Management
#==============================================================================================================================
DUMMY_MODE = True if "--test" in sys.argv or "-t" in sys.argv else False
while True:
    event, inputValues = window.read()
    if event == 'LOAD':
        runListPath = inputValues['runList']
        # validate input
        try:
            assert os.path.isfile(runListPath), "Run list path does not exist."
            assert runListPath[-4:]==".csv", "Run list file is not CSV."
        except AssertionError as e:
            sg.popup(e)
            continue

        runList = pd.read_csv(str(runListPath))
        totalRuns = runList.shape[0]
        sg.popup('Loaded ' + str(totalRuns) + ' Cases')
    if event == sg.WIN_CLOSED or event == 'EXIT':
        break

    if event == 'CALC ADORB':
        year1Path = inputValues['Year1ADORB']
        year1Start = int(inputValues['Year1ADORBstart'])
        year2Path = inputValues['Year2ADORB']
        year2Start = int(inputValues['Year2ADORBstart'])
        year3Path = inputValues['Year3ADORB']
        year3Start = int(inputValues['Year3ADORBstart'])

        multiphaseADORB(year1Path,year1Start,year2Path,year2Start,year3Path,year3Start)

    if event == 'RUN ANALYSIS':
        cleanFolder = inputValues['DeleteFiles']
        parallel_cores = int(inputValues['PARALLEL'])
        batchName = str(inputValues['batchName']) if not DUMMY_MODE else "dummy"

        iddfile = str(inputValues['iddFile'])
        runListPath = str(inputValues['runList']) if not DUMMY_MODE else os.path.join("dummy", "dummy_runlist.csv")
        studyFolder = str(inputValues['studyFolder']) if not DUMMY_MODE else os.path.abspath("dummy")
        databases = str(inputValues['dataBases'])
        
        emissionsDatabase = os.path.join(databases,'Hourly Emission Rates.csv')
        weatherDatabase = os.path.join(databases, 'Weather Data')
        constructionDatabase = os.path.join(databases, 'Construction Database.csv')
        
        runList = pd.read_csv(runListPath)
        totalRuns = runList.shape[0]
        batchName = batchName.replace(" ", "_")

        pdfReport = inputValues['genPDF']
        graphs = inputValues['GenerateGraphs']

        ResultsTable = pd.DataFrame(columns=["Run Name","SET ≤ 12.2°C Hours (F)","Hours < 2°C [hr]",'Total Deadly Days','Min outdoor DB [°C]','Min outdoor DP [°C]',
                                                    'Max outdoor DB [°C]','Max outdoor DP [°C]',"Caution (> 26.7, ≤ 32.2°C) [hr]","Extreme Caution (> 32.2, ≤ 39.4°C) [hr]",
                                                    "Danger (> 39.4, ≤ 51.7°C) [hr]","Extreme Danger (> 51.7°C) [hr]", 'EUI','Peak Electric Demand [W]',
                                                    'Heating Battery Size [kWh]', 'Cooling Battery Size [kWh]', 'Total ADORB Cost [$]','First Year Electric Cost [$]',
                                                    'First Year Gas Cost [$]','First Cost [$]','Wall Cost [$]','Roof Cost [$]','Floor Cost [$]','Window Cost [$]',
                                                    'Door Cost [$]','Air Sealing Cost [$]','Mechanical Cost [$]','Water Heater Cost [$]','Appliances Cost [$]','PV Cost [$]',
                                                    'Battery Cost [$]','pv_dirEn_tot','pv_dirMR_tot','pv_opCO2_tot','pv_emCO2_tot','pv_eTrans_tot'])

        # validate input data
        with open('required_columns.csv') as f:
            reader = csv.reader(f)
            required_columns = list(reader)[0]

        try:
            assert os.path.isfile(iddfile), "Energy+ IDD path does not exist."
            assert os.path.isfile(runListPath), "Run list path does not exist."
            assert os.path.isdir(studyFolder), "Study folder path does not exist."
            assert os.path.isdir(databases), "Database path does not exist."
            assert os.path.isfile(emissionsDatabase), 'Database folder is missing "Hourly Emission Rates.csv".'
            assert os.path.isdir(weatherDatabase), 'Database folder is missing "Weather Data" directory.'
            assert os.path.isfile(constructionDatabase), 'Database folder is missing "Construction Database.csv".'

            for col in required_columns:
                assert col in runList, f'{col} column missing, run list may be out of date.'
        
        except AssertionError as e:
            sg.popup(e)
            continue

        # for case in range(totalRuns):
        def simulation(case, ResultsTable):
            os.chdir(str(studyFolder))
            IDF.setiddname(iddfile)

            runCount = case
            idfgName = str(runList['GEOMETRY_IDF'][runCount])
            BaseFileName = str(batchName + '_' + runList['CASE_NAME'][runCount])
            caseName = runList['CASE_NAME'][runCount]

            sg.one_line_progress_meter('Progress Meter', runCount, totalRuns, 'Analysis Running','Current Case: ' + str(caseName))

            print('Running: ' + str(BaseFileName))

            # testingFile = str(studyFolder) + "/" + str(BaseFileName) + ".idf"
            testingFile_BA = os.path.join(studyFolder, BaseFileName + "_BA.idf")
            testingFile_BR = os.path.join(studyFolder, BaseFileName + "_BR.idf")
            passIDF = os.path.join(studyFolder, BaseFileName + "_PASS.idf")

            #==============================================================================================================================
            # 4.0 Variable Assignment
            #==============================================================================================================================

            try:
                epwFile = os.path.join(weatherDatabase, str(runList['EPW'][runCount]))
                ddyName =  os.path.join(weatherDatabase, str(runList['DDY'][runCount]))
                
                # validate spreadsheet input
                assert os.path.isfile(epwFile), "Cannot find specified EPW file."
                assert os.path.isfile(ddyName), "Cannot find specified DDY file."
                
            except AssertionError as ae:
                # handling still needs some work
                sg.popup(e)
                return

            try:

                
                ZoneName = 'Zone 1'

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
                constructionList = pd.read_csv(constructionDatabase, index_col="Name")
                appliance_list = list(runList['APPLIANCE_LIST'][runCount].split(', '))
                
                total_appliance_cost = fridge = dishWasher = clothesWasher = clothesDryer = lights_cost = 0
                ihg_dict = {}
                for Nbr in range(9):
                    for appliance_name, row in constructionList.filter(items=appliance_list, axis=0).iterrows():
                        rating = float(row["Appliance_Rating"]) # must be float for fractional efficiency
                        cost = int(row["Mechanical Cost"])
                        if 'FRIDGE' in appliance_name:
                            fridge += (rating/(8760))*1000 # always on design load

                        elif 'DISHWASHER' in appliance_name:
                            dishWasher += (((86.3 + (47.73 / (215 / rating)))/215) * ((88.4 + 34.9*Nbr)*(12/12))*(1/365)*1000)

                        elif 'CLOTHESWASHER' in appliance_name:
                            clothesWasher += (rating/365)*1000

                        elif 'CLOTHESDRYER' in appliance_name:
                            clothesDryer += ((12.4*(164+46.5*Nbr)*1.18/3.01*(2.874/0.817-704/rating)/(0.2184*(4.5*4.08+0.24)))/365)*1000

                        elif 'LIGHTS' in appliance_name:
                            fracHighEff = rating
                            lights_cost += cost
                    
                        total_appliance_cost += cost
                    ihg_dict[Nbr] = {'fridge':fridge, 'dishwasher':dishWasher, 'clotheswasher':clothesWasher,
                                     'clothesdryer':clothesDryer, 'lighting efficacy':fracHighEff, 'applianceCost':total_appliance_cost}
                    
                
                # REMOVE LATER
                constructionList = constructionList.reset_index()
                PV_SIZE = runList['PV_SIZE_[W]'][runCount]
                PV_TILT = runList['PV_TILT'][runCount]
                
                # Envelope

                flowCoefficient = runList['FLOW_COEFFICIENT [SI]'][runCount]
                Ext_Window1 = runList['EXT_WINDOW_1'][runCount]
                Ext_Window2 = runList['EXT_WINDOW_2'][runCount]
                Ext_Window3 = runList['EXT_WINDOW_3'][runCount]

                Ext_Wall1 = runList['EXT_WALL_1_NAME'][runCount]
                Ext_Roof1 = runList['EXT_ROOF_1_NAME'][runCount]
                Ext_Floor1 = runList['EXT_FLOOR_1_NAME'][runCount]
                Ext_Door1 = runList['EXT_DOOR_1_NAME'][runCount]
                Int_Floor1 = runList['INT_FLOOR_1_NAME'][runCount]

                Ext_Wall2 = runList['EXT_WALL_2_NAME'][runCount]
                Ext_Roof2 = runList['EXT_ROOF_2_NAME'][runCount]
                Ext_Floor2 = runList['EXT_FLOOR_2_NAME'][runCount]
                Ext_Door2 = runList['EXT_DOOR_2_NAME'][runCount]
                Int_Floor2 = runList['INT_FLOOR_2_NAME'][runCount]

                Ext_Wall3 = runList['EXT_WALL_3_NAME'][runCount]
                Ext_Roof3 = runList['EXT_ROOF_3_NAME'][runCount]
                Ext_Floor3 = runList['EXT_FLOOR_3_NAME'][runCount]
                Ext_Door3 = runList['EXT_DOOR_3_NAME'][runCount]
                Int_Floor3 = runList['INT_FLOOR_3_NAME'][runCount]

                # Foundation interfaces
                fnd1 = runList['FOUNDATION_INTERFACE_1'][runCount]
                fnd1i = runList['FOUNDATION_INSUINSULATION_1'][runCount]
                fnd1p = runList['FOUNDATION_PERIMETER_1'][runCount]
                fnd1d = runList['FOUNDATION_INSULATION_DEPTH_1'][runCount]

                fnd2 = runList['FOUNDATION_INTERFACE_2'][runCount]
                fnd2i = runList['FOUNDATION_INSUINSULATION_2'][runCount]
                fnd2p = runList['FOUNDATION_PERIMETER_2'][runCount]
                fnd2d = runList['FOUNDATION_INSULATION_DEPTH_2'][runCount]

                fnd3 = runList['FOUNDATION_INTERFACE_3'][runCount]
                fnd3i = runList['FOUNDATION_INSUINSULATION_3'][runCount]
                fnd3p = runList['FOUNDATION_PERIMETER_3'][runCount]
                fnd3d = runList['FOUNDATION_INSULATION_DEPTH_3'][runCount]


                if str(fnd1) != 'nan':
                    foundationList = [(fnd1,fnd1i,fnd1d,fnd1p)]

                if str(fnd2) != 'nan':
                    foundationList = [(fnd1,fnd1i,fnd1d,fnd1p),
                                      (fnd2,fnd2i,fnd2d,fnd2p)]
                
                if str(fnd3) != 'nan':
                    foundationList = [(fnd1,fnd1i,fnd1d,fnd1p),
                                      (fnd2,fnd2i,fnd2d,fnd2p),
                                      (fnd3,fnd3i,fnd3d,fnd3p)]

                # Schedule Based Inputs 
                outage1start = runList['OUTAGE_1_START'][runCount]
                outage1end = runList['OUTAGE_1_END'][runCount]
                outage2start = runList['OUTAGE_2_START'][runCount]
                outage2end = runList['OUTAGE_2_END'][runCount]
                outage1type = runList['1ST_OUTAGE'][runCount]

                # Weather Morph inputs
                MorphFactorDB1 = runList['MorphFactorDB1'][runCount]
                MorphFactorDP1 = runList['MorphFactorDP1'][runCount]
                MorphFactorDB2 = runList['MorphFactorDB2'][runCount]
                MorphFactorDP2 = runList['MorphFactorDP2'][runCount]

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
                idfg = IDF(os.path.join(studyFolder, idfgName))
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

                
                # High level model information
                Version(idf1)
                SimulationControl(idf1)
                Building(idf1,BaseFileName)
                CO2Balance(idf1)
                Timestep(idf1)
                RunPeriod(idf1)
                GeometryRules(idf1)

                modeled_zones = idf1.idfobjects['ZONE']
                DHW_CombinedGPM = 0

                for zone in modeled_zones:
                    zone_name = zone.Name.split('|')
                    zone_type = zone_name[1] if len(zone_name)>1 else ""
                    if 'UNIT' in zone_type:
                        occ = 1 + float(zone_name[2][0])
                        icfa_zone = zone.Floor_Area
                        Nbr_zone = float(zone_name[2][0])
                        fracHighEff = ihg_dict[float(zone_name[2][0])]['lighting efficacy']
                        PhiusLights = (0.2 + 0.8*(4 - 3*fracHighEff)/3.7)*(455 + 0.8*icfa_zone*10.76391) * 0.8 * 1000 * (1/365) #power per day W use Phius calc
                        PhiusMELs = ((413 + 69*Nbr_zone + 0.91*icfa_zone*10.76391)/365)*1000*0.8 #consumption per day per phius calc
                        rangeElec = ((331 + 39*Nbr_zone)/365)*1000
                        
                        # DHW Calc per BA
                        DHW_ClothesWasher = 2.3 + 0.78*Nbr_zone
                        DHW_Dishwasher = 2.26 + 0.75*Nbr_zone
                        DHW_Shower = 0.83*(14 + 1.17*Nbr_zone)
                        DHW_Bath = 0.83*(3.5+1.17*Nbr_zone)
                        DHW_Sinks = 0.83*(12.5+4.16*Nbr_zone)
                        DHW_CombinedGPM = (DHW_ClothesWasher + DHW_Dishwasher + DHW_Shower + DHW_Bath + DHW_Sinks)*4.381E-8

                        # Sizing loads from ASHRAE 1199-RP

                        G_0s = 136  #in W
                        G_0l = 20  #in W
                        G_cfs = 2.2  #in W
                        G_cfl = 0.22  #in W
                        G_ocs = 22  #in W
                        G_ocl = 12  #in W

                        sizingLoadSensible = G_0s + G_cfs*icfa_zone + G_ocs*occ
                        sizingLoadLatent = G_0l + G_cfl*icfa_zone + G_ocl*occ
                        People(idf1, zone_name, occ)
                        LightsMELsAppliances(idf1, zone_name, PhiusLights, PhiusMELs, fridge, rangeElec, 
                                    clothesDryer,clothesWasher,dishWasher)
                        SizingLoads(idf1, zone_name, sizingLoadSensible, sizingLoadLatent)
                        ThermalMass(idf1, zone_name, icfa_zone)

                    if 'STAIR' in zone_type:
                        print(str(zone_name[0]) + ' is some Stairs')
                    if 'CORRIDOR' in zone_type:
                        print(str(zone_name[0]) + ' is some a Corridor')
                
                # Materials and constructions
                materials = pd.read_csv(os.path.join(databases, 'Material Database.csv'))
                materialList = materials.shape[0]

                for item in range(materialList):
                    materialBuilder(idf1, materials['NAME'][item], materials['ROUGHNESS'][item], 
                                    materials['THICKNESS [m]'][item], materials['CONDUCTIVITY [W/mK]'][item],
                                    materials['DENSITY [kg/m3]'][item], materials['SPECIFIC HEAT CAPACITY [J/kgK]'][item])
                    
                glazingSpecs = pd.read_csv(os.path.join(databases, 'Window Database.csv'))

                glazings = glazingSpecs.shape[0]

                for item in range(glazings):
                    glazingBuilder(idf1, glazingSpecs['NAME'][item], glazingSpecs['U-FACTOR [W/m2K]'][item],glazingSpecs['SHGC'][item])

                # Constructions 

                constructions = constructionList.shape[0]

                for item in range(constructions):
                    if str(constructionList['Outside_Layer'][item]) != 'nan':
                        layers = [constructionList['Outside_Layer'][item],
                        constructionList['Layer_2'][item],
                        constructionList['Layer_3'][item],
                        constructionList['Layer_4'][item],
                        constructionList['Layer_5'][item],
                        constructionList['Layer_6'][item],
                        constructionList['Layer_7'][item],
                        constructionList['Layer_8'][item],
                        constructionList['Layer_9'][item],
                        constructionList['Layer_10'][item]]

                        layerList = [x for x in layers if str(x) != 'nan']

                    constructionBuilder(idf1, constructionList['Name'][item],layerList)

                # Envelope inputs
                Infiltration(idf1, flowCoefficient)
                SpecialMaterials(idf1)
                FoundationInterface(idf1,foundationList)

                ShadeMaterials(idf1)

                # Window inputs and shading controls
                WindowVentilation(idf1, halfHeight, operableArea_N, operableArea_W, 
                        operableArea_S, operableArea_E)
                

                windowNames_split = list(divide_chunks(windowNames, 10))

                for i in range(len(windowNames_split)):
                    windowNamesChunk = windowNames_split[i]
                    WindowShadingControl(idf1, windowNamesChunk)

                WindowShadingControl(idf1, windowNames)

                AssignContructions(idf1, Ext_Wall1,Ext_Wall2,Ext_Wall3,
                       Ext_Roof1,Ext_Roof2,Ext_Roof3,
                       Ext_Floor1,Ext_Floor2,Ext_Floor3,
                       Ext_Door1,Ext_Door2,Ext_Door3, 
                       Int_Floor1,Int_Floor2,Int_Floor3,
                       Ext_Window1,Ext_Window2,Ext_Window3)

                # Sizing settings:
                SizingSettings(idf1, ZoneName)
                HVACControls(idf1, ZoneName)
                ZoneMechConnections(idf1, ZoneName)
                HVACBuilder(idf1, ZoneName, mechSystemType)
                WaterHeater(idf1, ZoneName, dhwFuel, DHW_CombinedGPM)
                Curves(idf1)

                Renewables(idf1, ZoneName, PV_SIZE, PV_TILT)

                SimulationOutputs(idf1)
                # ============================================================================
                # Pass IDF 
                # ============================================================================
                
                idf1.saveas(str(passIDF))

                # ============================================================================
                # Resilience Specific
                # ============================================================================

                idf1 = IDF(str(passIDF))

                zeroSch(idf1, 'BARangeSchedule')
                zeroSch(idf1, 'Phius_Lighting')
                zeroSch(idf1, 'Phius_MELs')
                zeroSch(idf1, 'CombinedDHWSchedule')
                zeroSch(idf1, 'BAClothesDryerSchedule')
                zeroSch(idf1, 'BAClothesWasherSchedule')
                zeroSch(idf1, 'BADishwasherSchedule')
                ResilienceSchedules(idf1, outage1start, outage1end, outage2start, outage2end, 
                            coolingOutageStart,coolingOutageEnd,NatVentAvail,
                            demandCoolingAvail,shadingAvail,outage1type)
                
                ResilienceControls(idf1, NatVentType)

                ResilienceERV(idf1, occ, ervSense, ervLatent)

                WeatherMorphSine(idf1, outage1start, outage1end, outage2start, outage2end,
                        MorphFactorDB1, MorphFactorDP1, MorphFactorDB2, MorphFactorDP2)


                # ==================================================================================================================================
                # Run Resilience Simulation and Collect Results
                # ==================================================================================================================================

                # add the index in from the for loop for the number of runs to make this table happen faster

                # run the simulation or generate dummy files for speed
                if not DUMMY_MODE:
                    idf1.saveas(str(testingFile_BR))
                    idf = IDF(str(testingFile_BR), str(epwFile))
                    idf.run(readvars=True,output_prefix=str(str(BaseFileName) + "_BR"))

                fname = os.path.join(studyFolder, BaseFileName + '_BRtbl.htm')

                site_source_energy_table = fasthtml.tablebyname(open(fname, 'r'), "Site and Source Energy")
                eui = float(site_source_energy_table[1][1][2])

                time_bin_table = fasthtml.tablebyname(open(fname, 'r'), "Time Bin Results")
                Below2C = float(time_bin_table[1][39][2])

                heating_set_hours_table = fasthtml.tablebyname(open(fname, 'r'), "Heating SET Hours")
                HeatingSET = float(heating_set_hours_table[1][1][1])

                heating_index_hours_table = fasthtml.tablebyname(open(fname, 'r'), "Heat Index Hours")
                Caution = float(heating_index_hours_table[1][1][2])
                ExtremeCaution = float(heating_index_hours_table[1][1][3])
                Danger = float(heating_index_hours_table[1][1][4])
                ExtremeDanger = float(heating_index_hours_table[1][1][5])

                # Resilience Graphs
                        
                filehandle = os.path.join(studyFolder, BaseFileName + '_BRout.csv')
                hourly = pd.read_csv(filehandle)
                hourlyBA = pd.read_csv(filehandle)

                hourly.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
                hourly[['Date2','Time']] = hourly.DateTime.str.split(expand=True)
                hourly['Date'] = hourly['Date2'].map(str) + '/' + str(2020)
                hourly['Time'] = (pd.to_numeric(hourly['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourly['Time'].str[2:]
                hourly['DateTime'] = hourly['Date'] + ' ' + hourly['Time']
                hourly['DateTime'] = pd.to_datetime(hourly['DateTime'], format="%m/%d/%Y %H:%M:%S", exact=True)

                endWarmup = hourly[hourly['DateTime'] == '2020-01-01 00:00:00'].index[0]
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

                MinDBOut = min(hourlyHeat['Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'].tolist())
                MinDPOut = min(hourlyHeat['Environment:Site Outdoor Air Dewpoint Temperature [C](Hourly)'].tolist())
                MaxDBOut = max(hourlyCool['Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'].tolist())
                MaxDPOut = max(hourlyCool['Environment:Site Outdoor Air Dewpoint Temperature [C](Hourly)'].tolist())

                x = hourlyHeat['DateTime']
                if graphs == True:
                    fig = plt.figure(layout='constrained', figsize=(10, 10))
                    fig.suptitle((str(caseName) + '_Heating Outage Resilience'), fontsize='x-large')
                    ax = fig.subplot_mosaic([['temperature'],['rh'],['SET']])
                    ax['temperature'].plot(x,hourlyHeat["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"], label="Site Dry Bulb [C]", linestyle='dashed')
                    ax['temperature'].plot(x,hourlyHeat["ZONE 1:Zone Air Temperature [C](Hourly)"], label="Zone Dry Bulb [C]",color='black',linewidth=2)
                    ax['temperature'].set_ylim(((min(min(hourlyHeat["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]), min(hourlyHeat["ZONE 1:Zone Air Temperature [C](Hourly)"])))-5),((max(max(hourlyHeat["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]), max(hourlyHeat["ZONE 1:Zone Air Temperature [C](Hourly)"])))+5))
                    ax['temperature'].set_ylabel('Temperature [C]')
                    ax['temperature'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['temperature'].grid(True)

                    ax['rh'].plot(x,hourlyHeat['ZONE 1:Zone Air Relative Humidity [%](Hourly)'], label=("Zone RH"),color='black',linewidth=2)
                    ax['rh'].set_ylabel('Relative Humidity [%]')
                    ax['rh'].set_ylim(0,100)
                    ax['rh'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['rh'].grid(True)

                    ax['SET'].plot(x,hourlyHeat['ZONE OCCUPANTS:Zone Thermal Comfort Pierce Model Standard Effective Temperature [C](Hourly)'], label=("Zone SET"),color='black',linewidth=2)
                    ax['SET'].grid(True)
                    ax['SET'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['SET'].set_ylim((min(hourlyHeat['ZONE OCCUPANTS:Zone Thermal Comfort Pierce Model Standard Effective Temperature [C](Hourly)'])-5),(max(hourlyHeat['ZONE OCCUPANTS:Zone Thermal Comfort Pierce Model Standard Effective Temperature [C](Hourly)'])+5))
                    ax['SET'].set_xlabel('Date')
                    ax['SET'].set_ylabel('Standard Effective Temperature [°C]')
                    ax['SET'].axhline(12.2, color='crimson', linestyle='dashed')

                    heatingGraphFile = os.path.join(studyFolder, BaseFileName + "_Heating Outage Resilience Graphs.png")

                    plt.savefig(str(heatingGraphFile), dpi=300)
                    plt.clf()

                x = hourlyCool['DateTime']
                if graphs == True:
                    fig = plt.figure(layout='constrained', figsize=(10, 10))
                    fig.suptitle((str(caseName) + '_Cooling Outage Resilience'), fontsize='x-large')
                    ax = fig.subplot_mosaic([['temperature'],['rh'],['HI']])
                    ax['temperature'].plot(x,hourlyCool["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"], label="Site Dry Bulb [C]", linestyle='dashed')
                    ax['temperature'].plot(x,hourlyCool["ZONE 1:Zone Air Temperature [C](Hourly)"], label="Zone Dry Bulb [C]",color='black',linewidth=2)
                    ax['temperature'].set_ylim(((min(min(hourlyCool["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]), min(hourlyCool["ZONE 1:Zone Air Temperature [C](Hourly)"])))-5),((max(max(hourlyCool["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]), max(hourlyCool["ZONE 1:Zone Air Temperature [C](Hourly)"])))+5))
                    ax['temperature'].set_ylabel('Temperature [C]')
                    ax['temperature'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['temperature'].grid(True)

                    ax['rh'].plot(x,hourlyCool['ZONE 1:Zone Air Relative Humidity [%](Hourly)'], label=("Zone RH"),color='black',linewidth=2)
                    ax['rh'].set_ylabel('Relative Humidity [%]')
                    ax['rh'].set_ylim(0,100)
                    ax['rh'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['rh'].grid(True)

                    ax['HI'].plot(x,hourlyCool['ZONE 1:Zone Heat Index [C](Hourly)'], label=("Zone HI"),color='black',linewidth=2)
                    ax['HI'].grid(True)
                    ax['HI'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
                    ax['HI'].set_ylim((min(hourlyCool['ZONE 1:Zone Heat Index [C](Hourly)'])-5),(max(hourlyCool['ZONE 1:Zone Heat Index [C](Hourly)'])+5))
                    ax['HI'].set_xlabel('Date')
                    ax['HI'].set_ylabel('Heat Index [°C]')
                    ax['HI'].axhline(26.7, color='seagreen', linestyle='dashed')
                    ax['HI'].axhline(32.2, color='orange', linestyle='dashed')
                    ax['HI'].axhline(39.4, color='crimson', linestyle='dashed')
                    ax['HI'].axhline(51.7, color='darkmagenta', linestyle='dashed')

                    coolingGraphFile = os.path.join(studyFolder, BaseFileName + "_Cooling Outage Resilience Graphs.png")

                    plt.savefig(str(coolingGraphFile), dpi=300)
                    plt.clf()
                    del fig
                gc.collect()

                # Mora days

                RH = hourlyCool['ZONE 1:Zone Air Relative Humidity [%](Hourly)'].tolist()
                Temp = hourlyCool['ZONE 1:Zone Air Temperature [C](Hourly)'].tolist()

                RHdays = [RH[x:x+24] for x in range(0, len(RH), 24)]
                TEMPdays = [Temp[x:x+24] for x in range(0, len(Temp), 24)]

                avgRH = []
                avgTemp = []
                moraDays = []
                moraPF = []
                moraTotalDays = 0
                for day in range(7):
                    avgRH.append(mean(RHdays[day]))
                    avgTemp.append(mean(TEMPdays[day]))
                    moraDays.append((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2))
                    moraPF.append(mean(TEMPdays[day])-((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2)))
                    if (mean(TEMPdays[day])-((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2))) > 0:
                        moraTotalDays = moraTotalDays+1

                # Battery Sizing
                heatingBattery = (hourlyHeat['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778
                coolingBattery = (hourlyCool['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778

                # hourlyHeat.to_csv(str(studyFolder) + "/" + str(BaseFileName) + "_hourlyHeat.csv")
                # hourlyCool.to_csv(str(studyFolder) + "/" + str(BaseFileName) + "_hourlyCool.csv")

                # Save HTML and CSV outputs
                reportHTML = os.path.join(studyFolder, 'eplustbl.htm')
                reportCSV = os.path.join(studyFolder, 'eplusout.csv')
                reportSQL= os.path.join(studyFolder, 'eplusout.sql')
                reportHTML2 = os.path.join(studyFolder, BaseFileName + '_BR_eplustbl.htm')
                reportCSV2 = os.path.join(studyFolder, BaseFileName + '_BR_eplusout.csv')
                reportSQL2= os.path.join(studyFolder, BaseFileName + '_BR_eplusout.sql')


                # if os.path.exists(reportCSV2):
                #     os.remove(reportCSV2)
                
                # if os.path.exists(reportHTML2):
                #     os.remove(reportHTML2)

                # if os.path.exists(reportSQL2):
                #     os.remove(reportSQL2)

                # os.rename(reportHTML,reportHTML2)
                # os.rename(reportCSV,reportCSV2)
                # os.rename(reportSQL,reportSQL2)

                # ============================================================================
                # Annual Specific
                # ============================================================================

                idf2 = IDF(str(passIDF))

                AnnualSchedules(idf2, outage1start, outage1end, outage2start, outage2end, 
                            coolingOutageStart,coolingOutageEnd,NatVentAvail,
                            demandCoolingAvail,shadingAvail)

                AnnualERV(idf2, occ, ervSense, ervLatent)

                for item in range(constructions):
                    
                    name = constructionList['Name'][item]
                    outerLayer = constructionList['Outside_Layer'][item]
                    cost = constructionList['Cost_Per_Area_[$/m2]'][item]
                    costSealing = constructionList['Air_Sealing_Cost_[$/ft2 ICFA]'][item]
                    costBatt = constructionList['Battery_Cost_[$/kWh]'][item]
                    costPV = constructionList['PV_Cost_[$/W]'][item]
                    costMech = constructionList['Mechanical Cost'][item]

                    if cost > 0 and str(outerLayer) != 'nan':
                        costBuilder(idf2, name, '','Construction', name,'','',cost,'')
                    
                    if costSealing > 0 and str(name) == str(flowCoefficient):
                        costBuilder(idf2,('AIR SEALING = ' + str(name)),'','General',0,0,(costSealing*icfa),'',1)

                    if costMech> 0 and str(name) == str(mechSystemType):
                        costBuilder(idf2, ('MECH_' + str(name)),'','General',0,0,costMech,'',1)

                    if costMech> 0 and str(dhwFuel) in str(name):
                        costBuilder(idf2, (str(name)),'','General',0,0,costMech,'',1)
                    
                    if costBatt > 0 and str(outerLayer) == 'nan':
                        costBuilder(idf2, name,'' ,'General',0,0,(costBatt*max(heatingBattery,coolingBattery)),'',1)

                    if costPV > 0 and str(outerLayer) == 'nan':
                        costBuilder(idf2, name,'' ,'General',0,0,(costPV*PV_SIZE),'',1)


                costBuilder(idf2, ('APPLIANCES'),'','General',0,0,total_appliance_cost,'',1)
                costBuilder(idf2, ('LIGHTS'),'','General',0,0,lights_cost,'',1)


                    
                # Annual Result Collection

                if not DUMMY_MODE:
                    idf2.saveas(str(testingFile_BA))
                    idf = IDF(str(testingFile_BA), str(epwFile))
                    idf.run(readvars=True,output_prefix=str((str(BaseFileName) + '_BA')))


                filehandle = os.path.join(studyFolder, BaseFileName + '_BAout.csv')
                filehandleMTR = os.path.join(studyFolder, BaseFileName + '_BAmtr.csv')
                hourly = pd.read_csv(filehandle)
                monthlyMTR= pd.read_csv(filehandleMTR)

                hourly.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
                hourly[['Date2','Time']] = hourly.DateTime.str.split(expand=True)
                hourly['Date'] = hourly['Date2'].map(str) + '/' + str(2020)
                hourly['Time'] = (pd.to_numeric(hourly['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourly['Time'].str[2:]
                hourly['DateTime'] = hourly['Date'] + ' ' + hourly['Time']
                hourly['DateTime'] = pd.to_datetime(hourly['DateTime'], format="%m/%d/%Y %H:%M:%S", exact=True)

                endWarmup = hourly[hourly['DateTime'] == '2020-01-01 00:00:00'].index[0]
                dropWarmup = [*range(0, endWarmup,1)]

                hourly = hourly.drop(index = dropWarmup)
                hourly = hourly.reset_index()

                fname = os.path.join(studyFolder, BaseFileName + '_BAtbl.htm')
                
                site_source_energy_table = fasthtml.tablebyname(open(fname, 'r'), "Site and Source Energy")
                eui = float(site_source_energy_table[1][1][2])

                annual_peak_values_table = fasthtml.tablebyname(open(fname, 'r'), "Annual and Peak Values - Electricity")
                peakElec = float(annual_peak_values_table[1][1][4])

                if 'BASE' in str(BaseFileName):
                    firstCost = [0,0]
                    wallCost = 0
                    roofCost = 0
                    floorCost = 0
                    windowCost = 0
                    doorCost = 0
                    airSealing = 0
                    mechCost = 0
                    dhwCost = 0
                    applianceCost = 0
                    lightsCost = 0
                    pvCost = 0
                    batteryCost = 0
                else:
                    wallCostList = []
                    roofCostList = []
                    floorCostList = []
                    windowCostList = []
                    doorCostList = []
                    airSealingCostList = []
                    mechCostList = []
                    dhwCostList = []
                    applianceCostList = []
                    lightsCost = []

                    construction_cost_est_table = fasthtml.tablebyname(open(fname, 'r'), "Construction Cost Estimate Summary")
                    firstCost = [float(construction_cost_est_table[1][9][2]),0]

                    cost_line_item_detail_table = fasthtml.tablebyname(open(fname, 'r'), "Cost Line Item Details")
                    rows = len(cost_line_item_detail_table[1])
                    for row in range(rows):
                        item_name = cost_line_item_detail_table[1][row][2]
                        item_cost = cost_line_item_detail_table[1][row][6]
                        if 'WALL' in item_name:
                            wallCostList.append(item_cost)
                        elif 'ROOF' in item_name:
                            roofCostList.append(item_cost)
                        elif 'FLOOR' in item_name:
                            floorCostList.append(item_cost)
                        elif 'WINDOW' in item_name:
                            windowCostList.append(item_cost)
                        elif 'DOOR' in item_name:
                            doorCostList.append(item_cost)
                        elif 'AIR SEALING' in item_name:
                            airSealingCostList.append(item_cost)
                        elif 'MECH' in item_name:
                            mechCostList.append(item_cost)
                        elif 'DHW' in item_name:
                            dhwCostList.append(item_cost)
                        elif 'APPLIANCES' in item_name:
                            applianceCostList.append(item_cost)
                        elif 'LIGHTS' in item_name:
                            applianceCostList.append(item_cost)
                        elif 'PV COST' in item_name:
                            pvCost = (item_cost)
                        elif 'BATTERY COST' in item_name:
                            batteryCost = (item_cost)

                    wallCost = (sum(wallCostList))
                    roofCost = (sum(roofCostList))
                    floorCost = (sum(floorCostList))
                    windowCost = (sum(windowCostList))
                    doorCost = (sum(doorCostList))
                    airSealing = (sum(airSealingCostList))
                    mechCost = (sum(mechCostList))
                    dhwCost = (sum(dhwCostList))
                    applianceCost = (sum(applianceCostList))
                    pvCost = pvCost
                    batteryCost = batteryCost

                # Save HTML and CSV outputs
                reportHTML = os.path.join(studyFolder, 'eplustbl.htm')
                reportCSV = os.path.join(studyFolder, 'eplusout.csv')
                reportSQL= os.path.join(studyFolder, 'eplusout.sql')
                reportHTML2 = os.path.join(studyFolder, BaseFileName + '_BA_eplustbl.htm')
                reportCSV2 = os.path.join(studyFolder, BaseFileName + '_BA_eplusout.csv')
                reportSQL2= os.path.join(studyFolder, BaseFileName + '_BA_eplusout.sql')

                # if os.path.exists(reportCSV2):
                #     os.remove(reportCSV2)
                
                # if os.path.exists(reportHTML2):
                #     os.remove(reportHTML2)

                # if os.path.exists(reportSQL2):
                #     os.remove(reportSQL2)

                # os.rename(reportHTML,reportHTML2)
                # os.rename(reportCSV,reportCSV2)
                # os.rename(reportSQL,reportSQL2)

    ##################ADORB 436253 RED QUEEN PIN

                hourlyBA.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
                hourlyBA[['Date2','Time']] = hourlyBA.DateTime.str.split(expand=True)
                hourlyBA['Date'] = hourlyBA['Date2'].map(str) + '/' + str(2020)
                hourlyBA['Time'] = (pd.to_numeric(hourlyBA['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourlyBA['Time'].str[2:]
                hourlyBA['DateTime'] = hourlyBA['Date'] + ' ' + hourlyBA['Time']
                hourlyBA['DateTime'] = pd.to_datetime(hourlyBA['DateTime'], format="%m/%d/%Y %H:%M:%S", exact=True)

                endWarmup = hourlyBA[hourlyBA['DateTime'] == '2020-01-01 00:00:00'].index[0]
                dropWarmup = [*range(0, endWarmup,1)]

                hourlyBA = hourlyBA.drop(index = dropWarmup)
                hourlyBA = hourlyBA.reset_index()

                MWH = hourlyBA['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)']*0.0000000002778

                CO2_Elec_List = []
                count = 0
                for filename in os.listdir(os.path.join(databases, 'CambiumFactors')):
                    if filename.endswith('.csv'):
                        hourlyBAEmissions = pd.read_csv(os.path.join(databases, 'CambiumFactors', filename))
                        emissions = hourlyBAEmissions[str(gridRegion)]
                        CO2_Elec = sum(MWH*emissions)
                        count = count + 1
                        CO2_Elec_List.append((CO2_Elec))

                annualCO2Elec = CO2_Elec_List


                # CO2_Elec = sum(MWH*emissions)

                gasPrice = runList['GAS_PRICE_[$/THERM]'][runCount]

                if natGasPresent == 1:
                    monthlyMTR = monthlyMTR.drop(index=[0,1,2,3,4,5,6,7])
                    annualGas = (((sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*gasPrice)+(40*12))
                    annualCO2Gas = (sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*12.7
                else:
                    CO2_gas = 0
                    annualCO2Gas = 0
                    annualGas = 0


                # Future above to be better integrated

                duration = int(runList['ANALYSIS_DURATION'][runCount])
                elecPrice = float(runList['ELEC_PRICE_[$/kWh]'][runCount])
                elec_sellback_price = float(runList['SELLBACK_PRICE_[$/kWh]'][runCount])
                annualElec = ((hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum()*0.0000002778*elecPrice)-
                              (hourly['Whole Building:Facility Total Surplus Electricity Energy [J](Hourly)'].sum()*0.0000002778*elec_sellback_price)
                               +100)
                
                

                # annualCO2 = CO2_Elec + CO2_gas

                carbonDatabase = pd.read_csv(os.path.join(databases, 'Carbon Correction Database.csv'))
                countryEmissionsDatabase = pd.read_csv(os.path.join(databases, 'Country Emission Database.csv'))

                if str(runList['CARBON_MEASURES'][runCount]) != 'nan':
                    carbonMeasures = carbondMeasures = list(runList['CARBON_MEASURES'][runCount].split(', '))

                carbonMeasureCost = []

                for measure in range(carbonDatabase.shape[0]):
                    if carbonDatabase['Name'][measure] in carbonMeasures:
                        carbonMeasureCost.append([carbonDatabase['Cost'][measure], carbonDatabase['Year'][measure]])

                carbonMeasureCost.append(firstCost)

                emCO2 = []

                for measure in range(carbonDatabase.shape[0]):
                    if carbonDatabase['Name'][measure] in carbonMeasures:
                        for country in range(countryEmissionsDatabase.shape[0]):
                            if str(countryEmissionsDatabase['COUNTRY'][country]) == str(carbonDatabase['Country'][1]):
                                ef = countryEmissionsDatabase['EF [kg/$]'][country]
                            if str(countryEmissionsDatabase['COUNTRY'][country]) == 'USA':
                                efUSA = countryEmissionsDatabase['EF [kg/$]'][country]
                        emCO2.append([(carbonDatabase['Cost'][measure]*ef*(1-carbonDatabase['Labor Fraction'][measure])) + 
                                      ((carbonDatabase['Cost'][measure]*efUSA*(carbonDatabase['Labor Fraction'][measure]))), carbonDatabase['Year'][measure]])
                        # Labor fraction should be subtracted out and have USA EF applied

                for country in range(countryEmissionsDatabase.shape[0]):
                            if str(countryEmissionsDatabase['COUNTRY'][country]) == str(runList['ENVELOPE_COUNTRY'][runCount]):
                                efENV = countryEmissionsDatabase['EF [kg/$]'][country]
                                emCO2first = ((firstCost[0] * (1-runList['ENVELOPE_LABOR_FRACTION'][runCount]) * efENV) + 
                                    (firstCost[0] * (runList['ENVELOPE_LABOR_FRACTION'][runCount]) * efUSA))

                                emCO2firstCost = [emCO2first,0]

                emCO2.append(emCO2firstCost)

                # print(carbonMeasureCost)

                dirMR = carbonMeasureCost


                # EMBODIED CARBON CALCULATION
                
                # get emissions data ready
                constructionList['Name'] = constructionList['Name'].apply(lambda x: x.lower())
                constructionList = constructionList.set_index("Name")
                countryEmissionsDatabase = countryEmissionsDatabase.set_index("COUNTRY")
                country = runList['ENVELOPE_COUNTRY'][runCount]
                price_of_carbon = 0.25 # units: $/kg according to spec
                # TODO: AVOID HARDCODING CARBON MULTIPLE TIMES

                # define routine to compute the embodied CO2 and direct maintenance costs for ADORB
                def add_item_to_adorb_inputs(name, cost=None):
                    emissions_factor = countryEmissionsDatabase.loc[country, 'EF [kg/$]']
                    try:
                        # cross-reference with construction list if item exists
                        labor_fraction = constructionList.loc[name, "Labor_Fraction"]
                        lifetime = int(constructionList.loc[name, "Lifetime"])
                        if cost==None: cost = constructionList.loc[name, "Mechanical Cost"]
                    except KeyError:
                        print(f"Could not find \"{name}\" in construction database.")
                        return
                    embodied_carbon_calc = (cost * (1 - labor_fraction)) * (emissions_factor * price_of_carbon)
                    
                    # add cost anytime item needs installed or replaced
                    if lifetime != 0:
                        for year in range(0, duration, lifetime):
                            dirMR.append([cost, year])
                            emCO2.append([embodied_carbon_calc, year])
                    else:
                        dirMR.append([cost, 0])
                        emCO2.append([embodied_carbon_calc, 0])
                

                # extract cost line item subtotals
                fname = os.path.join(studyFolder, BaseFileName + '_BAtbl.htm')
                cost_line_item_detail_table = fasthtml.tablebyname(open(fname, 'r'), "Cost Line Item Details")
                cost_line_df = pd.DataFrame(cost_line_item_detail_table[1][1:],
                                            columns=cost_line_item_detail_table[1][0]).iloc[:-1] # drop the last summation row

                # compute emCO2 and dirMR per non-zero line item
                cost_line_df_subgroup = cost_line_df[cost_line_df["Quantity."] > 0]
                for _, row in cost_line_df_subgroup.iterrows():

                    # extract basic information
                    item_name = row["Item Name"].lower()
                    item_cost = row["SubTotal $"]

                    # strip any mechanical labels if neccessary
                    if item_name[:5] == "mech_": item_name = item_name[5:]

                    # handle appliance breakdown after loop
                    if item_name == "appliances" or item_name == "lights":
                        continue
                    
                    # for all normal entries compute and add to emCO2 and dirMR list
                    else:
                        add_item_to_adorb_inputs(item_name, item_cost)
                
                # compute emCO2 and dirMR per each appliance/lights 
                for appliance_name in appliance_list:
                    add_item_to_adorb_inputs(appliance_name.lower())

                # emCO2 = [(emCO2_firstCost,1),((8500*laborFraction*0.3),20),((8500*laborFraction*0.3),40),((8500*laborFraction*0.3),60)] 
                eTrans = peakElec
                
                final = adorb(BaseFileName, studyFolder, duration, annualElec, annualGas, annualCO2Elec, annualCO2Gas, dirMR, emCO2, eTrans, graphs)

                adorbCost = final[0]
                pv_dirEn_tot = final[1]
                pv_dirMR_tot = final[2]
                pv_opCO2_tot = final[3]
                pv_emCO2_tot = final[4]
                pv_eTrans_tot = final[5]

                # ===============================================================================================================
                # Final Result Collection
                # ===============================================================================================================
                newResultRow = pd.DataFrame([{'Run Name':runList['CASE_NAME'][runCount],
                                                    'SET ≤ 12.2°C Hours (F)':HeatingSET,
                                                    "Hours < 2°C [hr]":Below2C,
                                                    'Total Deadly Days':moraTotalDays,
                                                    'Min outdoor DB [°C]':MinDBOut,
                                                    'Min outdoor DP [°C]':MinDPOut,
                                                    'Max outdoor DB [°C]':MaxDBOut,
                                                    'Max outdoor DP [°C]':MaxDPOut,
                                                    "Caution (> 26.7, ≤ 32.2°C) [hr]":Caution,
                                                    "Extreme Caution (> 32.2, ≤ 39.4°C) [hr]":ExtremeCaution,
                                                    "Danger (> 39.4, ≤ 51.7°C) [hr]":Danger,
                                                    "Extreme Danger (> 51.7°C) [hr]":ExtremeDanger,
                                                    'EUI':eui,
                                                    'Peak Electric Demand [W]':peakElec,
                                                    'Heating Battery Size [kWh]':heatingBattery, 
                                                    'Cooling Battery Size [kWh]':coolingBattery,
                                                    'First Year Electric Cost [$]' : annualElec,
                                                    'First Year Gas Cost [$]':annualGas,
                                                    'First Cost [$]':firstCost[0],
                                                    'Wall Cost [$]':wallCost,
                                                    'Roof Cost [$]':roofCost,
                                                    'Floor Cost [$]':floorCost,
                                                    'Window Cost [$]':windowCost,
                                                    'Door Cost [$]':doorCost,
                                                    'Air Sealing Cost [$]':airSealing,
                                                    'Mechanical Cost [$]':mechCost,
                                                    'Water Heater Cost [$]':dhwCost,
                                                    'Appliances Cost [$]':applianceCost,
                                                    'PV Cost [$]':pvCost,
                                                    'Battery Cost [$]':batteryCost,
                                                    'Total ADORB Cost [$]':adorbCost,
                                                    'pv_dirEn_tot':pv_dirEn_tot,
                                                    'pv_dirMR_tot':pv_dirMR_tot,
                                                    'pv_opCO2_tot':pv_opCO2_tot,
                                                    'pv_emCO2_tot':pv_emCO2_tot,
                                                    'pv_eTrans_tot':pv_eTrans_tot}])
            
                newResultRow.to_csv(os.path.join(studyFolder, caseName + "_Test_ResultsTable.csv"))
                
                ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)#, ignore_index=True)

                if pdfReport == True:

                    PDF_Report(caseName, studyFolder, HeatingSET, Below2C, Caution, ExtremeCaution, Danger, ExtremeDanger, 
                            heatingBattery, coolingBattery, eui, peakElec, annualElec, annualGas,
                            firstCost, adorbCost, heatingGraphFile, coolingGraphFile, adorb.adorbWedgeGraph,
                            adorb.adorbBarGraph)

            except Exception as e:
                sg.popup(e)
                # errorFile1= (str(studyFolder) + '\eplusout.err')
                # errorFile2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BA_eplusout.sql')
                
                # if os.path.exists(errorFile2):
                #     os.remove(errorFile2)
                #     os.rename(errorFile1,errorFile2)
                newResultRow = pd.DataFrame([{'Run Name':runList['CASE_NAME'][runCount],
                                                        'SET ≤ 12.2°C Hours (F)':'ERROR',
                                                        "Hours < 2°C [hr]":'ERROR',
                                                        'Total Deadly Days':'ERROR',
                                                        'Min outdoor DB [°C]':'ERROR',
                                                        'Min outdoor DP [°C]':'ERROR',
                                                        'Max outdoor DB [°C]':'ERROR',
                                                        'Max outdoor DP [°C]':'ERROR',
                                                        "Caution (> 26.7, ≤ 32.2°C) [hr]":'ERROR',
                                                        "Extreme Caution (> 32.2, ≤ 39.4°C) [hr]":'ERROR',
                                                        "Danger (> 39.4, ≤ 51.7°C) [hr]":'ERROR',
                                                        "Extreme Danger (> 51.7°C) [hr]":'ERROR',
                                                        'EUI':'ERROR',
                                                        'Peak Electric Demand [W]':'ERROR',
                                                        'Heating Battery Size [kWh]':'ERROR', 
                                                        'Cooling Battery Size [kWh]':'ERROR',
                                                        'First Year Electric Cost [$]':'ERROR',
                                                        'First Year Gas Cost [$]':'ERROR',
                                                        'First Cost [$]':'ERROR',
                                                        'Wall Cost [$]':'ERROR',
                                                        'Roof Cost [$]':'ERROR',
                                                        'Floor Cost [$]':'ERROR',
                                                        'Window Cost [$]':'ERROR',
                                                        'Door Cost [$]':'ERROR',
                                                        'Air Sealing Cost [$]':'ERROR',
                                                        'Mechanical Cost [$]':'ERROR',
                                                        'Water Heater Cost [$]':'ERROR',
                                                        'Appliances Cost [$]':'ERROR',
                                                        'PV Cost [$]':'ERROR',
                                                        'Battery Cost [$]':'ERROR',
                                                        'Total ADORB Cost [$]':'ERROR',
                                                        'pv_dirEn_tot':'ERROR',
                                                        'pv_dirMR_tot':'ERROR',
                                                        'pv_opCO2_tot':'ERROR',
                                                        'pv_emCO2_tot':'ERROR',
                                                        'pv_eTrans_tot':'ERROR'}])
            
                newResultRow.to_csv(os.path.join(studyFolder, caseName + "_Test_ResultsTable.csv"))
                
                ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)#, ignore_index=Truue
                ResultsTable.to_csv(os.path.join(studyFolder, batchName + "_ResultsTable.csv"))
                # print('Saved Results')


        Parallel(n_jobs=int(parallel_cores))(delayed(simulation)(case, ResultsTable)for case in range(totalRuns))

        time.sleep(5)
        files = os.listdir(str(studyFolder))
        for file in files:
            if file.endswith('ResultsTable.csv'):
                newResultRow = pd.read_csv(os.path.join(studyFolder, file))
                ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)
        ResultsTable.to_csv(os.path.join(studyFolder, batchName + "_ResultsTable.csv"))
        print('Saved Results')


        # Utility Functions
        if cleanFolder == True:
            time.sleep(10)
            os.listdir(studyFolder)
            os.chdir(studyFolder)
            for filename in os.listdir(studyFolder):
                if filename.endswith('.idf'):
                        if 'PASS' in filename:
                            os.remove(filename)
                if filename.endswith('.sql'):
                    os.remove(filename)
                if filename.endswith('.rdd'):
                    os.remove(filename)
                if filename.endswith('.shd'):
                    os.remove(filename)
                if filename.endswith('.rvaudit'):
                    os.remove(filename)
                if filename.endswith('.mtr'):
                    os.remove(filename)
                if filename.endswith('.mtd'):
                    os.remove(filename)
                if filename.endswith('.mdd'):
                    os.remove(filename)
                if filename.endswith('.eso'):
                    os.remove(filename)
                if filename.endswith('.err'):
                    os.remove(filename)
                if filename.endswith('.eio'):
                    os.remove(filename)
                if filename.endswith('.end'):
                    os.remove(filename)
                if filename.endswith('.bnd'):
                    os.remove(filename)
                if filename.endswith('.audit'):
                    os.remove(filename)
                # Latex
                if filename.endswith('.tex'):
                    os.remove(filename)
                if filename.endswith('.log'):
                    os.remove(filename)
                if filename.endswith('.fls'):
                    os.remove(filename)
                if filename.endswith('.fdb_latexmk'):
                    os.remove(filename)
                if filename.endswith('.aux'):
                    os.remove(filename)


        sg.popup('Analysis Complete')