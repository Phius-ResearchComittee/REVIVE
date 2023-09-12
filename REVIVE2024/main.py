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
import PySimpleGUI as sg
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system

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
                [sg.Text('Please follow the steps below to test thermal resilience of the house')],
                ]

tab1_layout =   [[sg.Text('IDD File Location:', size =(15, 1)),sg.InputText("C:\EnergyPlusV9-5-0\Energy+.idd", key='iddFile'), sg.FileBrowse()],
                [sg.Text('Study Folder:', size =(15, 1)),sg.InputText('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29', key='studyFolder'), sg.FolderBrowse()],
                [sg.Text('Geometry IDF:', size =(15, 1)),sg.InputText('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/PNNL_SF_Geometry.idf', key='GEO'), sg.FileBrowse()],
                [sg.Text('Run List Location:', size =(15, 1)),sg.InputText('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29/testRuns.csv', key='runList'), sg.FileBrowse()],
                [sg.Text('Database Folder Location:', size =(15, 1)),sg.InputText('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Databases/', key='dataBases'), sg.FileBrowse()]
                ]

tab2_layout =   [[sg.Text('Batch Name:', size =(20, 1)),sg.InputText('Name your batch of files', key='batchName')]
                ]

layout1 = [
    # [sg.Image(r'C:\Users\amitc\Documents\GitHub\Phius-REVIVE\Project Program\4StepResilience\al_REVIVE_PILOT_logo.png')],
                [sg.TabGroup(
                [[sg.Tab('Start', tab0_layout,),
                sg.Tab('Project Settings', tab1_layout,),
                sg.Tab('Basic Input Data', tab2_layout,),]])],
                [sg.Button('LOAD'), sg.Button('RUN ANALYSIS'), sg.Button('EXIT')]]  

window = sg.Window('Phius REVIVE 2024 Analysis Tool v0.2',layout1, default_element_size=(125, 125), grab_anywhere=True)

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

    if event == 'RUN ANALYSIS':
        ResultsTable = pd.DataFrame(columns=["Run Name","SET ≤ 12.2°C Hours (F)","Hours < 2°C [hr]","Caution (> 26.7, ≤ 32.2°C) [hr]","Extreme Caution (> 32.2, ≤ 39.4°C) [hr]",
                                                    "Danger (> 39.4, ≤ 51.7°C) [hr]","Extreme Danger (> 51.7°C) [hr]", 'EUI','Peak Electric Demand [W]',
                                                    'Heating Battery Size [kWh]', 'Cooling Battery Size [kWh]', 'Total ADORB Cost [$]','First Year Electric Cost [$]',
                                                    'First Year Gas Cost [$]','First Cost [$]','pv_dirEn_tot','pv_dirMR_tot','pv_opCO2_tot','pv_emCO2_tot',
                                                    'pv_eTrans_tot'])
        for case in range(totalRuns):
            iddfile = str(inputValues['iddFile'])
            runListPath = inputValues['runList']
            studyFolder = inputValues['studyFolder']
            idfgName = inputValues['GEO']
            emissionsDatabase = (str(inputValues['dataBases']) + 'Hourly Emission Rates.csv')
            runList = pd.read_csv(str(runListPath))
            totalRuns = runList.shape[0]
            batchName = str(inputValues['batchName'])

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

            epwFile = runList['EPW'][runCount]
            ddyName = runList['DDY'][runCount]

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

            Ext_Wall2 = 0
            Ext_Wall3 = 0
            Ext_Roof2 = 0
            Ext_Roof3 = 0
            Ext_Floor2 = 0
            Ext_Floor3 = 0

            # Foundation interfaces
            fnd1 = runList['FOUNDATION_INTERFACE_1'][runCount]
            fnd1i = runList['FOUNDATION_INSUINSULATION_1'][runCount]
            fnd1p = runList['FOUNDATION_PERIMETER_1'][runCount]
            fnd1d = runList['FOUNDATION_INSULATION_DEPTH_1'][runCount]

            # fnd2 = 'Crawl'
            # fnd2i = 'XPS'
            # fnd2p = 30
            # fnd2d = 2*0.3048

            # fnd3 = 'Basement'
            # fnd3i = 'MWB'
            # fnd3p = 35
            # fnd3d = 2*0.3048

            foundationList = [(fnd1,fnd1i,fnd1d,fnd1p)]
                        # (fnd2,fnd2i,fnd2d,fnd2p),
                        # (fnd3,fnd3i,fnd3d,fnd3p)]

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
            materialBuilder(idf1, 'M01 100mm brick', 'MediumRough', 0.1016, 0.89, 1920, 790)
            materialBuilder(idf1, 'G05 25mm wood', 'MediumSmooth', 0.0254, 0.15, 608, 1630)
            materialBuilder(idf1, 'F08 Metal surface', 'Smooth', 0.0008, 45.28, 7824, 500)
            materialBuilder(idf1, 'I01 25mm insulation board', 'MediumRough', 0.0254, 0.03, 43, 1210)
            materialBuilder(idf1, 'I02 50mm insulation board', 'MediumRough', 0.0508, 0.03, 43, 1210)
            materialBuilder(idf1, 'G01a 19mm gypsum board', 'MediumSmooth', 0.019, 0.16, 800, 1090)
            materialBuilder(idf1, 'M11 100mm lightweight concrete', 'MediumRough', 0.1016, 0.53, 1280, 840)
            materialBuilder(idf1, 'F16 Acoustic tile', 'MediumSmooth', 0.0191, 0.06, 368, 590)
            materialBuilder(idf1, 'M15 200mm heavyweight concrete', 'MediumRough', 0.2032, 1.95, 2240, 900)
            materialBuilder(idf1, 'M05 200mm concrete block', 'MediumRough', 0.1016, 1.11, 800, 920)
            materialBuilder(idf1, 'Mass wood', 'MediumSmooth', 0.065532, 0.15, 608.701223809829, 1630)
            materialBuilder(idf1, 'Foundation EPS', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
            materialBuilder(idf1, 'F11 Wood siding', 'MediumSmooth', 0.0127, 0.09, 592, 1170)
            materialBuilder(idf1, 'R-11 3.5in Wood Stud', 'VeryRough', 0.0889, 0.05426246, 19, 960)
            materialBuilder(idf1, 'Plywood (Douglas Fir) - 12.7mm', 'Smooth', 0.0127, 0.12, 540, 1210)
            materialBuilder(idf1, 'EPS 1in', 'MediumSmooth', 0.0254, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 1.625in', 'MediumSmooth', 0.041275, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 2in', 'MediumSmooth', 0.0508, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 4in', 'MediumSmooth', 0.1016, 0.02884, 29, 1210 )
            materialBuilder(idf1, 'EPS 6in', 'MediumSmooth', 0.1524, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 7.5in', 'MediumSmooth', 0.1905, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 9in', 'MediumSmooth', 0.1524, 0.02884, 29, 1210)
            materialBuilder(idf1, 'EPS 14in', 'MediumSmooth', 0.3556, 0.02884, 29, 1210)
            materialBuilder(idf1, 'FG Attic R-19', 'MediumRough', 0.13716, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-30', 'MediumRough', 0.21844, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-38', 'MediumRough', 0.275844, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-49', 'MediumRough', 0.3556, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-55', 'MediumRough', 0.3991229, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-60', 'MediumRough', 0.3556, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-75', 'MediumRough', 0.54356, 0.04119794, 64, 960)
            materialBuilder(idf1, 'FG Attic R-100', 'MediumRough', 0.72644, 0.04119794, 64, 960)
            materialBuilder(idf1, 'ccSF R-13', 'Rough', 0.05503418, 0.024033814, 32, 920)
            materialBuilder(idf1, 'ccSF R-19', 'Rough', 0.080433418, 0.024033814, 32, 920)
            materialBuilder(idf1, 'ccSF R-30', 'Rough', 0.127, 0.024033814, 32, 920)
            materialBuilder(idf1, 'ccSF R-38', 'Rough', 0.160866582, 0.024033814, 32, 920)
            materialBuilder(idf1, 'ccSF R-49', 'Rough', 0.207433418, 0.024033814, 32, 920)
            materialBuilder(idf1, 'StemWall UnIns', 'MediumRough', 0.003175, 0.53, 1280, 840)

            constructionBuilder(idf1, 'Brick Wall', ['M01 100mm brick'])
            constructionBuilder(idf1, 'Ext_Door1',['G05 25mm wood'])
            constructionBuilder(idf1, 'Thermal Mass',['G05 25mm wood'])
            constructionBuilder(idf1, 'Interior Floor', ['Plywood (Douglas Fir) - 12.7mm', 'F05 Ceiling air space resistance', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Slab UnIns', ['M15 200mm heavyweight concrete'])
            constructionBuilder(idf1, 'Exterior Slab + 2in EPS', ['EPS 2in', 'M15 200mm heavyweight concrete'])
            constructionBuilder(idf1, 'Exterior Wall', ['F11 Wood siding', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Interior Wall', ['G01a 19mm gypsum board', 'F04 Wall air space resistance', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof', ['FG Attic R-19', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Door', ['F08 Metal surface', 'I02 50mm insulation board', 'F08 Metal surface'])
            constructionBuilder(idf1, 'Interior Door', ['G05 25mm wood'])
            constructionBuilder(idf1, 'Exterior Wall +1in EPS', ['F11 Wood siding', 'EPS 1in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +1.625in EPS', ['F11 Wood siding', 'EPS 1.625in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +2in EPS', ['F11 Wood siding', 'EPS 2in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +4in EPS', ['F11 Wood siding', 'EPS 4in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +7.5in EPS', ['F11 Wood siding', 'EPS 7.5in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +6in EPS', ['F11 Wood siding', 'EPS 6in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +9in EPS', ['F11 Wood siding', 'EPS 9in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Wall +14in EPS', ['F11 Wood siding', 'EPS 14in', 'Plywood (Douglas Fir) - 12.7mm', 'R-11 3.5in Wood Stud', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-30', ['FG Attic R-30', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-38', ['FG Attic R-38', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-49', ['FG Attic R-49', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-55', ['FG Attic R-55', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-60', ['FG Attic R-60', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-75', ['FG Attic R-75', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'Exterior Roof R-100', ['FG Attic R-100', 'Plywood (Douglas Fir) - 12.7mm', 'G01a 19mm gypsum board'])
            constructionBuilder(idf1, 'P+B UnIns', ['Plywood (Douglas Fir) - 12.7mm', 'F05 Ceiling air space resistance', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
            constructionBuilder(idf1, 'P+B R-13', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-13', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
            constructionBuilder(idf1, 'P+B R-19', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-19', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
            constructionBuilder(idf1, 'P+B R-30', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-30', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
            constructionBuilder(idf1, 'P+B R-38', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-38', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])
            constructionBuilder(idf1, 'P+B R-49', ['Plywood (Douglas Fir) - 12.7mm', 'ccSF R-49', 'Plywood (Douglas Fir) - 12.7mm', 'G05 25mm wood'])

            costBuilder(idf1, 'Wall 1', '','Construction', 'Exterior Wall +1in EPS','','',13.77915008)
            costBuilder(idf1, 'Wall 2', '','Construction', 'Exterior Wall +1.625in EPS','','',16.79333916)
            costBuilder(idf1, 'Wall 3', '','Construction', 'Exterior Wall +2in EPS','','',18.62338253)
            costBuilder(idf1, 'Wall 4', '','Construction', 'Exterior Wall +4in EPS','','',25.40530796)
            costBuilder(idf1, 'Wall 5', '','Construction', 'Exterior Wall +6in EPS','','',34.55552481)
            costBuilder(idf1, 'Wall 6', '','Construction', 'Exterior Wall +9in EPS','','',46.93522996)
            costBuilder(idf1, 'Wall 7', '','Construction', 'Exterior Wall +14in EPS','','',63.6209195100001)
            costBuilder(idf1, 'Roof 1', '','Construction', 'Exterior Roof R-30','','',7.96607114000001)
            costBuilder(idf1, 'Roof 2', '','Construction', 'Exterior Roof R-49','','',8.39666958000001)
            costBuilder(idf1, 'Roof 3', '','Construction', 'Exterior Roof R-60','','',21.529922)
            costBuilder(idf1, 'Roof 4', '','Construction', 'Exterior Roof R-75','','',39.39975726)
            costBuilder(idf1, 'Roof 5', '','Construction', 'Exterior Roof R-100','','',69.3263488400001)
            costBuilder(idf1, 'Window 1', '','Construction', 'ExteriorWindow1','','',(147*math.exp(0.23*Ext_Window1_Ufactor)))

            # Envelope inputs
            Infiltration(idf1, flowCoefficient)
            SpecialMaterials(idf1)
            FoundationInterface(idf1,foundationList)


            ShadeMaterials(idf1)

            # Window inputs and shading controls
            WindowVentilation(idf1, halfHeight, operableArea_N, operableArea_W, 
                      operableArea_S, operableArea_E)
            WindowMaterials(idf1, Ext_Window1_Ufactor,Ext_Window1_SHGC)

            AssignContructions(idf1, Ext_Wall1,Ext_Wall2,Ext_Wall3,
                       Ext_Roof1,Ext_Roof2,Ext_Roof3,
                       Ext_Floor1,Ext_Floor2,Ext_Floor3,
                       Ext_Door1, Int_Floor1)

            # Sizing settings:
            SizingSettings(idf1, ZoneName)
            HVACControls(idf1, ZoneName)
            ZoneMechConnections(idf1, ZoneName)
            HVACBuilder(idf1, ZoneName, mechSystemType)
            WaterHeater(idf1, ZoneName, dhwFuel, DHW_CombinedGPM)
            Curves(idf1)

            Renewables(idf1, ZoneName)

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
                        demandCoolingAvail,shadingAvail)
            
            ResilienceControls(idf1, NatVentType)

            ReslienceERV(idf1, occ, ervSense, ervLatent)

            # WeatherMorphSine(idf1, outage1start, outage1end, outage2start, outage2end,
                    #  MorphFactorDB1, MorphFactorDP1, MorphFactorDB2, MorphFactorDP2)


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

            AnnualSchedules(idf1, outage1start, outage1end, outage2start, outage2end, 
                        coolingOutageStart,coolingOutageEnd,NatVentAvail,
                        demandCoolingAvail,shadingAvail)

            AnnualERV(idf1, occ, ervSense, ervLatent)



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

##################ADORB

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
            
            final = adorb(BaseFileName, studyFolder, duration, annualElec, annualGas, annualCO2, dirMR, emCO2, eTrans)

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
                                                'pv_eTrans_tot':pv_eTrans_tot}])
        
            newResultRow.to_csv(str(studyFolder) + "/" + str(caseName) + "_Test_ResultsTable.csv")
            
            ResultsTable = pd.concat([ResultsTable, newResultRow], axis=0, ignore_index=True)#, ignore_index=True)
            
        ResultsTable.to_csv(str(studyFolder) + "/" + str(batchName) + "_ResultsTable.csv")

        sg.popup('Analysis Complete')