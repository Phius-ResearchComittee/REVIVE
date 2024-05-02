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
from eppy.runner.run_functions import runIDFs
# from PIL import Image, ImageTk
import os
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import subprocess
import os
from os import system
import os
import shutil
import fnmatch
import glob

def adorb(BaseFileName, studyFolder, duration, annualElec, annualGas, annualCO2Elec, annualCO2Gas, dirMR, emCO2, eTrans, graphs):
    results = pd.DataFrame(columns=['pv_dirEn', 'pv_opCO2', 'pv_dirMR', 'pv_emCO2', 'pv_eTrans'])
    years = range(duration)
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
        c_opCarb = (annualCO2Elec[i] + annualCO2Gas) * pc
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
        newRow = pd.Series({'pv_dirEn':pv_dirEn, 'pv_opCO2':pv_opCO2, 'pv_dirMR':pv_dirMR, 'pv_emCO2':pv_emCO2, 'pv_eTrans':pv_eTrans})
        results = pd.concat([results, newRow.to_frame().T], ignore_index=True)
    results.to_csv(str(BaseFileName) + '_ADORBresults.csv')

    df = results

    df2 = pd.DataFrame()
    df2['pv_dirEn'] = df['pv_dirEn'].cumsum()
    df2['pv_dirMR'] = df['pv_dirMR'].cumsum()
    df2['pv_opCO2'] = df['pv_opCO2'].cumsum()
    df2['pv_emCO2'] = df['pv_emCO2'].cumsum()
    df2['pv_eTrans'] = df['pv_eTrans'].cumsum()

    # df2.plot(kind='area', xlabel='Years', ylabel='Cummulative Present Value [$]', title='ADORB COST', figsize=(6.5,8.5))


    pv_dirEn_tot = df['pv_dirEn'].sum()
    pv_dirMR_tot = df['pv_dirMR'].sum()
    pv_opCO2_tot = df['pv_opCO2'].sum()
    pv_emCO2_tot = df['pv_emCO2'].sum()
    pv_eTrans_tot = df['pv_eTrans'].sum()

    if 'BASE' not in BaseFileName:
        for filename in os.listdir(studyFolder):
            if filename.endswith('.csv'):
                if 'BASE' in str(filename):
                    if 'ADORB' in str(filename):
                        basedf = pd.read_csv(filename)

                        pv_dirEn_tot_base = basedf['pv_dirEn'].sum()
                        pv_dirMR_tot_base = basedf['pv_dirMR'].sum()
                        pv_opCO2_tot_base = basedf['pv_opCO2'].sum()
                        pv_emCO2_tot_base = basedf['pv_emCO2'].sum()
                        pv_eTrans_tot_base = basedf['pv_eTrans'].sum()

                        case = ('Base Case','Proposed')
                        case_data = {
                            "Direct Energy": np.array([pv_dirEn_tot_base,pv_dirEn_tot]),
                            "Direct Maintenance": np.array([pv_dirMR_tot_base,pv_dirMR_tot]),
                            "Operational CO2": np.array([pv_opCO2_tot_base,pv_opCO2_tot]),
                            "Embodied CO2": np.array([pv_emCO2_tot_base,pv_emCO2_tot]),
                            "Energy Transition": np.array([pv_eTrans_tot_base,pv_eTrans_tot]),
                        }
                        width = 0.3  # the width of the bars: can also be len(x) sequence

                        if graphs == True:
                            fig, ax = plt.subplots(figsize=(10,6))
                            left = np.zeros(2)

                            for sex, sex_count in case_data.items():
                                # p = ax.bar(case, sex_count, width, label=sex, bottom=bottom)
                                y = ax.barh(case,sex_count,width,label=sex,left=left)
                                left += sex_count

                                ax.bar_label(y, label_type='center',rotation=-45)

                            ax.set_title('Total Lifecycle ADORB Cost')
                            ax.legend(loc="upper right")
                            ax.set_xlabel('Cost [$]')
                            plt.savefig(str(adorb.adorbBarGraph),dpi=300)
                            plt.clf()
    try:
        if graphs == True:
            fig = df2.plot(kind='area', xlabel='Years', ylabel='Cummulative Present Value [$]', title=(str(BaseFileName) + '_ADORB COST'), figsize=(10,6)).get_figure()

            adorb.adorbWedgeGraph = os.path.join(studyFolder, BaseFileName + '_ADORB_Wedge.png')
            adorb.adorbBarGraph = os.path.join(studyFolder, BaseFileName + '_ADORB_Bar.png')
            fig.savefig(adorb.adorbWedgeGraph)

    except:
        print('No Graph')

    return sum(pv), pv_dirEn_tot, pv_dirMR_tot, pv_opCO2_tot, pv_emCO2_tot,pv_eTrans_tot

        # PV_i = sum over y from 1 to N of C_i_y / (1+k_i^y) , where
        # C_i  is the Cost, of cost component i [$].
        # k_i is the discount rate for cost component i [fraction 0 to 1].
        # k_dirEnr = 0.02
        # k_opCarb = 0
        # k_dirMR = 0.02
        # k_emCarb = 0
        # y is the year, counting from the current year = 1, that is, the future calendar year minus the previous calendar year.

def multiphaseADORB(year1Path,year1Start,year2Path,year2Start,year3Path,year3Start):

    duration0 = []
    duration1 = []
    duration2 = []
    duration3 = []

    year1 = ''
    year2 = ''
    year3 = ''

    if year1Path:
        year1 = pd.read_csv(str(year1Path))
        year1FirstCost = year1['pv_dirMR'][1]
        year1EC = year1['pv_emCO2'][1]
        duration0 = [*range(0,year1Start)]
        duration1 = [*range(year1Start,year2Start)]
    if year2Path:
        year2 = pd.read_csv(str(year2Path))
        year2FirstCost = year2['pv_dirMR'][1]
        year2EC = year2['pv_emCO2'][1]
        if year3Path:
            duration2 = [*range(year2Start,year3Start)]
        else:
            duration2 = [*range(year2Start,70)]
    if year3Path:
        year3 = pd.read_csv(str(year3Path))
        year3FirstCost = year3['pv_dirMR'][1]
        year3EC = year3['pv_emCO2'][1]
        duration3 = [*range(year3Start,70)]


    if year1Path:
        year1 = year1.drop(index=(duration0 + duration2 + duration3))
    if year2Path:
        year2 = year2.drop(index=(duration0 + duration1 + duration3))
    if year3Path:
        year3 = year3.drop(index=(duration0 + duration1 + duration2))


    if year3Path:
        final = pd.concat([year1,year2,year3],ignore_index=False)
        final.at[year2Start, 'pv_dirMR'] = (year2FirstCost-year1FirstCost)/((1+0.02)**year2Start)
        final.at[year3Start, 'pv_dirMR'] = (year3FirstCost-year2FirstCost-year1FirstCost)/((1+0.02)**year3Start)
        final.at[year2Start, 'pv_emCO2'] = (year2EC-year1EC)
        final.at[year3Start, 'pv_emCO2'] = (year3EC-year2EC-year1EC)
    else:
        final = pd.concat([year1,year2],ignore_index=False)
        final.at[year2Start, 'pv_dirMR'] = (year2FirstCost-year1FirstCost)/((1+0.02)**year2Start)
        final.at[year2Start, 'pv_emCO2']= (year2EC-year1EC)

    adorbComp = final[['pv_dirEn','pv_dirMR','pv_eTrans','pv_emCO2','pv_opCO2']].sum()
    adorbTotal = sum(adorbComp)

    print("Analysis Complete")