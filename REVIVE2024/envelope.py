# This file contains functions for building envelope building
# Updated 2023.08.23

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
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system



# This function builds E+ contstructions from different layers: 
def constructionBuilder(idf, constructionName, constructionLayers):
    params = [x for x in constructionLayers]
    layers = {}
    count = 0
    for i,param in enumerate(params):
        count = count + 1
        layers['Layer_' + str(count)] = param

    layers.pop('Layer_1')
    idf.newidfobject('Construction',
    Name = str(constructionName),
    Outside_Layer = str(constructionLayers[0]),
    **layers)

# This function builds out custom materials and base materials in the file:
def materialBuilder(idf, name, rough, thick, conduct, dense, heatCap):
    idf.newidfobject('Material',
        Name = str(name),
        Roughness = str(rough),
        Thickness = thick,
        Conductivity = conduct,
        Density = dense,
        Specific_Heat = heatCap
        )

# This function creates line item costs
def costBuilder(idf, name, type, lineItemType, itemName, objEndUse, costEach, costArea,quantity):
    idf.newidfobject('ComponentCost:LineItem',
        Name = name,
        Type = type,
        Line_Item_Type = lineItemType,
        Item_Name = itemName,
        Object_EndUse_Key = objEndUse,
        Cost_per_Each = costEach,
        Cost_per_Area = costArea,
        Quantity = quantity
        )
    
def glazingBuilder(idf, name, uFactor, shgc):
    idf.newidfobject('WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
        Name = name,
        UFactor = uFactor,
        Solar_Heat_Gain_Coefficient = shgc
        )

def Infiltration(idf, flowCoefficient):
    
    idf.newidfobject('ZoneInfiltration:FlowCoefficient',
        Name = 'Zone_Infiltration',
        Zone_Name = 'Zone 1',
        Schedule_Name = 'Always_On',
        Flow_Coefficient = flowCoefficient,
        Stack_Coefficient = 0.078,
        Wind_Coefficient = 0.17,
        Shelter_Factor = 0.9
        )

def SpecialMaterials(idf):

    idf.newidfobject('Material:AirGap',
        Name = 'F04 Wall air space resistance',
        Thermal_Resistance = 0.15
        )

    idf.newidfobject('Material:AirGap',
        Name = 'F05 Ceiling air space resistance',
        Thermal_Resistance = 0.18
        )

# def WindowMaterials(idf, Ext_Window1_Ufactor,Ext_Window1_SHGC):

#     idf.newidfobject('WindowMaterial:SimpleGlazingSystem',
#         Name = 'ExteriorWindow1',
#         UFactor = (Ext_Window1_Ufactor*5.678),
#         Solar_Heat_Gain_Coefficient = Ext_Window1_SHGC
#         )

#     idf.newidfobject('Construction',
#         Name = 'Ext_Window1',
#         Outside_Layer = 'ExteriorWindow1')
    
def ShadeMaterials(idf):

    idf.newidfobject('WindowMaterial:Shade',
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
    
    idf.newidfobject('WindowMaterial:Shade',
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

    idf.newidfobject('WindowMaterial:Shade',
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
    
def WindowVentilation(idf, halfHeight, operableArea_N, operableArea_W, 
                      operableArea_S, operableArea_E):

    idf.newidfobject('ZoneVentilation:WindandStackOpenArea',
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

    idf.newidfobject('ZoneVentilation:WindandStackOpenArea',
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

    idf.newidfobject('ZoneVentilation:WindandStackOpenArea',
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

    idf.newidfobject('ZoneVentilation:WindandStackOpenArea',
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
    
def WindowShadingControl(idf, windowNames):
    runs = windowNames
    params = [x for x in runs]
    values = {}
    for i,param in enumerate(params):
        values['Fenestration_Surface_' + str(i+1) + '_Name'] = param
    idf.newidfobject('WindowShadingControl',
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

def AssignContructions(idf, Ext_Wall1,Ext_Wall2,Ext_Wall3,
                       Ext_Roof1,Ext_Roof2,Ext_Roof3,
                       Ext_Floor1,Ext_Floor2,Ext_Floor3,
                       Ext_Door1,Ext_Door2,Ext_Door3, 
                       Int_Floor1,Int_Floor2,Int_Floor3,
                       Ext_Window1,Ext_Window2,Ext_Window3):

    count = -1
    for srf in idf.idfobjects['BuildingSurface:Detailed']:
        count += 1
        surface = idf.idfobjects['BuildingSurface:Detailed'][count]
        if surface.Construction_Name == 'Ext_Wall1':
            surface.Construction_Name = str(Ext_Wall1)
        if surface.Construction_Name == 'Ext_Roof1':
            surface.Construction_Name = str(Ext_Roof1)
        if surface.Construction_Name == 'Ext_Floor1':
            surface.Construction_Name = str(Ext_Floor1)
        if surface.Construction_Name == 'Ext_Wall2':
            surface.Construction_Name = str(Ext_Wall2)
        if surface.Construction_Name == 'Ext_Roof2':
            surface.Construction_Name = str(Ext_Roof2)
        if surface.Construction_Name == 'Ext_Floor2':
            surface.Construction_Name = str(Ext_Floor2)
        if surface.Construction_Name == 'Ext_Wall3':
            surface.Construction_Name = str(Ext_Wall3)
        if surface.Construction_Name == 'Ext_Roof3':
            surface.Construction_Name = str(Ext_Roof3)
        if surface.Construction_Name == 'Ext_Floor3':
            surface.Construction_Name = str(Ext_Floor3)
        if surface.Construction_Name == 'Ext_Door1':
            surface.Construction_Name = str(Ext_Door1)
        if surface.Construction_Name == 'Int_Floor1':
            surface.Construction_Name = str(Int_Floor1)
        if surface.Construction_Name == 'Ext_Door2':
            surface.Construction_Name = str(Ext_Door2)
        if surface.Construction_Name == 'Int_Floor2':
            surface.Construction_Name = str(Int_Floor2)
        if surface.Construction_Name == 'Ext_Door3':
            surface.Construction_Name = str(Ext_Door3)
        if surface.Construction_Name == 'Int_Floor3':
            surface.Construction_Name = str(Int_Floor3)

    count = -1
    for fen in idf.idfobjects['FenestrationSurface:Detailed']:
        count += 1
        window = idf.idfobjects['FenestrationSurface:Detailed'][count]
        if window.Construction_Name == 'Ext_Window1':
            window.Construction_Name = str(Ext_Window1)
            # window.Construction_Name = 'pizza'
        if window.Construction_Name == 'Ext_Window2':
            window.Construction_Name = str(Ext_Window2)
        if window.Construction_Name == 'Ext_Window3':
            window.Construction_Name = str(Ext_Window3)

def FoundationInterface(idf,foundationList):

    for row in foundationList:
        # if row[0] != '':
        fndType = str(row[0])
        fndIns = str(row[1])
        fndInsDepth = row[2]*0.3048
        fndPerim = row[3]*0.3048
        
        idf.newidfobject('Foundation:Kiva',
            # Name = ('Slab Details'),
            Name = (str(fndType) + ' Details'),
            # ,_________________________!-_Initial_Indoor_Air_Temperature
            # ,_________________________!-_Interior_Horizontal_Insulation_Material_Name
            # ,_________________________!-_Interior_Horizontal_Insulation_Depth
            # ,_________________________!-_Interior_Horizontal_Insulation_Width
            # ,_________________________!-_Interior_Vertical_Insulation_Material_Name
            # ,_________________________!-_Interior_Vertical_Insulation_Depth
            # ,_________________________!-_Exterior_Horizontal_Insulation_Material_Name
            # ,_________________________!-_Exterior_Horizontal_Insulation_Depth
            # ,_________________________!-_Exterior_Horizontal_Insulation_Width
            Exterior_Vertical_Insulation_Material_Name = str(fndIns),
            Exterior_Vertical_Insulation_Depth = fndInsDepth,
            # 0.1524,___________________!-_Wall_Height_Above_Grade
            # 1.0668,___________________!-_Wall_Depth_Below_Slab
            # ,_________________________!-_Footing_Wall_Construction_Name
            # M15_200mm_heavyweight_concrete,____!-_Footing_Material_Name
            Footing_Depth = 0.4
            )

        idf.newidfobject('SurfaceProperty:ExposedFoundationPerimeter',
            Surface_Name = str(fndType),
            Exposed_Perimeter_Calculation_Method = 'TotalExposedPerimeter',
            Total_Exposed_Perimeter = fndPerim
            # Exposed_Perimeter_Fraction = 1.0,
            # Surface_Segment_1_Exposed = 'Yes'
            )