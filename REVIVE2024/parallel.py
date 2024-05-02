import asyncio
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
from joblib import Parallel, delayed
# import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
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


os.chdir('C:\REVIVE v24.1.0\MF\MF Results')
iddfile  = 'C:\EnergyPlusV9-5-0\Energy+.idd'
epwFile = 'USA_IL_Chicago-Midway.AP.725340_TMY3.epw'
IDF.setiddname(iddfile)

files = os.listdir()
runs = []
for file in files:
    if file.endswith('idf'):
        runs.append(str(file))

# print(runs)
# for run in runs:
#     idf = IDF(str(run), str(epwFile))
#     idf.run(readvars=True)


def simulation(run):
    IDF.setiddname(iddfile)
    idf = IDF(str(run), str(epwFile))
    idf.run(readvars=True,output_prefix=str(run))

Parallel(n_jobs=4)(delayed(simulation)(run) for run in runs)
