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

study_folder = 'D:/ABCC/upg_0_job_1_idf/sim_files_job0_2'
iddName = "C:/EnergyPlusV23-1-0/Energy+.idd"


# files = os.listdir(study_folder)

IDF.setiddname(iddName)
os.chdir(str(study_folder))

files = os.listdir()

print(files)
for file in files:
    if '.idf' in str(file):
        idfName = file

for file in files:
    if '.csv' in file:
        scheduleFile = file


idf1 = IDF(idfName)

for object in idf1.idfobjects['LifeCycleCost:Parameters']:
    idf1.removeidfobject(object)

for object in idf1.idfobjects['LifeCycleCost:NonrecurringCost']:
    idf1.removeidfobject(object)

delete_objects = idf1.idfobjects['LifeCycleCost:UsePriceEscalation']
for object in range(len(delete_objects)):
    idf1.removeidfobject(delete_objects[-1])

schedules_from_file = idf1.idfobjects['Schedule:File']

for schedule in schedules_from_file:
        schedule.File_Name = scheduleFile

compact_schedules = idf1.idfobjects['Schedule:Compact']
for schedule in compact_schedules:
    if schedule.Name == 'living zone Thermostat Schedule':
        t_stat_sch = schedule.Name


non_occ_schedules = []
non_occ_schedules_EMS = [t_stat_sch.replace(' ','_')]

for schedule in schedules_from_file:
    if 'occupants' not in schedule.Name: 
        non_occ_schedules.append(schedule.Name)
        non_occ_schedules_EMS.append(schedule.Name.replace(' ','_'))

# Occupant settings and new schedules for the thermal resilience test
idf1.newidfobject('Schedule:Compact',
        Name = 'Occupant_Eff_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0
        )

idf1.newidfobject('Schedule:Compact',
        Name = 'Occupant_Clothing_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 04/30',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1.0,
        Field_5 = 'Through: 09/30',
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 0.3,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 1.0
        )
idf1.newidfobject('Schedule:Constant',
        Name = 'AirVelocitySch',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0.16
        )

people = idf1.idfobjects['PEOPLE']
for persons in people:
    persons.Work_Efficiency_Schedule_Name = 'Occupant_Eff_Schedule'
    persons.Clothing_Insulation_Calculation_Method = 'ClothingInsulationSchedule'
    persons.Clothing_Insulation_Calculation_Method_Schedule_Name = 'Occupant_Clothing_Schedule'
    persons.Clothing_Insulation_Schedule_Name = 'Occupant_Clothing_Schedule'
    persons.Air_Velocity_Schedule_Name = 'AirVelocitySch'
    persons.Thermal_Comfort_Model_1_Type = 'Pierce'

    outputs = idf1.idfobjects['OUTPUTCONTROL:TABLE:STYLE']

for output in outputs:
    output.Unit_Conversion = 'InchPound'

idf1.newidfobject('Output:Table:TimeBins',
    Key_Value = '*',
    Variable_Name = 'Zone Air Temperature',
    Interval_Start = -40,
    Interval_Size = 42,
    Interval_Count = 1,
    Variable_Type = 'Temperature'
    )

outputVars = ['Site Outdoor Air Drybulb Temperature', 'Zone Air Relative Humidity', 'Zone Air CO2 Concentration', 'Zone Air Temperature', 'Exterior Lights Electricity Energy', 
            'Zone Ventilation Mass Flow Rate', 'Schedule Value', 'Electric Equipment Electricity Energy',
            'Facility Total Purchased Electricity Energy', 'Zone Heat Index', 'Zone Thermal Comfort Pierce Model Standard Effective Temperature', 'Site Outdoor Air Relative Humidity',
            'Site Outdoor Air Dewpoint Temperature', 'Zone Mean Air Dewpoint Temperature']
meterVars = ['InteriorLights:Electricity', 'InteriorEquipment:Electricity', 'Fans:Electricity', 'Heating:Electricity', 'Cooling:Electricity', 'ElectricityNet:Facility',
            'NaturalGas:Facility'] 
for x in outputVars:
    idf1.newidfobject('Output:Variable',
    Key_Value = '*',
    Variable_Name = str(x),
    Reporting_Frequency = 'hourly'
    )

for x in meterVars:
    idf1.newidfobject('Output:Meter:MeterFileOnly',
    Key_Name = str(x),
    Reporting_Frequency = 'Monthly'
    )

fName = (str(idfName.split('.')[0]) + '_BR.idf')
runName = (str(idfName) + '_BR')

idf1.saveas(fName)