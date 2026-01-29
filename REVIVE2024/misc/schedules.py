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

def hourSch(idf,nameSch, hourlyValues):
    params = [x for x in hourlyValues]
    schValues = {}
    count = 5
    for i,param in enumerate(params):
        count = count + 1
        schValues['Field_' + str(count)] = ('Until: ' + str(i + 1) + ':00')
        count = count + 1
        schValues['Field_' + str(count)] = param
    idf.newidfobject('Schedule:Compact',
    Name = str(nameSch),
    Schedule_Type_Limits_Name = 'Fraction',
    Field_1 = 'Through: 12/31',
    Field_2 = 'For: SummerDesignDay WinterDesignDay',
    Field_3 = 'Until: 24:00',
    Field_4 = 0,
    Field_5 = 'For: AllOtherDays',
    **schValues)

def zeroSch(idf,nameSch):
    idf.newidfobject('Schedule:Compact',
        Name = str(nameSch),
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = 'For: AllOtherDays',
        Field_6 = 'Until: 24:00',
        Field_7 = 0
    )

def ResilienceSchedules(idf, outage1start, outage1end, outage2start, outage2end, 
                        coolingOutageStart,coolingOutageEnd,NatVentAvail,NatVentType,
                        demandCoolingAvail,shadingAvail,outage1type):
    
    outage1start = datetime.datetime.strptime(outage1start, "%d-%b").strftime("%m/%d")
    outage1end = datetime.datetime.strptime(outage1end, "%d-%b").strftime("%m/%d")
    outage2start = datetime.datetime.strptime(outage2start, "%d-%b").strftime("%m/%d")
    outage2end = datetime.datetime.strptime(outage2end, "%d-%b").strftime("%m/%d")
    coolingOutageStart = datetime.datetime.strptime(coolingOutageStart, "%d-%b").strftime("%m/%d")
    coolingOutageEnd = datetime.datetime.strptime(coolingOutageEnd, "%d-%b").strftime("%m/%d")
    
    idf.newidfobject('Schedule:Compact',
        Name = 'ExhaustFanSchedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 06:00',
        Field_4 = 0,
        Field_5 = 'Until: 06:30',
        Field_6 = 1,
        Field_7 = 'Until: 18:00',
        Field_8 = 0.0,
        Field_9 = 'Until: 18:30',
        Field_10 = 1.0,
        Field_11 = 'Until: 24:00'
        )
    
    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Number')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Any Number')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Fraction')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'On/Off')

    idf.newidfobject('Schedule:Constant',
        Name = 'HVAC_ALWAYS_4',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 4
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Phius_68F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 20
        )
    
    idf.newidfobject('Schedule:Constant',
        Name = 'DHW_122F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 2
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Phius_77F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 25
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'HUMIDITY_SETPOINT',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 60
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'AirVelocitySch',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0.16
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Always_On',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Always Off',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'Occupant_Activity_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 120
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'Occupant_Eff_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0
        )

    idf.newidfobject('Schedule:Compact',
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

    idf.newidfobject('Schedule:Compact',
        Name = 'CO2_Schedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 500
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'OccupantSchedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'ERVAvailable',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )
    
    if demandCoolingAvail == 1 and outage1type =='HEATING':
        idf.newidfobject('Schedule:Compact',
            Name = 'MechAvailable',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = ('Through: ' + str(outage1start)),
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = ('Through: ' + str(outage1end)),
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 0.0,
            Field_9 = ('Through: ' + str(outage2start)),
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0,
            Field_13 = ('Through: ' + str(outage2end)),
            Field_14 = 'For: AllDays',
            Field_15 = 'Until: 24:00',
            Field_16 = 1.0,
            Field_17 = 'Through: 12/31',
            Field_18 = 'For: AllDays',
            Field_19 = 'Until: 24:00',
            Field_20 = 1.0
            )

    if demandCoolingAvail == 1 and outage1type !='HEATING':
        idf.newidfobject('Schedule:Compact',
            Name = 'MechAvailable',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = ('Through: ' + str(outage1start)),
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = ('Through: ' + str(outage1end)),
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 1.0,
            Field_9 = ('Through: ' + str(outage2start)),
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0,
            Field_13 = ('Through: ' + str(outage2end)),
            Field_14 = 'For: AllDays',
            Field_15 = 'Until: 24:00',
            Field_16 = 0.0,
            Field_17 = 'Through: 12/31',
            Field_18 = 'For: AllDays',
            Field_19 = 'Until: 24:00',
            Field_20 = 1.0
            )

    if demandCoolingAvail != 1:
        idf.newidfobject('Schedule:Compact',
            Name = 'MechAvailable',
            Schedule_Type_Limits_Name = 'Fraction',
            Field_1 = ('Through: ' + str(outage1start)),
            Field_2 = 'For: AllDays',
            Field_3 = 'Until: 24:00',
            Field_4 = 1.0,
            Field_5 = ('Through: ' + str(outage1end)),
            Field_6 = 'For: AllDays',
            Field_7 = 'Until: 24:00',
            Field_8 = 0.0,
            Field_9 = ('Through: ' + str(outage2start)),
            Field_10 = 'For: AllDays',
            Field_11 = 'Until: 24:00',
            Field_12 = 1.0,
            Field_13 = ('Through: ' + str(outage2end)),
            Field_14 = 'For: AllDays',
            Field_15 = 'Until: 24:00',
            Field_16 = 0.0,
            Field_17 = 'Through: 12/31',
            Field_18 = 'For: AllDays',
            Field_19 = 'Until: 24:00',
            Field_20 = 1.0
            )

    if NatVentType == "NatVent":
        idf.newidfobject('Schedule:Compact',
            Name = 'NatVent',
            Schedule_Type_Limits_Name = 'On/Off',
            Field_1 = ('Through: ' + str(coolingOutageStart)),
            Field_2 = 'For: SummerDesignDay',
            Field_3 = 'Until: 24:00',
            Field_4 = 0,
            Field_5 = 'For: AllOtherDays',
            Field_6  ='Until: 24:00',
            Field_7 = 0,
            Field_8 = ('Through: ' + str(coolingOutageEnd)),
            Field_9 = 'For: SummerDesignDay',
            Field_10 = 'Until: 24:00',
            Field_11 = 0,
            Field_12 = 'For: AllOtherDays',
            Field_13  ='Until: 24:00',
            Field_14 = NatVentAvail,
            Field_15 = 'Through: 12/31', 
            Field_16 = 'For: AllDays',
            Field_17 = 'Until: 24:00',
            Field_18 = 0)
        
    if NatVentType == "SchNatVent":
        idf.newidfobject('Schedule:Compact',
            Name = 'SchNatVent',
            Schedule_Type_Limits_Name = 'On/Off',
            Field_1 = ('Through: ' + str(coolingOutageStart)),
            Field_2 = 'For: SummerDesignDay',
            Field_3 = 'Until: 24:00',
            Field_4 = 0,
            Field_5 = 'For: AllOtherDays',
            Field_6  ='Until: 24:00',
            Field_7 = 0,
            Field_8 = ('Through: ' + str(coolingOutageEnd)),
            Field_9 = 'For: SummerDesignDay',
            Field_10 = 'Until: 24:00',
            Field_11 = 0,
            Field_12 = 'For: AllOtherDays',
            Field_13  ='Until: 24:00',
            Field_14 = NatVentAvail,
            Field_15 = 'Through: 12/31', 
            Field_16 = 'For: AllDays',
            Field_17 = 'Until: 24:00',
            Field_18 = 0)
        
    if NatVentType == "DCinterlock":
        idf.newidfobject('Schedule:Compact',
            Name = 'DCinterlock',
            Schedule_Type_Limits_Name = 'On/Off',
            Field_1 = ('Through: ' + str(coolingOutageStart)),
            Field_2 = 'For: SummerDesignDay',
            Field_3 = 'Until: 24:00',
            Field_4 = 0,
            Field_5 = 'For: AllOtherDays',
            Field_6  ='Until: 24:00',
            Field_7 = 0,
            Field_8 = ('Through: ' + str(coolingOutageEnd)),
            Field_9 = 'For: SummerDesignDay',
            Field_10 = 'Until: 24:00',
            Field_11 = 0,
            Field_12 = 'For: AllOtherDays',
            Field_13  ='Until: 24:00',
            Field_14 = NatVentAvail,
            Field_15 = 'Through: 12/31', 
            Field_16 = 'For: AllDays',
            Field_17 = 'Until: 24:00',
            Field_18 = 0)
        
    idf.newidfobject('Schedule:Compact',
        Name = 'OutageCooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 0,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 1)

    idf.newidfobject('Schedule:Compact',
        Name = 'Demand Control Cooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = demandCoolingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf.newidfobject('Schedule:Compact',
        Name = 'ShadingAvailable',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = shadingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf.newidfobject('Schedule:Compact',
        Name = 'SizingLoads',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0)
    
def VanosZoneCalculations(idf, zone):

    # Creating Vanos Schedule and EMS components for a given zone
    idf.newidfobject('Schedule:Constant',
        Name = (str(zone) + '_Vanos'),
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0
    )

    idf.newidfobject('Schedule:Constant',
        Name = (str(zone) + '_VanosLimit'),
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0
    )
    
    idf.newidfobject('Output:Table:TimeBins',
        Key_Value = (str(zone) + '_Vanos'),
        Variable_Name = 'Schedule Value',
        Interval_Start = 0,
        Interval_Size = 0.75,
        Interval_Count = 1
    )

    # Trying the above method
    # idf.newidfobject('Output:Table:Monthly',
    #     Name = (str(zone) + '_Vanos'),
    #     Digits_After_Decimal = 0,
    #     Variable_or_Meter_1_Name = 'Schedule Value',
    #     Aggregation_Type_for_Variable_or_Meter_1 = 'HoursPositive'
    # )

    # EMS Scripting

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = (str(zone) + '_IRH'),
        OutputVariable_or_OutputMeter_Index_Key_Name = (str(zone)),
        OutputVariable_or_OutputMeter_Name = 'Zone Air Relative Humidity'
    )

    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = (str(zone) + '_Vanos'),
        Actuated_Component_Unique_Name = (str(zone) + '_Vanos'),
        Actuated_Component_Type = 'Schedule:Constant',
        Actuated_Component_Control_Type = 'Schedule Value'
    )

    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = (str(zone) + '_VanosLimit'),
        Actuated_Component_Unique_Name = (str(zone) + '_VanosLimit'),
        Actuated_Component_Type = 'Schedule:Constant',
        Actuated_Component_Control_Type = 'Schedule Value'
    )

    idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
        Name = (str(zone) + '_VanosCaller'),
        EnergyPlus_Model_Calling_Point = 'EndOfZoneTimestepAfterZoneReporting',
        Program_Name_1 = (str(zone) + '_VanosCalculation')
    )

    idf.newidfobject('EnergyManagementSystem:Program',
        Name = (str(zone) + '_VanosCalculation'),
        Program_Line_1 = ('SET ' + (str(zone) + '_Vanos') + ' = 0'),
        Program_Line_2 = ('SET ' + (str(zone) + '_VanosLimit') + ' = (-0.0032 *' + (str(zone) + '_IDB') + '^5) + (0.55 * ' + (str(zone) + '_IDB') + '^4) - (37.9 * ' + (str(zone) + '_IDB') + '^3) + (1299.7 * ' + (str(zone) + '_IDB') + '^2) - (22167.2 * ' + (str(zone) + '_IDB') + ') + 151867'),
        Program_Line_3 = ('IF ' + (str(zone) + '_IRH') +' > ' + (str(zone) + '_VanosLimit')),
        Program_Line_4 = ('SET ' + (str(zone) + '_Vanos') + ' = ' + (str(zone) + '_Vanos') + ' + 1'),
        Program_Line_5 = 'ENDIF'
        )


# def VanosGeneralCalculations(zone):

def AnnualControls(idf, unit_list):
    for zone in unit_list:
        idf.newidfobject('Schedule:Constant',
            Name = (str(zone) + '_WindowFractionControl'),
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )
def TBschedules(idf, unit_list):
    for zone in unit_list:

        idf.newidfobject('EnergyManagementSystem:Sensor',
            Name = (str(zone) + '_IDB'),
            OutputVariable_or_OutputMeter_Index_Key_Name = str(zone),
            OutputVariable_or_OutputMeter_Name = 'Zone Air Temperature')
        
        idf.newidfobject('EnergyManagementSystem:Sensor',
            Name = 'ODB',
            OutputVariable_or_OutputMeter_Index_Key_Name ='*',
            OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Drybulb Temperature')
        
        idf.newidfobject('EnergyManagementSystem:Actuator',
            Name = (str(zone) + '_tbTemp'),
            Actuated_Component_Unique_Name = (str(zone) + '_TB Schedule'),
            Actuated_Component_Type = 'Schedule:Constant',
            Actuated_Component_Control_Type = 'Schedule Value')
        
        idf.newidfobject('Schedule:Constant',
            Name = (str(zone) + '_TB Schedule'),
            Schedule_Type_Limits_Name = 'Fraction',
            Hourly_Value = 0
            )
        
        idf.newidfobject('EnergyManagementSystem:Program',
            Name = (str(zone) + '_TBDelta'),
            Program_Line_1 = ('IF ODB == ' + (str(zone) + '_IDB')),
            Program_Line_2 = ('SET ' + (str(zone) + '_tbTemp') + ' = 0'),
            Program_Line_3 = 'ELSE',
            Program_Line_4 = ('SET ' + (str(zone) + '_tbTemp') + ' = ' + 'ODB - ' + (str(zone) + '_IDB')),
            Program_Line_5 = 'ENDIF')
        
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
            Name = (str(zone) + '_Program Caller'),
            EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
            Program_Name_1 = (str(zone) + '_TBDelta')
            )



def ResilienceControls(idf, unit_list, NatVentType):

    for zone in unit_list:
        # zone = str(zone).replace(' ','_')

        idf.newidfobject('EnergyManagementSystem:Sensor',
            Name = (str(zone) + '_IWB'),
            OutputVariable_or_OutputMeter_Index_Key_Name = (str(zone) + '_Zone_Air_Node'),
            OutputVariable_or_OutputMeter_Name = 'System Node Wetbulb Temperature')
        
        
        idf.newidfobject('EnergyManagementSystem:Sensor',
            Name = (str(zone) + '_IDh'),
            OutputVariable_or_OutputMeter_Index_Key_Name = (str(zone) + '_Zone_Air_Node'),
            OutputVariable_or_OutputMeter_Name = 'System Node Enthalpy')    

        idf.newidfobject('EnergyManagementSystem:Sensor',
            Name = (str(zone) + '_IDB'),
            OutputVariable_or_OutputMeter_Index_Key_Name = str(zone),
            OutputVariable_or_OutputMeter_Name = 'Zone Air Temperature')
        
        idf.newidfobject('EnergyManagementSystem:Actuator',
            Name = (str(zone) + 'WindowEconomizer'),
            Actuated_Component_Unique_Name = (str(zone) + '_WindowFractionControl'),
            Actuated_Component_Type = 'Schedule:Constant',
            Actuated_Component_Control_Type = 'Schedule Value')
        
        idf.newidfobject('EnergyManagementSystem:Actuator',
            Name = (str(zone) + '_tbTemp'),
            Actuated_Component_Unique_Name = (str(zone) + '_TB Schedule'),
            Actuated_Component_Type = 'Schedule:Constant',
            Actuated_Component_Control_Type = 'Schedule Value')
                
        idf.newidfobject('Schedule:Constant',
            Name = (str(zone) + '_WindowFractionControl'),
            Schedule_Type_Limits_Name = 'Any Number',
            Hourly_Value = 0
            )
        
        idf.newidfobject('Schedule:Constant',
            Name = (str(zone) + '_TB Schedule'),
            Schedule_Type_Limits_Name = 'Fraction',
            Hourly_Value = 0
            )
        

        if NatVentType == "SchNatVent":
            idf.newidfobject('EnergyManagementSystem:Program',
                Name = (str(zone) + '_SummerVentDB'),
                Program_Line_1 = ('IF ' + (str(zone) + '_IDB') + '> 1+ ODB && NatVentAvail > 0 && Clock > 0'),
                Program_Line_2 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 1'),
                Program_Line_3 = 'SET DC_Coolings = 0',
                Program_Line_4 = 'ELSE',
                Program_Line_5 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 0'),
                Program_Line_6 = 'ENDIF')
            
        if NatVentType == "NatVent":
            idf.newidfobject('EnergyManagementSystem:Program',
                Name = (str(zone) + '_SummerVentDB'),
                Program_Line_1 = ('IF ' + (str(zone) + '_IDB') + '> 1+ ODB && NatVentAvail > 0'),
                Program_Line_2 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 1'),
                Program_Line_3 = 'SET DC_Coolings = 0',
                Program_Line_4 = 'ELSE',
                Program_Line_5 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 0'),
                Program_Line_6 = 'ENDIF')
            
        if NatVentType == "DCinterlock":
            idf.newidfobject('EnergyManagementSystem:Program',
                Name = (str(zone) + '_SummerVentDB'),
                Program_Line_1 = ('IF ' + (str(zone) + '_IDh') + '> 7000 + ODh && ' + (str(zone) + '_IDB') + ' < 29.5 && NatVentAvail > 0'),
                Program_Line_2 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 1'),
                Program_Line_3 = 'SET DC_Coolings = 0',
                Program_Line_4 = 'ELSEIF NatVentAvail > 0',
                Program_Line_5 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 0'),
                Program_Line_6 = 'SET DC_Coolings = 1',
                Program_Line_7 = 'ELSE',
                Program_Line_8 = ('SET ' + (str(zone) + 'WindowEconomizer') + ' = 0'),
                Program_Line_9 = 'SET DC_Coolings = 0',
                Program_Line_10 = 'ENDIF')
        
        idf.newidfobject('EnergyManagementSystem:Program',
            Name = (str(zone) + '_TBDelta'),
            Program_Line_1 = ('IF ODB == ' + (str(zone) + '_IDB')),
            Program_Line_2 = ('SET ' + (str(zone) + '_tbTemp') + ' = 0'),
            Program_Line_3 = 'ELSE',
            Program_Line_4 = ('SET ' + (str(zone) + '_tbTemp') + ' = ' + 'ODB - ' + (str(zone) + '_IDB')),
            Program_Line_5 = 'ENDIF')
        
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager',
            Name = (str(zone) + '_Program Caller'),
            EnergyPlus_Model_Calling_Point  ='BeginZoneTimestepBeforeSetCurrentWeather',
            Program_Name_1 = (str(zone) + '_SummerVentDB'),
            Program_Name_2 = (str(zone) + '_TBDelta')
            )
            

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'OWB',
        OutputVariable_or_OutputMeter_Index_Key_Name ='*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Wetbulb Temperature')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'ODB',
        OutputVariable_or_OutputMeter_Index_Key_Name ='*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Drybulb Temperature')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'ODh',
        OutputVariable_or_OutputMeter_Index_Key_Name ='*',
        OutputVariable_or_OutputMeter_Name = 'Site Outdoor Air Enthalpy')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'NatVentAvail',
        OutputVariable_or_OutputMeter_Index_Key_Name = str(NatVentType),
        OutputVariable_or_OutputMeter_Name = 'Schedule Value')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'Clock',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'PhiusExtLight',
        OutputVariable_or_OutputMeter_Name = 'Exterior Lights Electricity Energy')

    idf.newidfobject('EnergyManagementSystem:Sensor',
        Name = 'PV',
        OutputVariable_or_OutputMeter_Index_Key_Name = 'ELC',
        OutputVariable_or_OutputMeter_Name = 'Electric Load Center Produced Electricity Energy')

    idf.newidfobject('EnergyManagementSystem:Actuator',
        Name = 'DC_Coolings',
        Actuated_Component_Unique_Name = 'Demand Control Cooling',
        Actuated_Component_Type = 'Schedule:Compact',
        Actuated_Component_Control_Type = 'Schedule Value')
    
def AnnualSchedules(idf, outage1start, outage1end, outage2start, outage2end, 
                        coolingOutageStart,coolingOutageEnd,NatVentAvail,
                        demandCoolingAvail,shadingAvail):

    SchName_Lighting = 'Phius_Lighting'
    SchValues_Lighting = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

    SchName_MELs = 'Phius_MELs'
    SchValues_MELs = [0.008, 0.008, 0.008, 0.008, 0.024, 0.050, 0.056, 0.050, 0.022, 0.015, 0.015, 0.015, 0.015, 0.015, 0.026, 0.015, 0.056, 0.078, 0.105, 0.126, 0.128, 0.088, 0.049, 0.020]

    SchName_DHW = 'CombinedDHWSchedule'
    SchValues_DHW = [0.006, 0.003, 0.001, 0.001, 0.003, 0.022, 0.075, 0.079, 0.076, 0.067, 0.061, 0.048, 0.042, 0.037, 0.037, 0.033, 0.044, 0.058, 0.069, 0.065, 0.059, 0.048, 0.042, 0.023]

    SchName_Range = 'BARangeSchedule'
    SchValues_Range = [0.007,0.007,0.004,0.004,0.007,0.011,0.025,0.042,0.046,0.048,0.042,0.05,0.057,0.046,0.057,0.044,0.092,0.15,0.117,0.06,0.035,0.025,0.016,0.011]    

    SchName_ClothesDryer = 'BAClothesDryerSchedule'
    SchValues_ClothesDryer = [0.01,0.006,0.004,0.002,0.004,0.006,0.016,0.032,0.048,0.068,0.078,0.081,0.074,0.067,0.057,0.061,0.055,0.054,0.051,0.051,0.052,0.054,0.044,0.024]  

    SchName_ClothesWasher = 'BAClothesWasherSchedule'
    SchValues_ClothesWasher = [0.009,0.007,0.004,0.004,0.007,0.011,0.022,0.049,0.073,0.086,0.084,0.075,0.067,0.06,0.049,0.052,0.05,0.049,0.049,0.049,0.049,0.047,0.032,0.017]  

    SchName_Dishwasher = 'BADishwasherSchedule'
    SchValues_Dishwasher = [0.015,0.007,0.005,0.003,0.003,0.01,0.02,0.031,0.058,0.065,0.056,0.048,0.041,0.046,0.036,0.038,0.038,0.049,0.087,0.111,0.09,0.067,0.044,0.031]

    SchName_Occupant = 'OccupantSchedule'
    SchValues_Occupant = [1,1,1,1,1,1,1,1,0.9,0.4,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.55,0.9,0.9,0.9,1,1,1]

    hourSch(idf, SchName_Lighting, SchValues_Lighting)
    hourSch(idf, SchName_MELs, SchValues_MELs)
    hourSch(idf, SchName_DHW, SchValues_DHW)
    hourSch(idf, SchName_Range, SchValues_Range)
    hourSch(idf, SchName_ClothesDryer, SchValues_ClothesDryer)
    hourSch(idf, SchName_ClothesWasher, SchValues_ClothesWasher)
    hourSch(idf, SchName_Dishwasher, SchValues_Dishwasher)
    hourSch(idf, SchName_Occupant, SchValues_Occupant)

    idf.newidfobject('Schedule:Compact',
        Name = 'ExhaustFanSchedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 06:00',
        Field_4 = 0,
        Field_5 = 'Until: 06:30',
        Field_6 = 1,
        Field_7 = 'Until: 18:00',
        Field_8 = 0.0,
        Field_9 = 'Until: 18:30',
        Field_10 = 1.0,
        Field_11 = 'Until: 24:00'
        )

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Number')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Any Number')
    
    idf.newidfobject('ScheduleTypeLimits',
        Name = 'ANYNUMBER')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'Fraction')

    idf.newidfobject('ScheduleTypeLimits',
        Name = 'On/Off')

    idf.newidfobject('Schedule:Constant',
        Name = 'WindowFraction2',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'HVAC_ALWAYS_4',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 4
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Phius_68F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 20
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Phius_77F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 25
        )
    
    idf.newidfobject('Schedule:Constant',
        Name = 'DHW_122F',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 50
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'HUMIDITY_SETPOINT',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 60
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'AirVelocitySch',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0.16
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Always_On',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'Always Off',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 0
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'Occupant_Activity_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 120
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'Occupant_Eff_Schedule',
        Schedule_Type_Limits_Name = 'Any Number',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0
        )

    idf.newidfobject('Schedule:Compact',
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

    idf.newidfobject('Schedule:Compact',
        Name = 'CO2_Schedule',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 500
        )

    idf.newidfobject('Schedule:Constant',
        Name = 'ERVAvailable',
        Schedule_Type_Limits_Name = 'Any Number',
        Hourly_Value = 1
        )
    
    idf.newidfobject('Schedule:Compact',
        Name = 'MechAvailable',
        Schedule_Type_Limits_Name = 'Fraction',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1.0,
        )

    idf.newidfobject('Schedule:Compact',
        Name = 'OutageCooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 1,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 1)

    idf.newidfobject('Schedule:Compact',
        Name = 'Demand Control Cooling',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = 0,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf.newidfobject('Schedule:Compact',
        Name = 'ShadingAvailable',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = ('Through: ' + str(coolingOutageStart)),
        Field_2 = 'For: AllDays',
        Field_3 = 'Until: 24:00',
        Field_4 = 0,
        Field_5 = ('Through: ' + str(coolingOutageEnd)),
        Field_6 = 'For: AllDays',
        Field_7 = 'Until: 24:00',
        Field_8 = shadingAvail,
        Field_9 = 'Through: 12/31',
        Field_10 = 'For: AllDays',
        Field_11 = 'Until: 24:00',
        Field_12 = 0)

    idf.newidfobject('Schedule:Compact',
        Name = 'SizingLoads',
        Schedule_Type_Limits_Name = 'On/Off',
        Field_1 = 'Through: 12/31',
        Field_2 = 'For: SummerDesignDay',
        Field_3 = 'Until: 24:00',
        Field_4 = 1,
        Field_5 = 'For: AllOtherDays',
        Field_6  ='Until: 24:00',
        Field_7 = 0)