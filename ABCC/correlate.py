import pandas as pd
import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
from eppy.results import readhtml # the eppy module with functions to read the html
from eppy.results import fasthtml
import datetime
from datetime import timedelta
import itertools
from itertools import product
import random
import os
import time
from joblib import Parallel,delayed 
import subprocess

iddName = "C:/EnergyPlusV23-1-0/Energy+.idd"
energyplus_install_dir = r"C:/EnergyPlusV23-1-0/"
epw_relative_filepath = 'C:/EnergyPlusV23-1-0/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'



source_dir = 'D:/ABCC/BaseModelCorrelation'

files = os.listdir(source_dir)
print(files)
os.chdir(source_dir)

def area_correlation(iddname, file):
    if '.idf' in str(file):
        IDF.setiddname(iddName)
        idf1 = IDF(file)

        for object in idf1.idfobjects['SimulationControl']:
            object.Do_Zone_Sizing_Calculation = 'Yes'
            object.Do_System_Sizing_Calculation = 'No'
            object.Do_Plant_Sizing_Calculation = 'No'
            object.Run_Simulation_for_Sizing_Periods = 'No'
            object.Run_Simulation_for_Weather_File_Run_Periods = 'No'

        for object in idf1.idfobjects['Site:Location']:
            site_name = object.Name

        idf1.saveas(str(file))

        
        # for i in new_values:
        input_file = str(os.path.abspath(file)).replace("\\","/")
        file_prefix = str(site_name).replace(' ', '_') + '_' + str(file).replace('.idf', '') + ' '
        cl_st = (f'{energyplus_install_dir}\\EnergyPlus '
                    + f'--output-prefix {file_prefix}'
                    # + '--readvars '  
                    # + f'--output-directory output_files '
                    + f'--weather {epw_relative_filepath} '
                    + f'{input_file}'
                    )
        print(cl_st)
        subprocess.run(cl_st, capture_output = True)
    else:
        pass

Parallel(n_jobs=8)(delayed(area_correlation)(iddName, file) for file in files)

# area_correlation(iddName, '1.idf')