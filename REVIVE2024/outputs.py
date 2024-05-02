# This file contains functions for building envelope building
# Updated 2023.08.23

from pickle import TRUE
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
import email.utils as eutils
import time
import math
# import streamlit as st
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system
from pylatex import *

from pylatex import Document, PageStyle, Head, MiniPage, Foot, LargeText, \
    MediumText, LineBreak, simple_page_number
from pylatex.utils import bold
from pylatex import Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat
from pylatex.utils import italic


def SimulationOutputs(idf):

    idf.newidfobject('Output:VariableDictionary',
        Key_Field = 'IDF')

    idf.newidfobject('Output:Table:SummaryReports',
        Report_1_Name = 'AllSummary')

    idf.newidfobject('Output:Table:TimeBins',
        Key_Value = '*',
        Variable_Name = 'Zone Air Temperature',
        Interval_Start = -40,
        Interval_Size = 42,
        Interval_Count = 1,
        Variable_Type = 'Temperature'
        )

    idf.newidfobject('OutputControl:Table:Style',
        Column_Separator = 'HTML',
        Unit_Conversion = 'InchPound'
        )

    idf.newidfobject('Output:SQLite',
        Option_Type = 'SimpleAndTabular',
        Unit_Conversion_for_Tabular_Data = 'InchPound'
        )

    outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature', 'Exterior Lights Electricity Energy', 
                'Zone Ventilation Mass Flow Rate', 'Schedule Value', 'Electric Equipment Electricity Energy',
                'Facility Total Purchased Electricity Energy', 'Zone Heat Index', 'Zone Thermal Comfort Pierce Model Standard Effective Temperature', 'Site Outdoor Air Relative Humidity',
                'Site Outdoor Air Dewpoint Temperature', 'Zone Mean Air Dewpoint Temperature','Facility Total Surplus Electricity Energy']
    meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity', 'ElectricityNet:Facility',
                'NaturalGas:Facility'] 
    for x in outputVars:
        idf.newidfobject('Output:Variable',
        Key_Value = '*',
        Variable_Name = str(x),
        Reporting_Frequency = 'hourly'
        )

    for x in meterVars:
        idf.newidfobject('Output:Meter:MeterFileOnly',
        Key_Name = str(x),
        Reporting_Frequency = 'Monthly'
        )

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
        doc.append('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Elit sed vulputate mi sit amet mauris. Eu feugiat pretium nibh ipsum consequat nisl vel pretium lectus. Viverra maecenas accumsan lacus vel facilisis volutpat est velit. Pellentesque nec nam aliquam sem et tortor. Pellentesque diam volutpat commodo sed egestas egestas fringilla phasellus. Malesuada fames ac turpis egestas. Turpis in eu mi bibendum neque egestas. Ac auctor augue mauris augue neque gravida in fermentum et. Et tortor at risus viverra adipiscing at in. Quis viverra nibh cras pulvinar mattis nunc sed. Ac orci phasellus egestas tellus rutrum tellus pellentesque. Adipiscing enim eu turpis egestas pretium. Proin sed libero enim sed faucibus turpis in eu mi.')
        doc.append('Ullamcorper eget nulla facilisi etiam dignissim diam. Enim neque volutpat ac tincidunt vitae semper quis. Amet est placerat in egestas. Sapien et ligula ullamcorper malesuada proin libero nunc consequat interdum. Ultrices gravida dictum fusce ut placerat orci. Lorem ipsum dolor sit amet. Ut pharetra sit amet aliquam id. Scelerisque felis imperdiet proin fermentum leo. Urna duis convallis convallis tellus. Lectus vestibulum mattis ullamcorper velit sed ullamcorper morbi tincidunt ornare. Tortor at auctor urna nunc id cursus. Donec adipiscing tristique risus nec feugiat in fermentum posuere. Feugiat nisl pretium fusce id velit. Et egestas quis ipsum suspendisse ultrices gravida. Condimentum id venenatis a condimentum vitae sapien pellentesque habitant morbi. Auctor eu augue ut lectus arcu bibendum at varius vel. Tellus at urna condimentum mattis pellentesque id nibh tortor. Aliquet risus feugiat in ante metus. Sit amet nisl purus in. Velit laoreet id donec ultrices tincidunt arcu non.')
        # doc.append(italic('italic text. '))
        # doc.append('\nAlso some crazy characters: $&#{}')
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
                table.add_row(['Heating Battery Size', round(heatingBattery,2), 'kWh'])
                table.add_row(['Cooling Battery Size', round(coolingBattery,2), 'kWh'])
                table.add_hline()

    with doc.create(Subsection('Adorb Single Point Metrics')): 
        with doc.create(Tabular('l|l|l')) as table:
                table.add_hline()
                table.add_row(['Metric','Result','Unit'])
                table.add_hline()
                table.add_row(['Energy Use Intensity', round(eui,2),'kBtu/ sf yr'])
                table.add_row(['Peak Electrical Load', round(peakElec),'W'])
                table.add_hline()
                table.add_row(['First Year Electric Cost', round(annualElec),'$'])
                table.add_row(['First Cost', round(firstCost),'$'])
                table.add_row(['Total ADORB Cost', round(adorbCost),'$'])
                table.add_hline()
    
    with doc.create(Section('Graph Results')):
        doc.append('Some regular text and some')

    doc.append(NewPage())
    with doc.create(Subsection('Resilience Graph Results')):
        with doc.create(Figure(position='ht')) as heatingOutageGraph:
            heatingOutageGraph.add_image(str(heatingGraphFile), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

        with doc.create(Figure(position='ht')) as coolingOutageGraph:
            coolingOutageGraph.add_image(str(coolingGraphFile), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

    doc.append(NewPage())
    with doc.create(Subsection('Adorb Graph Results')):
        with doc.create(Figure(position='ht')) as adorbWedge:
            adorbWedge.add_image(str(adorbWedgeGraph), width='6in')
            # coolingOutageGraph.add_caption('Look it\'s on its back')

        if os.path.exists(adorbBarGraph):
            with doc.create(Figure(position='ht')) as adorbBar:
                adorbBar.add_image(str(adorbBarGraph), width='6in')
                # coolingOutageGraph.add_caption('Look it\'s on its back')

    

    docname = os.path.join(studyFolder, caseName + "_Summary Report")
    doc.generate_pdf(docname, silent=True, clean_tex=False)


