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
from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system
from pylatex import *

import pprint
pp = pprint.PrettyPrinter()

from pylatex import Document, PageStyle, Head, MiniPage, Foot, LargeText, \
    MediumText, LineBreak, simple_page_number
from pylatex.utils import bold
from pylatex import Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat
from pylatex.utils import italic



        
eui = 34.5
peakElec = 543
heatingBattery = 5
coolingBattery = 6

caseName = 'Pizza Hut'
HeatingSET =56.4
Below2C = 2
Caution = 4
ExtremeCaution = 89
Danger = 453
ExtremeDanger = 858383

annualElec = 1505.02
annualGas = 3504
firstCost = 543254 
adorbCost = 572343

heatingGraphFile = 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29/Name your batch of files_Montreal_Package_0_BASE House_Elec_Heating Outage Resilience Graphs.png'
coolingGraphFile = 'C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29/Name your batch of files_Montreal_Package_0_BASE House_Elec_Heating Outage Resilience Graphs.png'

adorbWedgeGraph = "C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29/Name your batch of files_Montreal_Package_3_IECC_Elec_ADORB_Wedge.png"
adorbBarGraph = "C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29/Name your batch of files_Montreal_Package_3B_IECC+0.04_Elec_ADORB_Bar.png"
studyFolder = "C:/Users/amitc_crl/OneDrive/Documents/GitHub/REVIVE/REVIVE2024/Testing Files/Testing_2023-08-29"

def PDF_Report(caseName, studyFolder, HeatingSET, Below2C, Caution, ExtremeCaution, Danger, ExtremeDanger, 
                    heatingBattery, coolingBattery, eui, peakElec, annualElec, annualGas,
                    firstCost, adorbCost, heatingGraphFile, coolingGraphFile, adorbWedgeGraph,
                    adorbBarGraph):
    today = datetime.now()
    todayStamp = (str(today.month)+'/'+str(today.day)+'/'+str(today.year))

    geometry_options = {"margin": "1in"}
    doc = Document(geometry_options=geometry_options)
    # Add document header
    header = PageStyle("header")
    # Create left header
    with header.create(Head("L")):
        header.append("Report date: " + str(todayStamp))
        header.append(LineBreak())
    # Create center header
    with header.create(Head("C")):
        header.append("Phius")
    # Create right header
    with header.create(Head("R")):
        header.append(simple_page_number())


    doc.preamble.append(header)
    doc.change_document_style("header")

    # Add Heading
    with doc.create(MiniPage(align='c')):
        doc.append(LargeText(bold("REVIVE 2024 Report")))
        doc.append(LineBreak())
        doc.append(MediumText(("Resilience and ADORB Summary")))
        doc.append(LineBreak())
        doc.append(LineBreak())
        doc.append(MediumText(bold(str(caseName))))

    with doc.create(Section('Introduction')):
        doc.append('Some regular text and some')
        doc.append(italic('italic text. '))
        doc.append('\nAlso some crazy characters: $&#{}')
    with doc.create(Subsection('Math that is incorrect')):
            doc.append(Math(data=['2*3', '=', 9]))

    with doc.create(Section('Tables')):
        doc.append('Tables for thermal resilience and ADORB Costs')

    with doc.create(Subsection('Resilience Single Point Metrics')): 
        with doc.create(Tabular('l|l|l')) as table:
                table.add_hline()
                table.add_row(['Metric','Result','Unit'])
                table.add_hline()
                table.add_row(['Heating SET Hours',HeatingSET,'°F hr'])
                table.add_row(['Hours Below 2°C',Below2C,'hr'])
                table.add_hline()
                table.add_row(['Caution (> 26.7, < 32.2°C)', Caution, 'hr'])
                table.add_row(['Extreme Caution (> 32.2, < 39.4°C)', ExtremeCaution, 'hr'])
                table.add_row(['Danger (> 39.4, < 51.7°C)', Danger, 'hr'])
                table.add_row(['Extreme Danger (> 51.7°C)', ExtremeDanger, 'hr'])
                table.add_hline()
                table.add_row(['Heating Battery Size', heatingBattery, 'kWh'])
                table.add_row(['Cooling Battery Size', coolingBattery, 'kWh'])
                table.add_hline()

    with doc.create(Subsection('Adorb Single Point Metrics')): 
        with doc.create(Tabular('l|l|l')) as table:
                table.add_hline()
                table.add_row(['Metric','Result','Unit'])
                table.add_hline()
                table.add_row(['Energy Use Intensity', eui,'kBtu/ sf yr'])
                table.add_row(['Peak Electrical Load', peakElec,'W'])
                table.add_hline()
                table.add_row(['First Year Electric Cost', annualElec,'$'])
                table.add_row(['First Cost', firstCost,'$'])
                table.add_row(['Total ADORB Cost', adorbCost,'$'])
                table.add_hline()
    
    with doc.create(Section('Graph Results')):
        doc.append('Some regular text and some')

    with doc.create(Subsection('Resilience Graph Results')):
        with doc.create(Figure(position='ht')) as heatingOutageGraph:
            heatingOutageGraph.add_image(str(heatingGraphFile), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

        with doc.create(Figure(position='ht')) as coolingOutageGraph:
            coolingOutageGraph.add_image(str(coolingGraphFile), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

    with doc.create(Subsection('Adorb Graph Results')):
        with doc.create(Figure(position='ht')) as adorbWedge:
            adorbWedge.add_image(str(adorbWedgeGraph), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

        if os.path.exists(adorbBarGraph):
            with doc.create(Figure(position='ht')) as adorbBar:
                adorbBar.add_image(str(adorbBarGraph), width='6in')
                # coolingOutageGraph.add_caption('Look it\'s on its back')

    

    docname = (str(studyFolder) + "/" + str(caseName) + "_Summary Report")
    doc.generate_pdf(docname, silent=True, clean_tex=False)



PDF_Report(caseName, studyFolder, HeatingSET, Below2C, Caution, ExtremeCaution, Danger, ExtremeDanger, 
                    heatingBattery, coolingBattery, eui, peakElec, annualElec, annualGas,
                    firstCost, adorbCost, heatingGraphFile, coolingGraphFile, adorbWedgeGraph,
                    adorbBarGraph)