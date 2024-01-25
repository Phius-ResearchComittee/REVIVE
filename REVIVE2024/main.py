#=============================================================================================================================
# PhiusREVIVE Research Tool
# Updated 2023/11/27
# v24.1.0
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
import datetime as dt
from datetime import datetime
import email.utils as eutils
from statistics import mean
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
import gc
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
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
from hvac import *
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
                [sg.Text('Study Folder:', size =(15, 1)),sg.InputText('C:/REVIVE v23.1.0/Parametric Runs 2', key='studyFolder'), sg.FolderBrowse()],
                [sg.Text('Geometry IDF:', size =(15, 1)),sg.InputText('C:/REVIVE v23.1.0/Databases/Sample Geometry/PNNL_SF_Geometry.idf', key='GEO'), sg.FileBrowse()],
                [sg.Text('Run List Location:', size =(15, 1)),sg.InputText('C:/REVIVE v23.1.0/Parametric Run List/ChicagoIL_ParametricRuns_2023-12-06.csv', key='runList'), sg.FileBrowse()],
                [sg.Text('Database Folder Location:', size =(15, 1)),sg.InputText('C:/REVIVE v23.1.0/Databases', key='dataBases'), sg.FolderBrowse()]
                ]

tab2_layout =   [[sg.Checkbox('Generate PDF?', size=(25, 1), default=False,key='genPDF')],
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

window = sg.Window('Phius REVIVE 2024 Analysis Tool v24.1.0',layout1, default_element_size=(125, 125), grab_anywhere=True)

#==============================================================================================================================
# 3.0 File Management
#==============================================================================================================================
while True:
    event, inputValues = window.read()
    if event == 'LOAD':
        runListPath = inputValues['runList']
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
        ResultsTable = pd.DataFrame(columns=["Run Name","SET ≤ 12.2°C Hours (F)","Hours < 2°C [hr]",'Total Deadly Days','Min outdoor DB [°C]','Min outdoor DP [°C]',
                                                    'Max outdoor DB [°C]','Max outdoor DP [°C]',"Caution (> 26.7, ≤ 32.2°C) [hr]","Extreme Caution (> 32.2, ≤ 39.4°C) [hr]",
                                                    "Danger (> 39.4, ≤ 51.7°C) [hr]","Extreme Danger (> 51.7°C) [hr]", 'EUI','Peak Electric Demand [W]',
                                                    'Heating Battery Size [kWh]', 'Cooling Battery Size [kWh]', 'Total ADORB Cost [$]','First Year Electric Cost [$]',
                                                    'First Year Gas Cost [$]','First Cost [$]','Wall Cost [$]','Roof Cost [$]','Floor Cost [$]','Window Cost [$]',
                                                    'Door Cost [$]','Air Sealing Cost [$]','Mechanical Cost [$]','Water Heater Cost [$]','Appliances Cost [$]','PV Cost [$]',
                                                    'Battery Cost [$]','pv_dirEn_tot','pv_dirMR_tot','pv_opCO2_tot','pv_emCO2_tot','pv_eTrans_tot'])
        for case in range(totalRuns):
            try:
                iddfile = str(inputValues['iddFile'])
                runListPath = inputValues['runList']
                studyFolder = inputValues['studyFolder']
                databases = inputValues['dataBases']

                idfgName = inputValues['GEO']
                emissionsDatabase = (str(inputValues['dataBases']) + 'Hourly Emission Rates.csv')
                weatherDatabase = (str(inputValues['dataBases']) + '/Weather Data/')
                runList = pd.read_csv(str(runListPath))
                totalRuns = runList.shape[0]
                batchName = str(inputValues['batchName'])

                pdfReport = inputValues['genPDF']
                graphs = inputValues['GenerateGraphs']
                cleanFolder = inputValues['DeleteFiles']


                os.chdir(str(studyFolder))
                IDF.setiddname(iddfile)

                runCount = case
                BaseFileName = (batchName + '_' + runList['CASE_NAME'][runCount])
                caseName = runList['CASE_NAME'][runCount]

                sg.one_line_progress_meter('Progress Meter', runCount, totalRuns, 'Analysis Running','Current Case: ' + str(caseName))

                print('Running: ' + str(BaseFileName))

                # testingFile = str(studyFolder) + "/" + str(BaseFileName) + ".idf"
                testingFile_BA = str(studyFolder) + "/" + str(BaseFileName) + "_BA.idf"
                testingFile_BR = str(studyFolder) + "/" + str(BaseFileName) + "_BR.idf"
                passIDF = str(studyFolder) + "/" + str(BaseFileName) + "_PASS.idf"

                #==============================================================================================================================
                # 4.0 Variable Assignment
                #==============================================================================================================================

                epwFile = str(weatherDatabase) + str(runList['EPW'][runCount])
                ddyName =  str(weatherDatabase) + str(runList['DDY'][runCount])

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

                fridge = (445/(8760))*1000 # always on design load
                fracHighEff = 1.0
                PhiusLights = (0.2 + 0.8*(4 - 3*fracHighEff)/3.7)*(455 + 0.8*icfa) * 0.8 * 1000 * (1/365) #power per day W use Phius calc
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
                Version(idf1)
                SimulationControl(idf1)
                Building(idf1,BaseFileName)
                CO2Balance(idf1)
                Timestep(idf1)
                RunPeriod(idf1)
                GeometryRules(idf1)

                # IHGs
                People(idf1, occ)
                LightsMELsAppliances(idf1, PhiusLights, PhiusMELs, fridge, rangeElec, 
                                    clothesDryer,clothesWasher,dishWasher)
                SizingLoads(idf1, sizingLoadSensible, sizingLoadLatent)
                ThermalMass(idf1, icfa_M)


                # Materials and constructions
                materials = pd.read_csv(str(inputValues['dataBases']) + '/Material Database.csv')
                materialList = materials.shape[0]

                for item in range(materialList):
                    materialBuilder(idf1, materials['NAME'][item], materials['ROUGHNESS'][item], 
                                    materials['THICKNESS [m]'][item], materials['CONDUCTIVITY [W/mK]'][item],
                                    materials['DENSITY [kg/m3]'][item], materials['SPECIFIC HEAT CAPACITY [J/kgK]'][item])
                    
                glazingSpecs = pd.read_csv(str(inputValues['dataBases']) + '/Window Database.csv')

                glazings = glazingSpecs.shape[0]

                for item in range(glazings):
                    glazingBuilder(idf1, glazingSpecs['NAME'][item], glazingSpecs['U-FACTOR [W/m2K]'][item],glazingSpecs['SHGC'][item])

                # Constructions 
                #     
                constructionList = pd.read_csv(str(inputValues['dataBases']) + '/Construction Database.csv')

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

                ReslienceERV(idf1, occ, ervSense, ervLatent)

                WeatherMorphSine(idf1, outage1start, outage1end, outage2start, outage2end,
                        MorphFactorDB1, MorphFactorDP1, MorphFactorDB2, MorphFactorDP2)


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
                hourlyBA = pd.read_csv(filehandle)

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

                    heatingGraphFile = (str(studyFolder) + "/" + str(BaseFileName) + "_Heating Outage Resilience Graphs.png")

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

                    coolingGraphFile = (str(studyFolder) + "/" + str(BaseFileName) + "_Cooling Outage Resilience Graphs.png")

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

                AnnualSchedules(idf1, outage1start, outage1end, outage2start, outage2end, 
                            coolingOutageStart,coolingOutageEnd,NatVentAvail,
                            demandCoolingAvail,shadingAvail)

                AnnualERV(idf1, occ, ervSense, ervLatent)

                for item in range(constructions):
                    
                    name = constructionList['Name'][item]
                    outerLayer = constructionList['Outside_Layer'][item]
                    cost = constructionList['Cost_Per_Area_[$/m2]'][item]
                    costSealing = constructionList['Air_Sealing_Cost_[$/ft2 ICFA]'][item]
                    costBatt = constructionList['Battery_Cost_[$/kWh]'][item]
                    costPV = constructionList['PV_Cost_[$/W]'][item]
                    costMech = constructionList['Mechanical Cost'][item]

                    if cost > 0 and str(outerLayer) != 'nan':
                        costBuilder(idf1, name, '','Construction', name,'','',cost,'')
                    
                    if costSealing > 0 and str(name) == str(flowCoefficient):
                        costBuilder(idf1,('AIR SEALING = ' + str(name)),'','General',0,0,(costSealing*icfa),'',1)

                    if costMech> 0 and str(name) == str(mechSystemType):
                        costBuilder(idf1, ('MECH_' + str(name)),'','General',0,0,costMech,'',1)

                    if costMech> 0 and str(dhwFuel) in str(name):
                        costBuilder(idf1, (str(name)),'','General',0,0,costMech,'',1)
                    
                    if costMech> 0 and 'Apppliances' in str(name):
                        costBuilder(idf1, (str(name)),'','General',0,0,costMech,'',1)
                    
                    if costBatt > 0 and str(outerLayer) == 'nan':
                        costBuilder(idf1, name,'' ,'General',0,0,(costBatt*max(heatingBattery,coolingBattery)),'',1)

                    if costPV > 0 and str(outerLayer) == 'nan':
                        costBuilder(idf1, name,'' ,'General',0,0,(costPV*PV_SIZE),'',1)


                    
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
                    for ltable in ltables:
                        if 'Construction Cost Estimate Summary' in '\n'.join(ltable[0]): #and 'For: Entire Facility' in '\n'.join(ltable[0]):
                            firstCost = [(float(ltable[1][9][2])),0]
                            # firstCost = [(float(ltable[1][9][2])*1.8),0]
                        if 'Cost Line Item Details' in '\n'.join(ltable[0]):
                            rows = len(ltable[1])
                            for row in range(rows):
                                # print(ltable[1][row][2])
                                # print(ltable[1][row][5])
                                if 'WALL' in str(ltable[1][row][2]):
                                    wallCostList.append(ltable[1][row][6])
                                if 'ROOF' in str(ltable[1][row][2]):
                                    roofCostList.append(ltable[1][row][6])
                                if 'FLOOR' in str(ltable[1][row][2]):
                                    floorCostList.append(ltable[1][row][6])
                                if 'WINDOW' in str(ltable[1][row][2]):
                                    windowCostList.append(ltable[1][row][6])
                                if 'DOOR' in str(ltable[1][row][2]):
                                    doorCostList.append(ltable[1][row][6])
                                if 'AIR SEALING' in str(ltable[1][row][2]):
                                    airSealingCostList.append(ltable[1][row][6])
                                if 'MECH' in str(ltable[1][row][2]):
                                    mechCostList.append(ltable[1][row][6])
                                if 'DHW' in str(ltable[1][row][2]):
                                    dhwCostList.append(ltable[1][row][6])
                                if 'APPLIANCE' in str(ltable[1][row][2]):
                                    applianceCostList.append(ltable[1][row][6])
                                if 'PV COST' in str(ltable[1][row][2]):
                                    pvCost = (ltable[1][row][6])
                                if 'BATTERY COST' in str(ltable[1][row][2]):
                                    batteryCost = (ltable[1][row][6])

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

    ##################ADORB 436253 RED QUEEN PIN

                hourlyBA.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
                hourlyBA[['Date2','Time']] = hourlyBA.DateTime.str.split(expand=True)
                hourlyBA['Date'] = hourlyBA['Date2'].map(str) + '/' + str(2020)
                hourlyBA['Time'] = (pd.to_numeric(hourlyBA['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourlyBA['Time'].str[2:]
                hourlyBA['DateTime'] = hourlyBA['Date'] + ' ' + hourlyBA['Time']
                hourlyBA['DateTime'] = pd.to_datetime(hourlyBA['DateTime'])

                endWarmup = int((hourlyBA[hourlyBA['DateTime'] == '2020-01-01 00:00:00'].index.values))
                dropWarmup = [*range(0, endWarmup,1)]

                hourlyBA = hourlyBA.drop(index = dropWarmup)
                hourlyBA = hourlyBA.reset_index()

                MWH = hourlyBA['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)']*0.0000000002778

                CO2_Elec_List = []
                count = 0
                os.listdir(str(databases) + '/CambiumFactors')
                for filename in os.listdir(str(databases) + '/CambiumFactors'):
                    if filename.endswith('.csv'):
                        hourlyBAEmissions = pd.read_csv(str(databases) + '/CambiumFactors/' + str(filename))
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

                duration = 70
                elecPrice = float(runList['ELEC_PRICE_[$/kWh]'][runCount])
                annualElec = ((hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum()*0.0000002778*elecPrice)+100)
                
                # annualCO2 = CO2_Elec + CO2_gas

                carbonDatabase = pd.read_csv(str(inputValues['dataBases']) + '/Carbon Correction Database.csv')
                countryEmissionsDatabase = pd.read_csv(str(inputValues['dataBases']) + '/Country Emission Database.csv')

                if str(runList['CARBON_MEASURES'][runCount]) != 'nan':
                    carbonMeasures = carbondMeasures = list(runList['CARBON_MEASURES'][runCount].split(', '))

                carbonMeasureCost = []

                for measure in range(carbonDatabase.shape[0]):
                    if carbonDatabase['Name'][measure] in carbonMeasures:
                        carbonMeasureCost.append((carbonDatabase['Cost'][measure], carbonDatabase['Year'][measure]))

                carbonMeasureCost.append(firstCost)

                emCO2 = []

                for measure in range(carbonDatabase.shape[0]):
                    if carbonDatabase['Name'][measure] in carbonMeasures:
                        for country in range(countryEmissionsDatabase.shape[0]):
                            if str(countryEmissionsDatabase['COUNTRY'][country]) == str(carbonDatabase['Country'][1]):
                                ef = countryEmissionsDatabase['EF [kg/$]'][country]
                            if str(countryEmissionsDatabase['COUNTRY'][country]) == 'USA':
                                efUSA = countryEmissionsDatabase['EF [kg/$]'][country]
                        emCO2.append(((carbonDatabase['Cost'][measure]*ef*(1-carbonDatabase['Labor Fraction'][measure])) + 
                                      ((carbonDatabase['Cost'][measure]*efUSA*(carbonDatabase['Labor Fraction'][measure]))), carbonDatabase['Year'][measure]))
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
            
                newResultRow.to_csv(str(studyFolder) + "/" + str(caseName) + "_Test_ResultsTable.csv")
                
                ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)#, ignore_index=True)

                if pdfReport == True:

                    PDF_Report(caseName, studyFolder, HeatingSET, Below2C, Caution, ExtremeCaution, Danger, ExtremeDanger, 
                            heatingBattery, coolingBattery, eui, peakElec, annualElec, annualGas,
                            firstCost, adorbCost, heatingGraphFile, coolingGraphFile, adorb.adorbWedgeGraph,
                            adorb.adorbBarGraph)

                
                ResultsTable.to_csv(str(studyFolder) + "/" + str(batchName) + "_ResultsTable.csv")
                print('Saved Results')

            except:
                errorFile1= (str(studyFolder) + '\eplusout.err')
                errorFile2 = (str(studyFolder) + "/" + str(BaseFileName)  + '_BA_eplusout.sql')
                
                if os.path.exists(errorFile2):
                    os.remove(errorFile2)
                    os.rename(errorFile1,errorFile2)
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
            
                newResultRow.to_csv(str(studyFolder) + "/" + str(caseName) + "_Test_ResultsTable.csv")
                
                ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)#, ignore_index=Truue
                ResultsTable.to_csv(str(studyFolder) + "/" + str(batchName) + "_ResultsTable.csv")
                print('Saved Results')




        if cleanFolder == True:
            os.listdir(studyFolder)
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