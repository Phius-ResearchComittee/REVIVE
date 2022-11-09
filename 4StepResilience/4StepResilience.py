#=============================================================================================================================
# 4 Step Resilience Analyzer
# Updated 2022/06/10
#   v1
#   v1.1 - improved graphs.  first version for internal release
#   v1.2 - added icfa and partition ratio inputs, updated graphs and legend location
#
#
""""
Copyright (c) 2022 Phius

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#==============================================================================================================================
# Outline
# 1. Dependencies
# 2. Simple GUI Setup

#==============================================================================================================================
# 1. Set up dependencies
#==============================================================================================================================

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime as dt
import email.utils as eutils
import time

import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
import PySimpleGUI as sg
from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
import subprocess
import os
from os import system

import pprint
pp = pprint.PrettyPrinter()


#==============================================================================================================================
# 2. Simply GUI Setup
#==============================================================================================================================

sg.theme('LightBlue2')
BAR_MAX = 24

tab0_layout =  [[sg.Text('Welcome')],
                [sg.Text('Please follow the steps below to test thermal resilience of the house')],
                [sg.Text('0. Click IMPORT TEMPLATE to creat a new blank IDF from template')],
                [sg.Text('1. Click IMPORT to import geometry from the base IDF and design weather data from DDY')],
                [sg.Text('2. Click CREATE to create an IDF from CSV Run List')],
                [sg.Text('3. Run parametric IDF using EP-Launch')],
                [sg.Text('4. Click COLLECT to compile results')],
                ]

tab1_layout =   [[sg.Text('Study Folder:', size =(15, 1)),sg.InputText('C:\\4StepResiliencev1-2', key='StudyFolder'), sg.FolderBrowse()],
                [sg.Text('Geometry IDF:', size =(15, 1)),sg.InputText('Select IDF with Geometry', key='GEO'), sg.FileBrowse()],
                [sg.Text('Template IDF:', size =(15, 1)),sg.InputText('C:\\4StepResiliencev1-2\\00_SF Base v1_noGeo.idf', key='template'), sg.FileBrowse()],
                [sg.Text('DDY:', size =(15, 1)),sg.InputText('Select DDY File', key='DDY'), sg.FileBrowse()],
                [sg.Text('IDD File Location:', size =(15, 1)),sg.InputText("C:\EnergyPlusV9-5-0\Energy+.idd", key='iddFile'), sg.FileBrowse()],
                [sg.Button('IMPORT TEMPLATE',  button_color=('white', 'orange'))],
                ]

tab2_layout =   [[sg.Text('File Name:', size =(20, 1)),sg.InputText('Name your file', key='BaseFileName')],
                [sg.Text('Occupancy:', size =(20, 1)),sg.InputText('4', key='Occupants')],
                [sg.Text('ICFA:', size =(20, 1)),sg.InputText('2128', key='ICFA')],
                [sg.Text('Partition to ICFA Ratio:', size =(20, 1)),sg.InputText('1.0', key='PartitionRatio')],
                [sg.Text('For plotting temperature and RH during outage:')],
                [sg.Text('Outage 1 Start Date:', size =(20, 1)),sg.InputText('2020-01-26 00:00:00', key='OS1')],
                [sg.Text('Outage 1 End Date:', size =(20, 1)),sg.InputText('2020-02-04 00:00:00', key='OE1')],
                [sg.Text('Outage 2 Start Date:', size =(20, 1)),sg.InputText('2020-07-19 00:00:00', key='OS2')],
                [sg.Text('Outage 2 End Date:', size =(20, 1)),sg.InputText('2020-07-30 00:00:00', key='OE2')],
                ]

layout1 = [[sg.Image(r'C:\Users\amitc\Documents\GitHub\Phius-REVIVE\Project Program\4StepResilience\al_REVIVE_PILOT_logo.png')],
                [sg.TabGroup(
                [[sg.Tab('Start', tab0_layout,),
                sg.Tab('Project Settings', tab1_layout,),
                sg.Tab('Basic Input Data', tab2_layout,),]])],
                [sg.Text('COLLECT Progress:')],
                [sg.ProgressBar(BAR_MAX, orientation='h', size=(20,20), key='-PROG-')],
                [sg.Button('IMPORT'), sg.Button('CREATE'), sg.Button('COLLECT'), sg.Button('EXIT')]]  

window = sg.Window('4 Step Resilience Test v1.2',layout1, default_element_size=(125, 125), grab_anywhere=True)   

#=============================================================================================================================
# 3. Loops
#=============================================================================================================================

while True:
    event, values = window.read()  

    #extractValues
    #Name = values['ProjectName']
    start_date = values['OS1']
    end_date = values['OE1']
    start_date2 = values['OS2']
    end_date2 = values['OE2']
    #cases = 12
    BaseFileName = values['BaseFileName']
    studyFolder = values['StudyFolder']
    iddfile = str(values['iddFile'])
    templateFile = str(values['template'])
    idfgName = str(values['GEO'])
    ddyName = values['DDY']
    occ = values['Occupants']
    icfa = (float(values['ICFA'])/10.76391)
    PartitionRatio = float(values['PartitionRatio'])


    #Vars
    os.chdir(str(studyFolder))
    testingFile = str(studyFolder) + "/" + str(BaseFileName) + ".idf"
    iddfile = str(values['iddFile'])
    fname1 = str(templateFile)
    runList = str(studyFolder) + "/" + "runs.csv"


    #if os.path.exists(testingFile):
    #    os.remove(testingFile)

    IDF.setiddname(iddfile)
    #epwfile = "C:\\ResilienceTest_v1\\USA_IL_Chicago.Midway.Intl.AP.725340_TMY3.epw"

    fname2 = str(studyFolder) + "/"  + str(BaseFileName) + ".idf"
    #idf2 = IDF(fname2)
    idfg = IDF(idfgName)
    ddy = IDF(ddyName)

    os.chdir(str(studyFolder))
    df = pd.read_csv(runList)
    RunNames = pd.read_csv(runList)
    df = df.fillna('')
    #df = df.dropna()
    length = df.shape

    CaseName = df["RunName"].tolist()

    iterations = length[0] + 1

    
    if event == sg.WIN_CLOSED or event == 'EXIT':
        sg.popup('Cancelled')
        break
    if event == 'IMPORT TEMPLATE':
        idft = IDF(fname1)
        idft.saveas(str(testingFile))
        sg.popup('Template Loaded')
    if event == 'IMPORT':
        #import the information needed from the orignal IDF file
        idf1 = IDF(str(testingFile))
        windowNames = []
        runs = [*range(1,iterations,1)]
        count = -1

        for zone in idfg.idfobjects['Zone']:
            idf1.copyidfobject(zone)

        for srf in idfg.idfobjects['BuildingSurface:Detailed']:
            idf1.copyidfobject(srf)

        for fen in idfg.idfobjects['FenestrationSurface:Detailed']:
            idf1.copyidfobject(fen)
            count += 1
            windows = idf1.idfobjects['FenestrationSurface:Detailed'][count]
            if windows.Surface_Type == 'Window':
                windowNames.append(windows.Name)
        
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
        Schedule_Name = 'Shading Availible',
        Setpoint = 100,
        Shading_Control_Is_Scheduled = 'Yes',
        Glare_Control_Is_Active = 'No',
        Shading_Device_Material_Name = 'HIGH REFLECT - LOW TRANS SHADE',
        Type_of_Slat_Angle_Control_for_Blinds = 'FixedSlatAngle',
        Multiple_Surface_Control_Type = 'Sequential',
        **values)

        for site in idfg.idfobjects['Shading:Site:Detailed']:
            idf1.copyidfobject(site)

        for bldg in idfg.idfobjects['Shading:Building:Detailed']:
            idf1.copyidfobject(bldg)

        #import sizing data

        for bldg in ddy.idfobjects['Site:Location']:
            idf1.copyidfobject(bldg)
            
        for bldg in ddy.idfobjects['SizingPeriod:DesignDay']:
            idf1.copyidfobject(bldg)

        idf1.saveas(str(testingFile))
        print(windowNames)

        sg.popup('Finished Import')
        #break
    if event =='CREATE':
        idf1 = IDF(str(testingFile))
        runs = [*range(1,iterations,1)]
        
        #Add basic inputs
        people = idf1.idfobjects['People'][0]
        people.Number_of_People = occ
        zone = idf1.idfobjects['Zone'][0]
        zone.Floor_Area = icfa
        FurnitureMass = idf1.idfobjects['InternalMass'][0]
        FurnitureMass.Surface_Area = icfa
        PartitionMass = idf1.idfobjects['InternalMass'][1]
        PartitionMass.Surface_Area = (icfa * PartitionRatio)
        
        #add parametrics to idf file
        runs = df['WindowConstruction']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$WindowConstruction',
        **values)

        runs = df['ExteriorWall']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$ExteriorWall',
        **values)

        runs = df['SHGC']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$SHGC',
        **values)

        runs = df['ERVSensibleRecovery']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$ERVSense',
        **values)

        runs = df['FloorConstruction']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$FloorConstruction',
        **values)

        runs = df['RoofConstruction']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$RoofConstruction',
        **values)

        runs = df['FlowCoefficient']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$Infiltration',
        **values)

        runs = df['ervSchedule']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$ERVSch',
        **values)

        runs = df['NatVentAvail']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$NV',
        **values)

        runs = df['NatVentAvail']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$SNV',
        **values)

        runs = df['NatVentType']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$NatVentType',
        **values)

        runs = df['ShadingAvailible']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$Shading',
        **values)

        runs = df['EvapCoolerAvail']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$ECSch',
        **values)

        runs = df['HeatPumpAvail']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$HPSch',
        **values)

        runs = df['DehumidifierAvail']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$DXDHSch',
        **values)

        runs = df['RunName']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$Name',
        **values)

        runs = df['StemWall']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$StemWall',
        **values)

        runs = df['OutStartH']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$OutStartH',
        **values)

        runs = df['OutStartC']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$OutStartC',
        **values)

        runs = df['OutEndH']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$OutEndH',
        **values)

        runs = df['OutEndC']
        params = [x for x in runs]
        values = {}
        for i,param in enumerate(params):
            values['Value_for_Run_' + str(i+1)] = param
        idf1.newidfobject('Parametric:SetValueForRun',
        Name = '$OutEndC',
        **values)

        idf1.saveas(str(testingFile))
        sg.popup('Finished Create')
        #break
    if event =='COLLECT':
        idf1 = IDF(str(testingFile))
        results = []
        runs = range(iterations-1)
        dft = dict()
        df1 = pd.DataFrame()

        for n in runs:
            name = (str(studyFolder) + "/" + str(BaseFileName) + "-" + str(n+1).rjust(6, '0') + ".csv")
            name2 = str(CaseName[n])
            results.append(name)
            dft[n] = pd.read_csv(results[n])
            df1["Date/Time"] = dft[n]["Date/Time"]
            df1[str(name2) + "Zone Air Temp"] = dft[n]["ZONE 1:Zone Air Temperature [F](Hourly)"]
            df1[str(name2) + "Zone RH"] = dft[n]['ZONE 1:Zone Air Relative Humidity [%](Hourly)']
            df1["Site Dry Bulb [F]"] = dft[n]['Environment:Site Outdoor Air Drybulb Temperature [F](Hourly)']
            df1[str(name2) + "Site Purchased Electricity [kWh]"] = dft[n]['ElectricityPurchased:Facility [kWh](Hourly)']

        #Plot Heating Outage

        df1.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
        df1[['Date2','Time']] = df1.DateTime.str.split(expand=True)
        df1['Date'] = df1['Date2'].map(str) + '/' + str(2020)
        df1['Time'] = (pd.to_numeric(df1['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + df1['Time'].str[2:]
        df1['DateTime'] = df1['Date'] + ' ' + df1['Time']
        df1['DateTime'] = pd.to_datetime(df1['DateTime'])

        endWarmup = int((df1[df1['DateTime'] == '2020-01-01 00:00:00'].index.values))
        dropWarmup = [*range(0, endWarmup,1)]

        df1 = df1.drop(index = dropWarmup)
        df1 = df1.reset_index()
        #=============================================================================================

        mask = (df1['DateTime'] >= start_date) & (df1['DateTime'] <= end_date)

        dfh = df1.loc[mask]

        x = dfh['DateTime']
        heatingBattery = []
        db = dict()
        rh = dict()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, sharey=True,constrained_layout=False)
        fig.suptitle((str(BaseFileName) + '_Heating Outage Resilience'), fontsize='x-large')

        for n in runs:
            db[n] = dfh[str(CaseName[n-1]) + "Zone Air Temp"]
            rh[n] = dfh[str(CaseName[n-1])+ "Zone RH"]
            heatingBattery.append(sum(dfh[str(CaseName[n-1])+ "Site Purchased Electricity [kWh]"]))
            if CaseName[n-1].__contains__("Phius"):
                ax1.plot(x,db[n], label=(str(CaseName[n-1]) + "_Zone Air Temp"), linestyle='dashdot')
                ax2.plot(x,rh[n], label=(str(CaseName[n-1]) + "_Zone RH"), linestyle='dashdot')
            else:
                ax1.plot(x,db[n], label=(str(CaseName[n-1]) + "_Zone Air Temp"))
                ax2.plot(x,rh[n], label=(str(CaseName[n-1]) + "_Zone RH"))

        #Plot site temp    
        ax1.plot(x,dfh["Site Dry Bulb [F]"], label="Site Dry Bulb [F]", linestyle='dashed')

        #fig.subplots_adjust(bottom=0.1)
        ax1.set_ylabel('Temperature [F]')
        ax1.legend(ncol=2, loc='lower left', borderaxespad=0, title = 'Case:', fontsize='xx-small')
        ax1.grid(True)

        ax2.set_xlabel('Date')
        ax2.set_ylabel('Relative Humidity [%]')
        ax2.legend(ncol=2, loc='lower left', borderaxespad=0, title = 'Case:', fontsize='xx-small')
        ax2.grid(True)

        plt.savefig(str(studyFolder) + "/" + str(BaseFileName) + "_Heating Outage Resilience Graphs.png", dpi=300)

        #Plot Cooling Outage
        mask = (df1['DateTime'] >= start_date2) & (df1['DateTime'] <= end_date2)

        dfh = df1.loc[mask]

        x = dfh['DateTime']
        db = dict()
        rh = dict()
        coolingBattery = []

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9))
        fig.suptitle(str(BaseFileName) + '_Cooling Outage Resilience', fontsize='x-large')

        for n in runs:
            db[n] = dfh[str(CaseName[n-1]) + "Zone Air Temp"]
            rh[n] = dfh[str(CaseName[n-1]) + "Zone RH"]
            coolingBattery.append(sum(dfh[str(CaseName[n-1])+ "Site Purchased Electricity [kWh]"]))
        #plot zone results
            if CaseName[n-1].__contains__("Phius"):
                ax1.plot(x,db[n], label=(str(CaseName[n-1]) + "_Zone Air Temp"), linestyle='dashdot')
                ax2.plot(x,rh[n], label=(str(CaseName[n-1]) + "_Zone RH"), linestyle='dashdot')
            else:
                ax1.plot(x,db[n], label=(str(CaseName[n-1]) + "_Zone Air Temp"))
                ax2.plot(x,rh[n], label=(str(CaseName[n-1]) + "_Zone RH"))
        #Plot site temp    
        ax1.plot(x,dfh["Site Dry Bulb [F]"], label="Site Dry Bulb [F]", linestyle='dashed')

        ax1.set_ylabel('Temperature [F]')
        ax1.legend(ncol=2, loc='lower left', borderaxespad=0, title = 'Case:', fontsize='xx-small')
        ax1.grid(True)

        ax2.set_xlabel('Date')
        ax2.set_ylabel('Relative Humidity [%]')
        ax2.legend(ncol=2, loc='lower left', borderaxespad=0, title = 'Case:', fontsize='xx-small')
        ax2.grid(True)

        plt.savefig(str(studyFolder) + "/" + str(BaseFileName) + "_Cooling Outage Resilience Graphs.png", dpi=300)
        
        ## Start results table
        results = []
        HeatingSET = []
        Caution = []
        ExtremeCaution = []
        Danger = []
        ExtremeDanger = []
        Below2C = []

        for n in runs:
            fname = (str(studyFolder)+ "/" + str(BaseFileName) + "-" + str(n+1).rjust(6, '0') + "Table.html")
            results.append(fname)
            filehandle = open(fname, 'r').read()

            htables = readhtml.titletable(filehandle) # reads the tables with their titles

            SETh = htables[178]
            item_title = SETh[0]
            item_table = SETh[1]
            row = item_table[1] # we start counting with 0. So 0, 1, 2 is third row
            value = row[1]
            HeatingSET.append(float(value))

            Caut = htables[174]
            item_title = Caut[0]
            item_table = Caut[1]
            row = item_table[1] # we start counting with 0. So 0, 1, 2 is third row
            value = row[2]
            Caution.append(float(value))

            ExCaut = htables[174]
            item_title = ExCaut[0]
            item_table = ExCaut[1]
            row = item_table[1] # we start counting with 0. So 0, 1, 2 is third row
            value = row[3]
            ExtremeCaution.append(float(value))

            Dang = htables[174]
            item_title = Dang[0]
            item_table = Dang[1]
            row = item_table[1] # we start counting with 0. So 0, 1, 2 is third row
            value = row[4]
            Danger.append(float(value))

            ExDang = htables[174]
            item_title = ExDang[0]
            item_table = ExDang[1]
            row = item_table[1] # we start counting with 0. So 0, 1, 2 is third row
            value = row[5]
            ExtremeDanger.append(float(value))

            Freeze = htables[184]
            item_title = Freeze[0]
            item_table = Freeze[1]
            row = item_table[39] # we start counting with 0. So 0, 1, 2 is third row
            value = row[2]
            Below2C.append(float(value))

            window['-PROG-'].update(n)

        ResultsTable = pd.DataFrame()
        ResultsTable["Run Name"] = RunNames["RunName"]
        ResultsTable["SET ≤ 12.2°C Hours (F)"] = HeatingSET
        ResultsTable["Hours < 2°C [hr]"] = Below2C
        ResultsTable["Caution (> 26.7, ≤ 32.2°C) [hr]"] = Caution
        ResultsTable["Extreme Caution (> 32.2, ≤ 39.4°C) [hr]"] = ExtremeCaution
        ResultsTable["Danger (> 39.4, ≤ 51.7°C) [hr]"] = Danger
        ResultsTable["Extreme Danger (> 51.7°C) [hr]"] = ExtremeDanger
        ResultsTable["Heating Battery [kWh]"] = heatingBattery
        ResultsTable["Cooling Battery [kWh]"] = coolingBattery

        ResultsTable.to_csv(str(studyFolder) + "/" + str(BaseFileName) + "_ResultsTable.csv")
        """
        #Plot Cooling Outage
        x = ResultsTable['Run Name']
        db = dict()
        rh = dict()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 15))
        fig.suptitle('Single Point Metrics')

        for n in runs:
            db[n] = dfh[str(CaseName[n-1]) + "Zone Air Temp"]
            rh[n] = dfh[str(CaseName[n-1]) + "Zone RH"]
        #plot zone results
            ax1.plot(x,db[n], label=(str(CaseName[n-1]) + "_Zone Air Temp"))
            ax2.plot(x,rh[n], label=(str(CaseName[n-1]) + "_Zone RH"))
        #Plot site temp    
        ax1.plot(x,dfh["Site Dry Bulb [F]"], label="Site Dry Bulb [F]", linestyle='dashed')

        ax1.set_ylabel('Temperature [F]')
        ax1.legend()
        ax1.grid(True)

        ax2.set_xlabel('Date')
        ax2.set_ylabel('Relative Humidity [%]')
        ax2.legend()
        ax2.grid(True)

        plt.savefig(str(studyFolder) + "/" + str(BaseFileName) + "_Results Graphs.png")

        """
        #=================================================== constructions database
        constructions = idf1.idfobjects["CONSTRUCTION"]
        cdd = pd.DataFrame()
        cdd['Constructions'] = [construction.Name for construction in constructions]
        cdd['Outside Layer'] = [construction.Outside_Layer for construction in constructions]
        cdd['Layer 2'] = [construction.Layer_2 for construction in constructions]
        cdd['Layer 3'] = [construction.Layer_3 for construction in constructions]
        cdd['Layer 4'] = [construction.Layer_4 for construction in constructions]
        cdd['Layer 5'] = [construction.Layer_5 for construction in constructions]
        cdd['Layer 6'] = [construction.Layer_6 for construction in constructions]
        cdd['Layer 7'] = [construction.Layer_7 for construction in constructions]

        cdd.to_csv(str(studyFolder) + "/" + 'Construction_Data_Dictionary.csv')

        sg.popup('Finished Collect')
        #break
