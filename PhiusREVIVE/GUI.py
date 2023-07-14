from pickle import TRUE
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
import email.utils as eutils
import time
import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
import PySimpleGUI as sg
from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system

import pprint
pp = pprint.PrettyPrinter()

sg.theme('LightBlue2')

tab0_layout =  [[sg.Text('Welcome')],
                [sg.Text('Please follow the steps below to test thermal resilience of the house')],
                [sg.Text('0. Click IMPORT TEMPLATE to creat a new blank IDF from template')],
                [sg.Text('1. Click IMPORT to import geometry from the base IDF and design weather data from DDY')],
                [sg.Text('2. Click CREATE to create an IDF from CSV Run List')],
                [sg.Text('3. Run parametric IDF using EP-Launch')],
                [sg.Text('4. Click COLLECT to compile results')],
                ]

tab1_layout =   [[sg.Text('IDD File Location:', size =(15, 1)),sg.InputText("C:\EnergyPlusV9-5-0\Energy+.idd", key='iddFile'), sg.FileBrowse()],
                [sg.Text('Study Folder:', size =(15, 1)),sg.InputText('C:\\4StepResiliencev1-2', key='StudyFolder'), sg.FolderBrowse()],
                [sg.Text('Geometry IDF:', size =(15, 1)),sg.InputText('Select IDF with Geometry', key='GEO'), sg.FileBrowse()],
                [sg.Text('Run List Location:', size =(15, 1)),sg.InputText('C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/PhiusREVIVE/Testing/test3/runs.csv', key='runList'), sg.FileBrowse()]
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

window = sg.Window('Phius REVIVE 2024 Analysis Tool v0.1',layout1, default_element_size=(125, 125), grab_anywhere=True)   

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
        for i in range(1,10000):
            sg.one_line_progress_meter('Progress Meter', i+1, 10000, 'AnalysisRunning','Please wait while the analysis runs, results will be available after it is complete')
