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

def SizingSettings(idf, zone):
    idf.newidfobject('DesignSpecification:OutdoorAir',
        Name = (str(zone) + '_SZ_DSOA'),
        Outdoor_Air_Method = 'Flow/Person',
        Outdoor_Air_Flow_per_Person = 7.08000089E-03,
        Outdoor_Air_Flow_per_Zone = 0.01179868608
        )

    idf.newidfobject('DesignSpecification:ZoneAirDistribution',
        Name = (str(zone) + '_SZ_DSZAD'),
        Zone_Air_Distribution_Effectiveness_in_Cooling_Mode = 1,
        Zone_Air_Distribution_Effectiveness_in_Heating_Mode = 1
        )

    idf.newidfobject('Sizing:Zone',
        Zone_or_ZoneList_Name = str(zone),
        Zone_Cooling_Design_Supply_Air_Temperature_Input_Method = 'SupplyAirTemperature',
        Zone_Cooling_Design_Supply_Air_Temperature = 12.8,
        Zone_Cooling_Design_Supply_Air_Temperature_Difference = 11.11,
        Zone_Heating_Design_Supply_Air_Temperature_Input_Method = 'SupplyAirTemperature',
        Zone_Heating_Design_Supply_Air_Temperature = 50,
        Zone_Heating_Design_Supply_Air_Temperature_Difference = 30,
        Zone_Cooling_Design_Supply_Air_Humidity_Ratio = 0.008,
        Zone_Heating_Design_Supply_Air_Humidity_Ratio = 0.008,
        Design_Specification_Outdoor_Air_Object_Name = (str(zone) + '_SZ_DSOA'),
        Cooling_Design_Air_Flow_Method = 'DesignDay',
        Heating_Design_Air_Flow_Method = 'DesignDay',
        Design_Specification_Zone_Air_Distribution_Object_Name = (str(zone) + '_SZ_DSZAD'),
        Zone_Heating_Sizing_Factor = 2,
        Zone_Cooling_Sizing_Factor = 1.5
        )
    
def HVACControls(idf, zone):
    idf.newidfobject('ZoneControl:Humidistat',
        Name = (str(zone) + '_Humidistat'),
        Zone_Name = str(zone),
        Humidifying_Relative_Humidity_Setpoint_Schedule_Name = 'Humidity_Setpoint'
        )

    idf.newidfobject('ZoneControl:Thermostat',
        Name = (str(zone) + '_Thermostat'),
        Zone_or_ZoneList_Name = str(zone),
        Control_Type_Schedule_Name = 'HVAC_Always_4',
        Control_1_Object_Type = 'ThermostatSetpoint:DualSetpoint',
        Control_1_Name = (str(zone) + '_DSP_Thermostat')
        )

    idf.newidfobject('ThermostatSetpoint:DualSetpoint',
        Name = (str(zone) + '_DSP_Thermostat'),
        Heating_Setpoint_Temperature_Schedule_Name = 'Phius_68F',
        Cooling_Setpoint_Temperature_Schedule_Name = 'Phius_77F'
        )
    
def ZoneMechConnections(idf, zone):
    idf.newidfobject('ZoneHVAC:EquipmentConnections',
        Zone_Name = str(zone),
        Zone_Conditioning_Equipment_List_Name = (str(zone) + '_Equipment'),
        Zone_Air_Inlet_Node_or_NodeList_Name = (str(zone) + '_Inlets'),
        Zone_Air_Exhaust_Node_or_NodeList_Name = (str(zone) + '_Exhausts'),
        Zone_Air_Node_Name = (str(zone) + '_Zone_Air_Node'),
        Zone_Return_Air_Node_or_NodeList_Name = (str(zone) + '_Returns')
        )

    idf.newidfobject('NodeList',
        Name = (str(zone) + '_Inlets'),
        Node_1_Name = (str(zone) + '_ERV_Supply'),
        Node_2_Name = (str(zone) + '_MECH_Air_Outlet')
        )

    idf.newidfobject('NodeList',
        Name = (str(zone) + '_Returns'),
        Node_1_Name = (str(zone) + '_Return')
        )

    idf.newidfobject('NodeList',
        Name = (str(zone) + '_Exhausts'),
        Node_1_Name = (str(zone) + '_ERV_Exhaust'),
        Node_2_Name = (str(zone) + '_MECH_Air_Inlet')
        )
    
def HVACBuilder(idf, zone, mechSystemType):

    if mechSystemType == 'PTHP':

        idf.newidfobject('ZoneHVAC:EquipmentList',
            Name = (str(zone) + '_Equipment'),
            Load_Distribution_Scheme = 'SequentialLoad',
            Zone_Equipment_1_Object_Type = 'ZoneHVAC:EnergyRecoveryVentilator',
            Zone_Equipment_1_Name = (str(zone) + ' ERV'),
            Zone_Equipment_1_Cooling_Sequence = 2,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence = 2,
            Zone_Equipment_2_Object_Type = 'ZoneHVAC:PackagedTerminalHeatPump',
            Zone_Equipment_2_Name = (str(zone) + '_PTHP'),
            Zone_Equipment_2_Cooling_Sequence = 1,
            Zone_Equipment_2_Heating_or_NoLoad_Sequence = 1
            #Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name = 
            #Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name = 
            )

        idf.newidfobject('ZoneHVAC:PackagedTerminalHeatPump',
            Name = (str(zone) + '_PTHP'),
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_MECH_Air_Outlet'),
            # OutdoorAir:Mixer,________!-_Outdoor_Air_Mixer_Object_Type
            # Zone1PTHPOAMixer,________!-_Outdoor_Air_Mixer_Name
            Cooling_Supply_Air_Flow_Rate = 'autosize',
            Heating_Supply_Air_Flow_Rate = 'autosize',
            # No_Load_Supply_Air_Flow_Rate_{m3/s}
            Cooling_Outdoor_Air_Flow_Rate = 'autosize',
            Heating_Outdoor_Air_Flow_Rate = 'autosize',
            # No_Load_Outdoor_Air_Flow_Rate_{m3/s}
            Supply_Air_Fan_Object_Type = 'Fan:SystemModel',
            Supply_Air_Fan_Name = (str(zone) + '_PTHP_Fan'),
            Heating_Coil_Object_Type = 'Coil:Heating:DX:SingleSpeed',
            Heating_Coil_Name = (str(zone) + '_PTHP_DX_Heat_Coil'),
            #Heating_Convergence_Tolerance_{dimensionless}
            Cooling_Coil_Object_Type = 'Coil:Cooling:DX:SingleSpeed',
            Cooling_Coil_Name = (str(zone) + '_PTHP_DX_Cool_Coil'),
            #Cooling_Convergence_Tolerance_{dimensionless}
            Supplemental_Heating_Coil_Object_Type = 'Coil:Heating:Electric',
            Supplemental_Heating_Coil_Name = (str(zone) + '_PTHP_Sup_Heater'),
            Maximum_Supply_Air_Temperature_from_Supplemental_Heater = 50,
            Maximum_Outdoor_DryBulb_Temperature_for_Supplemental_Heater_Operation = 10,
            Fan_Placement = 'BlowThrough'
            #ConstantFanSch;__________!-_Supply_Air_Fan_Operating_Mode_Schedule_Name')
            )

        idf.newidfobject('Fan:SystemModel',
            Name = (str(zone) + '_PTHP_Fan'),
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_PTHP_Fan_Outlet'),
            Design_Maximum_Air_Flow_Rate = 'autosize',
            Speed_Control_Method = 'Continuous',
            Electric_Power_Minimum_Flow_Rate_Fraction = 0.0,
            Design_Pressure_Rise = 160,
            Motor_Efficiency = 0.9,
            Motor_In_Air_Stream_Fraction = 1.0,
            Design_Electric_Power_Consumption = 'autosize',
            Design_Power_Sizing_Method = 'TotalEfficiencyAndPressure',
            # Electric_Power_Per_Unit_Flow_Rate_{W/(m3/s)}
            # Electric_Power_Per_Unit_Flow_Rate_Per_Unit_Pressure_{W/((m3/s)-Pa)}
            Fan_Total_Efficiency = 0.5,
            Electric_Power_Function_of_Flow_Fraction_Curve_Name = 'CombinedPowerAndFanEff'
            )

        idf.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = (str(zone) + '_PTHP_DX_Cool_Coil'),
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Total_Cooling_Capacity = 'autosize',
            Gross_Rated_Sensible_Heat_Ratio = 0.75,
            Gross_Rated_Cooling_COP = 3.0,  # Change to var for future shit
            Rated_Air_Flow_Rate = 'autosize',
            Air_Inlet_Node_Name = (str(zone) + '_PTHP_Fan_Outlet'),
            Air_Outlet_Node_Name  = (str(zone) + '_PTHP_DX_Cool_Coil_Outlet'),
            Total_Cooling_Capacity_Function_of_Temperature_Curve_Name = 'HPACCoolCapFT',
            Total_Cooling_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACCoolCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACPLFFPLR'
            )

        idf.newidfobject('Coil:Heating:DX:SingleSpeed',
            Name = (str(zone) + '_PTHP_DX_Heat_Coil'),
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Heating_Capacity = 'autosize',
            Gross_Rated_Heating_COP = 3.0, #change to var for future
            Rated_Air_Flow_Rate  ='autosize',
            # Rated_Supply_Fa,n_Power_Per_Volume_Flow_Rate_{W/(m3/s)}
            Air_Inlet_Node_Name = (str(zone) + '_PTHP_DX_Cool_Coil_Outlet'),
            Air_Outlet_Node_Name = (str(zone) + '_PTHP_DX_Heat_Coil_Outlet'),
            Heating_Capacity_Function_of_Temperature_Curve_Name = 'HPACHeatCapFT',
            Heating_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACHeatEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACCOOLPLFFPLR',
            # Defrost_Energy_Input_Ratio_Function_of_Temperature_Curve_Name
            Minimum_Outdoor_DryBulb_Temperature_for_Compressor_Operation = 0.0, #future var
            #Outdoor_Dry-Bulb_Temperature_to_Turn_On_Compressor_{C}
            Maximum_Outdoor_DryBulb_Temperature_for_Defrost_Operation = 5.0,
            Crankcase_Heater_Capacity = 0,
            Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater_Operation = 10.0,
            Defrost_Strategy = 'Resistive',
            Defrost_Control = 'TIMED',
            Defrost_Time_Period_Fraction = 0.166667,
            Resistive_Defrost_Heater_Capacity = 'autosize'
            )

        idf.newidfobject('Coil:Heating:Electric',
            Name = (str(zone) + '_PTHP_Sup_Heater'),
            Availability_Schedule_Name = 'MechAvailable',
            Efficiency = 1.0,
            Nominal_Capacity = 'autosize',
            Air_Inlet_Node_Name = (str(zone) + '_PTHP_DX_Heat_Coil_Outlet'),
            Air_Outlet_Node_Name = (str(zone) + '_MECH_Air_Outlet')
            )
        
    if mechSystemType == 'GasFurnaceDXAC':

        idf.newidfobject('ZoneHVAC:EquipmentList',
            Name = (str(zone) + '_Equipment'),
            Load_Distribution_Scheme = 'SequentialLoad',
            Zone_Equipment_1_Object_Type = 'ZoneHVAC:EnergyRecoveryVentilator',
            Zone_Equipment_1_Name = (str(zone) + ' ERV'),
            Zone_Equipment_1_Cooling_Sequence = 2,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence = 2,
            Zone_Equipment_2_Object_Type = 'AirLoopHVAC:UnitarySystem',
            Zone_Equipment_2_Name = (str(zone) +'_GasHeat_DXAC_Furnace'),
            Zone_Equipment_2_Cooling_Sequence = 1,
            Zone_Equipment_2_Heating_or_NoLoad_Sequence = 1
            #Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name = 
            #Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name = 
            )
      
        idf.newidfobject('AirLoopHVAC:UnitarySystem',
            Name = (str(zone) +'_GasHeat_DXAC_Furnace'),
            Control_Type = 'Load',
            Controlling_Zone_or_Thermostat_Location  =str(zone),
            Dehumidification_Control_Type = 'None',
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_MECH_Air_Outlet'),
            Supply_Fan_Object_Type = 'Fan:OnOff',
            Supply_Fan_Name = (str(zone) + 'Furnace_Blower'),
            Fan_Placement = 'BlowThrough',
            Heating_Coil_Object_Type = 'Coil:Heating:Fuel',
            Heating_Coil_Name = (str(zone) + 'Furnace_Heating_Coil'),
            Cooling_Coil_Object_Type = 'Coil:Cooling:DX:SingleSpeed',
            Cooling_Coil_Name = (str(zone) +'Furnace_DXAC_Coil'),
            Cooling_Supply_Air_Flow_Rate = 'autosize',
            Heating_Supply_Air_Flow_Rate = 'autosize',
            No_Load_Supply_Air_Flow_Rate = 0,
            Maximum_Supply_Air_Temperature = 50,
            )

        idf.newidfobject('Coil:Heating:Fuel',
            Name = (str(zone) + 'Furnace_Heating_Coil'),
            Availability_Schedule_Name = 'MechAvailable',
            Fuel_Type = 'NaturalGas',
            Burner_Efficiency = 0.8,
            Nominal_Capacity = 'autosize',
            Air_Inlet_Node_Name = (str(zone) + '_Heating_Coil_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_MECH_Air_Outlet'),
            )
        
        idf.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = (str(zone) + 'Furnace_DXAC_Coil'),
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Total_Cooling_Capacity = 'autosize',
            Gross_Rated_Sensible_Heat_Ratio = 0.75,
            Gross_Rated_Cooling_COP = 3.0,  # Change to var for future shit
            Rated_Air_Flow_Rate = 'autosize',
            Air_Inlet_Node_Name = (str(zone) + '_DXAC_Coil_Air_Inlet'),
            Air_Outlet_Node_Name  = (str(zone) + '_Heating_Coil_Air_Inlet'),
            Total_Cooling_Capacity_Function_of_Temperature_Curve_Name = 'HPACCoolCapFT',
            Total_Cooling_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACCoolCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACPLFFPLR'
            )

        idf.newidfobject('Fan:OnOff',
            Name = (str(zone) + 'Furnace_Blower'),
            Availability_Schedule_Name = 'MechAvailable',
            Fan_Total_Efficiency = 0.7,
            Pressure_Rise = 225,
            Maximum_Flow_Rate = 2,
            Motor_Efficiency = 0.9,
            Motor_In_Airstream_Fraction = 1.0,
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_DXAC_Coil_Air_Inlet')
            )
        

    if mechSystemType == 'SplitHeatPump':

        idf.newidfobject('ZoneHVAC:EquipmentList',
            Name = (str(zone) + '_Equipment'),
            Load_Distribution_Scheme = 'SequentialLoad',
            Zone_Equipment_1_Object_Type = 'ZoneHVAC:EnergyRecoveryVentilator',
            Zone_Equipment_1_Name = (str(zone) + ' ERV'),
            Zone_Equipment_1_Cooling_Sequence = 2,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence = 2,
            Zone_Equipment_2_Object_Type = 'AirLoopHVAC:UnitarySystem',
            Zone_Equipment_2_Name = (str(zone) + 'Split_HP'),
            Zone_Equipment_2_Cooling_Sequence = 1,
            Zone_Equipment_2_Heating_or_NoLoad_Sequence = 1
            #Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name = 
            #Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name = 
            )
        
        idf.newidfobject('AirLoopHVAC:UnitarySystem',
            Name = (str(zone) + 'Split_HP'),
            Control_Type = 'Load',
            Controlling_Zone_or_Thermostat_Location  =str(zone),
            Dehumidification_Control_Type = 'None',
            Availability_Schedule_Name = 'MechAvailable',
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_MECH_Air_Outlet'),
            Supply_Fan_Object_Type = 'Fan:OnOff',
            Supply_Fan_Name = 'FurnaceBlower',
            Fan_Placement = 'BlowThrough',
            Heating_Coil_Object_Type = 'Coil:Heating:DX:SingleSpeed',
            Heating_Coil_Name = 'Zone1SplitDXHeatCoil',
            Cooling_Coil_Object_Type = 'Coil:Cooling:DX:SingleSpeed',
            Cooling_Coil_Name = 'Furnace ACDXCoil 1',
            Cooling_Supply_Air_Flow_Rate = 'autosize',
            Heating_Supply_Air_Flow_Rate = 'autosize',
            No_Load_Supply_Air_Flow_Rate = 0,
            Maximum_Supply_Air_Temperature = 50,
            )

        idf.newidfobject('Coil:Heating:DX:SingleSpeed',
            Name = 'Zone1SplitDXHeatCoil',
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Heating_Capacity = 'autosize',
            Gross_Rated_Heating_COP = 4.5, #change to var for future
            Rated_Air_Flow_Rate  ='autosize',
            # Rated_Supply_Fa,n_Power_Per_Volume_Flow_Rate_{W/(m3/s)}
            Air_Inlet_Node_Name = 'Zone1PTHPDXCoolCoilOutletNode',
            Air_Outlet_Node_Name = 'Zone1PTHPDXHeatCoilOutletNode',
            Heating_Capacity_Function_of_Temperature_Curve_Name = 'HPACHeatCapFT',
            Heating_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACHeatEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACHeatEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACCOOLPLFFPLR',
            # Defrost_Energy_Input_Ratio_Function_of_Temperature_Curve_Name
            Minimum_Outdoor_DryBulb_Temperature_for_Compressor_Operation = 0.0, #future var
            #Outdoor_Dry-Bulb_Temperature_to_Turn_On_Compressor_{C}
            Maximum_Outdoor_DryBulb_Temperature_for_Defrost_Operation = 5.0,
            Crankcase_Heater_Capacity = 0,
            Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater_Operation = 10.0,
            Defrost_Strategy = 'Resistive',
            Defrost_Control = 'TIMED',
            Defrost_Time_Period_Fraction = 0.166667,
            Resistive_Defrost_Heater_Capacity = 'autosize'
            )
        idf.newidfobject('Coil:Cooling:DX:SingleSpeed',
            Name = (str(zone) + 'Furnace_DXAC_Coil'),
            Availability_Schedule_Name = 'MechAvailable',
            Gross_Rated_Total_Cooling_Capacity = 'autosize',
            Gross_Rated_Sensible_Heat_Ratio = 0.75,
            Gross_Rated_Cooling_COP = 3.0,  # Change to var for future shit
            Rated_Air_Flow_Rate = 'autosize',
            Air_Inlet_Node_Name = (str(zone) + '_DXAC_Coil_Air_Inlet'),
            Air_Outlet_Node_Name  = (str(zone) + '_Heating_Coil_Air_Inlet'),
            Total_Cooling_Capacity_Function_of_Temperature_Curve_Name = 'HPACCoolCapFT',
            Total_Cooling_Capacity_Function_of_Flow_Fraction_Curve_Name = 'HPACCoolCapFFF',
            Energy_Input_Ratio_Function_of_Temperature_Curve_Name = 'HPACEIRFT',
            Energy_Input_Ratio_Function_of_Flow_Fraction_Curve_Name = 'HPACEIRFFF',
            Part_Load_Fraction_Correlation_Curve_Name = 'HPACPLFFPLR'
            )

        idf.newidfobject('Fan:OnOff',
            Name = (str(zone) + 'Furnace_Blower'),
            Availability_Schedule_Name = 'MechAvailable',
            Fan_Total_Efficiency = 0.7,
            Pressure_Rise = 225,
            Maximum_Flow_Rate = 2,
            Motor_Efficiency = 0.9,
            Motor_In_Airstream_Fraction = 1.0,
            Air_Inlet_Node_Name = (str(zone) + '_MECH_Air_Inlet'),
            Air_Outlet_Node_Name = (str(zone) + '_DXAC_Coil_Air_Inlet')
            )
        
def WaterHeater(idf, zone, dhwFuel, DHW_CombinedGPM):

    idf.newidfobject('WaterHeater:Mixed',
        Name = (str(zone) + '_ElectricWaterHeater_50Gal'),
        Tank_Volume = 0.1892706,
        Setpoint_Temperature_Schedule_Name = 'DHW_122F',
        # Deadband Temperature Difference
        Maximum_Temperature_Limit = 82.2222,
        Heater_Control_Type = 'MODULATE',
        Heater_Maximum_Capacity = 11712,
        Heater_Minimum_Capacity = 0,
        # Heater Ignition Minimum Flow Rate {m3/s}
        # Heater Ignition Delay {s}
        Heater_Fuel_Type = str(dhwFuel),
        Heater_Thermal_Efficiency = 0.95,
        # Part Load Factor Curve Name
        Off_Cycle_Parasitic_Fuel_Consumption_Rate = 10,
        Off_Cycle_Parasitic_Fuel_Type = 'ELECTRICITY',
        Off_Cycle_Parasitic_Heat_Fraction_to_Tank = 0,
        On_Cycle_Parasitic_Fuel_Consumption_Rate = 30,
        On_Cycle_Parasitic_Fuel_Type = 'ELECTRICITY',
        On_Cycle_Parasitic_Heat_Fraction_to_Tank = 0,
        Ambient_Temperature_Indicator = 'ZONE',
        # Ambient Temperature Schedule Name
        Ambient_Temperature_Zone_Name = str(zone),
        # Ambient Temperature Outdoor Air Node Name
        Off_Cycle_Loss_Coefficient_to_Ambient_Temperature = 2.36,
        # Off Cycle Loss Fraction to Zone
        # On Cycle Loss Coefficient to Ambient Temperature {W/K}
        # On Cycle Loss Fraction to Zone
        Peak_Use_Flow_Rate = DHW_CombinedGPM,
        Use_Flow_Rate_Fraction_Schedule_Name = 'CombinedDHWSchedule'
        # Cold Water Supply Temperature Schedule Name
        )

def Curves(idf):

    idf.newidfobject('Curve:Cubic',
        Name = 'CombinedPowerAndFanEff',
        Coefficient1_Constant = 0.0,
        Coefficient2_x = 0.027411,
        Coefficient3_x2 = 0.008740,
        Coefficient4_x3 = 0.969563,
        Minimum_Value_of_x = 0.5,
        Maximum_Value_of_x = 1.5,
        Minimum_Curve_Output = 0.01,
        Maximum_Curve_Output = 1.5
        )
    idf.newidfobject('Curve:Quadratic',
        Name = 'HPACCoolCapFFF',
        Coefficient1_Constant = 0.8,
        Coefficient2_x = 0.2,
        Coefficient3_x2 = 0.0,
        Minimum_Value_of_x = 0.5,
        Maximum_Value_of_x = 1.5
        )
    idf.newidfobject('Curve:Quadratic',
        Name = 'HPACEIRFFF',
        Coefficient1_Constant = 1.1552,
        Coefficient2_x = -0.1808,
        Coefficient3_x2  =0.0256,
        Minimum_Value_of_x = 0.5,
        Maximum_Value_of_x = 1.5
        )
    idf.newidfobject('Curve:Quadratic',
        Name = 'HPACPLFFPLR',
        Coefficient1_Constant = 0.85,
        Coefficient2_x = 0.15,
        Coefficient3_x2 = 0.0,
        Minimum_Value_of_x = 0.0,
        Maximum_Value_of_x = 1.0
        )
    idf.newidfobject('Curve:Quadratic',
        Name = 'HPACHeatEIRFFF',
        Coefficient1_Constant = 1.3824,
        Coefficient2_x = -0.4336,
        Coefficient3_x2 = 0.0512,
        Minimum_Value_of_x = 0.0,
        Maximum_Value_of_x = 1.0
        )
    idf.newidfobject('Curve:Quadratic',
        Name = 'HPACCOOLPLFFPLR',
        Coefficient1_Constant = 0.75,
        Coefficient2_x = 0.25,
        Coefficient3_x2 = 0.0,
        Minimum_Value_of_x = 0.0,
        Maximum_Value_of_x = 1.0
        )
    idf.newidfobject('Curve:Cubic',
        Name = 'HPACHeatCapFT',
        Coefficient1_Constant = 0.758746,
        Coefficient2_x = 0.027626,
        Coefficient3_x2 = 0.000148716,
        Coefficient4_x3 = 0.0000034992,
        Minimum_Value_of_x = -20.0,
        Maximum_Value_of_x = 20.0,
        # Minimum_Curve_Output
        # Maximum_Curve_Output
        Input_Unit_Type_for_X = 'Temperature',
        Output_Unit_Type = 'Dimensionless'
        )
    idf.newidfobject('Curve:Cubic',
        Name = 'HPACHeatCapFFF',
        Coefficient1_Constant = 0.84,
        Coefficient2_x = 0.16,
        Coefficient3_x2 = 0.0,
        Coefficient4_x3 = 0.0,
        Minimum_Value_of_x = 0.5,
        Maximum_Value_of_x = 1.5
        )
    idf.newidfobject('Curve:Cubic',
        Name = 'HPACHeatEIRFT',
        Coefficient1_Constant = 1.19248,
        Coefficient2_x = -0.0300438,
        Coefficient3_x2 = 0.00103745,
        Coefficient4_x3 = -0.000023328,
        Minimum_Value_of_x = -20.0,
        Maximum_Value_of_x = 20.0,
        # Minimum_Curve_Output
        # Maximum_Curve_Output
        Input_Unit_Type_for_X = 'Temperature',
        Output_Unit_Type = 'Dimensionless'
        )
    idf.newidfobject('Curve:Cubic',
        Name = 'FanEffRatioCurve',
        Coefficient1_Constant = 0.33856828,
        Coefficient2_x = 1.72644131,
        Coefficient3_x2 = -1.49280132,
        Coefficient4_x3 = 0.42776208,
        Minimum_Value_of_x = 0.5,
        Maximum_Value_of_x = 1.5,
        Minimum_Curve_Output = 0.3,
        Maximum_Curve_Output = 1.0
        )
    idf.newidfobject('Curve:Exponent',
        Name = 'FanPowerRatioCurve',
        Coefficient1_Constant = 0.0,
        Coefficient2_Constant = 1.0,
        Coefficient3_Constant = 3.0,
        Minimum_Value_of_x = 0.0,
        Maximum_Value_of_x = 1.5,
        Minimum_Curve_Output = 0.01,
        Maximum_Curve_Output = 1.5
        )
    idf.newidfobject('Curve:Biquadratic',
        Name = 'HPACCoolCapFT',
        Coefficient1_Constant = 0.942587793,
        Coefficient2_x = 0.009543347,
        Coefficient3_x2 = 0.000683770,
        Coefficient4_y = -0.011042676,
        Coefficient5_y2 = 0.000005249,
        Coefficient6_xy = -0.000009720,
        Minimum_Value_of_x = 12.77778,
        Maximum_Value_of_x = 23.88889,
        Minimum_Value_of_y = 18.0,
        Maximum_Value_of_y = 46.11111,
        # Minimum_Curve_Output
        # Maximum_Curve_Output
        Input_Unit_Type_for_X = 'Temperature',
        Input_Unit_Type_for_Y = 'Temperature',
        Output_Unit_Type = 'Dimensionless'
        )
    idf.newidfobject('Curve:Biquadratic',
        Name = 'HPACEIRFT',
        Coefficient1_Constant = 0.342414409,
        Coefficient2_x = 0.034885008,
        Coefficient3_x2 = -0.000623700,
        Coefficient4_y = 0.004977216,
        Coefficient5_y2 = 0.000437951,
        Coefficient6_xy = -0.000728028,
        Minimum_Value_of_x = 12.77778,
        Maximum_Value_of_x = 23.88889,
        Minimum_Value_of_y = 18.0,
        Maximum_Value_of_y = 46.11111,
        # Minimum_Curve_Output
        # Maximum_Curve_Output
        Input_Unit_Type_for_X ='Temperature',
        Input_Unit_Type_for_Y ='Temperature',
        Output_Unit_Type = 'Dimensionless'
        )
    
def ResilienceERV(idf, zone, occ, ervSense, ervLatent):

    idf.newidfobject('ZoneHVAC:EnergyRecoveryVentilator',
        Name = (str(zone) + ' ERV'),
        Availability_Schedule_Name = 'ERVAvailable',
        Heat_Exchanger_Name = (str(zone) + ' ERV_Core'),
        Supply_Air_Flow_Rate = (0.00235973725*occ),
        Exhaust_Air_Flow_Rate = (0.00235973725*occ),
        Supply_Air_Fan_Name = (str(zone) + ' ERV_Supply_Fan'),
        Exhaust_Air_Fan_Name = (str(zone) + ' ERV_Exhaust_Fan')
        )

    idf.newidfobject('Fan:OnOff',
        Name = (str(zone) + ' ERV_Supply_Fan'),
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = (str(zone) + '_ERV_Core_Sup_Out'),
        Air_Outlet_Node_Name = (str(zone) + '_ERV_Supply'),
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf.newidfobject('Fan:OnOff',
        Name = (str(zone) + ' ERV_Exhaust_Fan'),
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = (str(zone) + '_ERV_Core_Exh_Out'),
        Air_Outlet_Node_Name = (str(zone) + '_ERV_Exhaust'),
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf.newidfobject('HeatExchanger:AirToAir:SensibleAndLatent',
        Name = (str(zone) + ' ERV_Core'),
        Availability_Schedule_Name = 'ERVAvailable',
        Nominal_Supply_Air_Flow_Rate = 0.047,
        Sensible_Effectiveness_at_100_Heating_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Heating_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Heating_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Heating_Air_Flow = (ervLatent * 1.1),
        Sensible_Effectiveness_at_100_Cooling_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Cooling_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Cooling_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Cooling_Air_Flow =  (ervLatent * 1.1),
        Supply_Air_Inlet_Node_Name = (str(zone) + '_OA_1'),
        Supply_Air_Outlet_Node_Name = (str(zone) + '_ERV_Core_Sup_Out'),
        Exhaust_Air_Inlet_Node_Name = (str(zone) + '_ERV_Exhaust'),
        Exhaust_Air_Outlet_Node_Name = (str(zone) + '_ERV_Core_Exh_Out'),
        Supply_Air_Outlet_Temperature_Control = 'No',
        Heat_Exchanger_Type = 'Plate',
        Frost_Control_Type = 'ExhaustAirRecirculation',
        Threshold_Temperature = -10,
        Initial_Defrost_Time_Fraction = 0.083,
        Rate_of_Defrost_Time_Fraction_Increase = 0.012,
        Economizer_Lockout = 'Yes'
        )

    idf.newidfobject('OutdoorAir:Node',
        Name = (str(zone) + '_OA_1'),
        Height_Above_Ground = 3.048
        )

    idf.newidfobject('OutdoorAir:Node',
        Name = (str(zone) + '_OA_2'),
        Height_Above_Ground = 3.048
        )

def AnnualERV(idf, zone, occ, ervSense, ervLatent):

    idf.newidfobject('ZoneHVAC:EnergyRecoveryVentilator',
        Name = (str(zone) + ' ERV'),
        Availability_Schedule_Name = 'ERVAvailable',
        Heat_Exchanger_Name = (str(zone) + ' ERV_Core'),
        Supply_Air_Flow_Rate = (0.00707921175*occ),
        Exhaust_Air_Flow_Rate = (0.00707921175*occ),
        Supply_Air_Fan_Name = (str(zone) + ' ERV_Supply_Fan'),
        Exhaust_Air_Fan_Name = (str(zone) + ' ERV_Exhaust_Fan')
        )

    idf.newidfobject('Fan:OnOff',
        Name = (str(zone) + ' ERV_Supply_Fan'),
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = (str(zone) + '_ERV_Core_Sup_Out'),
        Air_Outlet_Node_Name = (str(zone) + '_ERV_Supply'),
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf.newidfobject('Fan:OnOff',
        Name = (str(zone) + ' ERV_Exhaust_Fan'),
        Availability_Schedule_Name = 'ERVAvailable',
        Fan_Total_Efficiency = 0.6,
        Pressure_Rise = 200,
        Maximum_Flow_Rate = 'autosize',
        Motor_Efficiency = 0.8,
        Motor_In_Airstream_Fraction = 1,
        Air_Inlet_Node_Name = (str(zone) + '_ERV_Core_Exh_Out'),
        Air_Outlet_Node_Name = (str(zone) + '_ERV_Exhaust'),
        EndUse_Subcategory = 'ERV_Fan'
        )

    idf.newidfobject('HeatExchanger:AirToAir:SensibleAndLatent',
        Name = (str(zone) + ' ERV_Core'),
        Availability_Schedule_Name = 'ERVAvailable',
        Nominal_Supply_Air_Flow_Rate = 0.047,
        Sensible_Effectiveness_at_100_Heating_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Heating_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Heating_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Heating_Air_Flow = (ervLatent * 1.1),
        Sensible_Effectiveness_at_100_Cooling_Air_Flow = ervSense,
        Latent_Effectiveness_at_100_Cooling_Air_Flow = ervLatent,
        Sensible_Effectiveness_at_75_Cooling_Air_Flow = (ervSense * 1.1),
        Latent_Effectiveness_at_75_Cooling_Air_Flow =  (ervLatent * 1.1),
        Supply_Air_Inlet_Node_Name = (str(zone) + '_OA_1'),
        Supply_Air_Outlet_Node_Name = (str(zone) + '_ERV_Core_Sup_Out'),
        Exhaust_Air_Inlet_Node_Name = (str(zone) + '_ERV_Exhaust'),
        Exhaust_Air_Outlet_Node_Name = (str(zone) + '_ERV_Core_Exh_Out'),
        Supply_Air_Outlet_Temperature_Control = 'No',
        Heat_Exchanger_Type = 'Plate',
        Frost_Control_Type = 'ExhaustAirRecirculation',
        Threshold_Temperature = -10,
        Initial_Defrost_Time_Fraction = 0.083,
        Rate_of_Defrost_Time_Fraction_Increase = 0.012,
        Economizer_Lockout = 'Yes'
        )

    idf.newidfobject('OutdoorAir:Node',
        Name = (str(zone) + '_OA_1'),
        Height_Above_Ground = 3.048
        )

    idf.newidfobject('OutdoorAir:Node',
        Name = (str(zone) + '_OA_2'),
        Height_Above_Ground = 3.048
        )
