import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("agg")
# import datetime as dt
from datetime import datetime as dt
from datetime import timedelta
from statistics import mean
import eppy as eppy
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs
from eppy.runner.run_functions import EnergyPlusRunError
import multiprocessing.pool as mp_pool
# from PIL import Image, ImageTk
import os
from eppy.results import fasthtml
import os
import json
import misc.adorb as adorb
import misc.envelope as envelope
import misc.hvac as hvac
import misc.internalHeatGains as internalHeatGains
import misc.outputs as outputs
# import parallel
import misc.renewables as renewables
import misc.schedules as schedules
import misc.simControl as simControl
import misc.weatherMorph as weatherMorph
import misc.validation as validation
# TODO: CLEAN UP IMPORTS

"""Class to hold all inputs that do not vary from run to run""" 
class SimInputs:

    def __init__(self, batch_name, idd_file, study_folder, run_list, database_dir, num_procs, graphs_enabled, pdf_enabled, del_files, is_dummy_mode):
        # collect basic input information
        self.is_dummy_mode = is_dummy_mode
        self.idd_file = idd_file
        self.database_dir = database_dir
        self.num_procs = num_procs
        self.graphs_enabled = graphs_enabled
        self.pdf_enabled = pdf_enabled
        self.del_files_enabled = del_files
        
        # establish dummy-dependent input information
        self.batch_name = batch_name if not is_dummy_mode else os.path.abspath("dummy")
        self.study_folder = study_folder if not is_dummy_mode else os.path.abspath("dummy")
        self.run_list = run_list if not is_dummy_mode else os.path.join(study_folder, "dummy_runlist.csv")

        # establish output folder hierarchy
        self.batch_folder = os.path.join(study_folder, batch_name)
        self.results_folder = os.path.join(self.batch_folder, "results")
        self.graphs_folder = os.path.join(self.batch_folder, "graphs")
        self.temp_folder = os.path.join(self.batch_folder, "temp")
        
        # generate the implied input information
        self.generate_database_inputs()
        self.load_runlist()


    def generate_database_inputs(self):
        # emissions and weather data
        emissions_file = "Hourly Emission Rates.csv"
        weather_folder = "Weather Data"
        construction_file = "Construction Database.csv"
        self.emissions_db = os.path.join(self.database_dir, emissions_file)
        self.weather_db = os.path.join(self.database_dir, weather_folder)
        self.construction_db = os.path.join(self.database_dir, construction_file)


    def load_runlist(self):
        self.run_list_df = pd.read_csv(self.run_list)
        self.total_runs = self.run_list_df.shape[0]



class SimulationManager:
    def __init__(self, q, num_tasks, stop_event):
        # init the progress queue
        self.q = q

        # compute the increment amount
        self.num_checkpoints = 13 + 1 # changes based on how many baked into code
        self.increment_amt = 1 / (self.num_checkpoints * num_tasks)

        # init the stop event
        self.stop_event = stop_event

    
    def send_progress(self):
        if self.q is not None:
            self.q.put(self.increment_amt)

    def raise_exception(self, msg):
        if self.q is not None:
            try:
                self.q.put(msg)
            except BrokenPipeError:
                print(f"Failed to send message: \"{msg}\"")
    
    def check_if_stopped(self):
        return self.stop_event.is_set()
        


class GracefulExitException(Exception):
    """Throw specific type of error to signify graceful exit."""
    pass



### UTILITY FUNCTIONS
def divide_chunks(l, n): 
      
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n]


def get_outage_bounds(row):
    outage1start = row['OUTAGE_1_START'].item()
    outage1end = row['OUTAGE_1_END'].item()
    outage2start = row['OUTAGE_2_START'].item()
    outage2end = row['OUTAGE_2_END'].item()
    outage1type = row['1ST_OUTAGE'].item()

    # compute and return heating and cooling outages
    if outage1type == 'HEATING':
        heatingOutageStart, heatingOutageEnd, coolingOutageStart, coolingOutageEnd = outage1start, outage1end, outage2start, outage2end
    else:
        heatingOutageStart, heatingOutageEnd, coolingOutageStart, coolingOutageEnd = outage2start, outage2end, outage1start, outage1end

    return heatingOutageStart, heatingOutageEnd, coolingOutageStart, coolingOutageEnd


# TODO: HOW TO HANDLE CHECKPOINTS FOR BATCH SIMULATE?
def checkpoint(sm: SimulationManager):
    """Returns true if program received stop signal, otherwise sends progress update and returns false"""
    # gui not enabled, exit
    if sm is None: return

    # check for stop signal
    if sm.check_if_stopped(): raise GracefulExitException
    
    # all clear, update progress
    sm.send_progress()


def make_output_folders(sim_inputs: SimInputs):
    os.mkdir(sim_inputs.batch_folder)
    os.mkdir(sim_inputs.results_folder)
    if sim_inputs.graphs_enabled:
        os.mkdir(sim_inputs.graphs_folder)
    os.mkdir(sim_inputs.temp_folder)


# TODO: HOOK GUI UP TO INNER FUNCTION AND RETIRE PARALLEL_SIMULATE
def parallel_simulate(sim_inputs: SimInputs, progress_queue=None, stop_event=None):

    # run the parallelized simulation
    sim_mgr = SimulationManager(progress_queue, sim_inputs.total_runs, stop_event)
    simulate_with_gui_communication(sim_inputs, sim_mgr)
    
#     # export results of any completed runs
#     ResultsTable = pd.concat(result_rows)
#     if sm.check_if_stopped():
#         return
#     ResultsTable.to_csv(os.path.join(sim_inputs.study_folder, sim_inputs.batch_name + "_ResultsTable.csv"))
#     print('Saved Results')


def simulate_with_gui_communication(si: SimInputs, sm: SimulationManager):
    """Check for any graceful exit requests, otherwise communicate error received to gui."""
    # prepare folders to organize output
    make_output_folders(si)# move to study folder for all sims
    os.chdir(si.batch_folder)

    # attempt to run the simulation with error handling
    try:
        # perform resilience simulations
        idfs_batch1 = parallel_runner(resilience_simulation_prep, si, sm)
        batch_simulation(si, idfs_batch1, "BR", sm)

        # process resilience results
        parallel_runner(process_resilience_simulation_output, si, sm)

        # generate the idfs for annual simulation
        idfs_batch2 = parallel_runner(annual_simulation_prep, si, sm)
        batch_simulation(si, idfs_batch2, "BA", sm)

        # process annual results
        parallel_runner(process_annual_simulation_output, si, sm)

        # with the two simulations done, compute adorb costs
        parallel_runner(compute_adorb_costs, si, sm)

        # collect the individual and combined results
        output_file_names = parallel_runner(collect_individual_simulation_results, si, sm)
        collect_all_results(si, output_file_names, sm)

        # generate graphs
        if si.graphs_enabled:
            parallel_runner(generate_graphs, si, sm)

        # cleanup here
        cleanup_outputs(si) # TODO: INCLUDE DELETE TEMP FILES GUI OPTION
    
    # check for graceful exit request
    except GracefulExitException:
        return
    
    # collect and export here
    print("Saved Results!")
    return


def parallel_runner(fn, si: SimInputs, simulation_mgr=None):
    """Runs the specified simulate function in a multiprocessing pool."""
    # create the pool
    with mp_pool.ThreadPool(processes=si.num_procs) as pool:
        # run the function
        try:
            results = pool.starmap(error_handler, [(fn, si, case_id, simulation_mgr) for case_id in range(si.total_runs)])
        
        # otherwise, pass the error to the gui
        except GracefulExitException:
            pool.terminate()
            return
    
    # return results
    return results


def error_handler(fn, si: SimInputs, case_id: int, simulation_mgr=None):
    """Send any errors back to the gui and return None for run result if caught."""
    # run the function here
    try:
        return fn(si, case_id, simulation_mgr)

    # if caught, pass the graceful exit signal along
    except GracefulExitException:
        raise GracefulExitException
    
    # otherwise pass the error to the gui
    # COMMENT OUT BLOCK TO DEBUG
    # except Exception as e:
    #     simulation_mgr.raise_exception(str(e))
    #     return None



def resilience_simulation_prep(si: SimInputs, case_id: int, simulation_mgr=None):
    """Generates and returns IDF for a resilience simulation based on runlist inputs."""
    # CHECKPOINT: resilience prep started
    checkpoint(simulation_mgr)       

    # retrieve cached information from simulation input
    iddfile = si.idd_file
    studyFolder = si.study_folder
    batchFolder = si.batch_folder
    tempFolder = si.temp_folder
    databaseDir = si.database_dir

    weatherDatabase = si.weather_db
    constructionDatabase = si.construction_db

    IDF.setiddname(iddfile)

    runList = si.run_list_df
    runCount = case_id
    idfgName = str(runList['GEOMETRY_IDF'][runCount])
    caseName = runList['CASE_NAME'][runCount]

    # establish file names
    BaseFileName = f"{si.batch_name}_{caseName}"
    testingFile_BR = os.path.join(batchFolder, BaseFileName + "_BR.idf")
    passIDF = os.path.join(batchFolder, BaseFileName + "_PASS.idf")

    epwFile = os.path.join(weatherDatabase, str(runList['EPW'][runCount]))
    ddyName =  os.path.join(weatherDatabase, str(runList['DDY'][runCount]))
    
    # validate spreadsheet input
    assert os.path.isfile(epwFile), "Cannot find specified EPW file."
    assert os.path.isfile(ddyName), "Cannot find specified DDY file."

    operableArea_N = ((runList['Operable_Area_N'][runCount])*0.09290304)
    operableArea_S = ((runList['Operable_Area_S'][runCount])*0.09290304)
    operableArea_W = ((runList['Operable_Area_W'][runCount])*0.09290304)
    operableArea_E = ((runList['Operable_Area_E'][runCount])*0.09290304)
    halfHeight = 1.524
    ervSense = runList["SENSIBLE_RECOVERY_EFF"][runCount]
    ervLatent = runList["LATENT_RECOVERY_EFF"][runCount]


    # IHG Calc
    constructionList = pd.read_csv(constructionDatabase, index_col="Name")
    raw_appliance_list = runList["APPLIANCE_LIST"][runCount]
    appliance_list = raw_appliance_list.split(', ') if not pd.isna(raw_appliance_list) else []

    ihg_dict = {}
    for Nbr in range(9):
        total_appliance_cost = fridge = dishWasher = clothesWasher = clothesDryer = fracHighEff = lights_cost = 0
        for appliance_name, row in constructionList[constructionList.index.isin(appliance_list)].iterrows():
            rating = float(row["Appliance_Rating"]) # must be float for fractional efficiency
            cost = int(row["Mechanical Cost"])
            if 'FRIDGE' in appliance_name:
                fridge += (rating/(8760))*1000 # always on design load

            elif 'DISHWASHER' in appliance_name:
                dishWasher += (((86.3 + (47.73 / (215 / rating)))/215) * ((88.4 + 34.9*Nbr)*(12/12))*(1/365)*1000)

            elif 'CLOTHESWASHER' in appliance_name:
                clothesWasher += (rating/365)*1000

            elif 'CLOTHESDRYER' in appliance_name:
                clothesDryer += ((12.4*(164+46.5*Nbr)*1.18/3.01*(2.874/0.817-704/rating)/(0.2184*(4.5*4.08+0.24)))/365)*1000

            elif 'LIGHTS' in appliance_name:
                fracHighEff = rating
                lights_cost += cost
        
            total_appliance_cost += cost
        ihg_dict[Nbr] = {'fridge':fridge, 'dishwasher':dishWasher, 'clotheswasher':clothesWasher,
                         'clothesdryer':clothesDryer, 'lighting efficacy':fracHighEff, 
                         'lightsCost':lights_cost, 'applianceCost':total_appliance_cost}
    
    # export IHG dictionary to json for use in annual simulation
    # TODO: ASSIGN TO VARIABLE IN SIMULATION MANAGER
    # TODO: DELETE TEMPORARY FILES LIKE THIS UPON COMPLETION/EXIT
    with open(os.path.join(tempFolder, f"{BaseFileName}_IHGDict.json"), "w") as fp:
        json.dump(ihg_dict, fp)
    
    # TODO: REMOVE LATER
    constructionList = constructionList.reset_index()
    PV_SIZE = runList['PV_SIZE_[W]'][runCount]
    PV_TILT = runList['PV_TILT'][runCount]
    PV_AZIMUTH = runList["PV_AZIMUTH"][runCount]
    
    # Envelope

    infiltration_rate = runList['INFILTRATION_RATE'][runCount]
    tb = runList['CHI_VALUE'][runCount]

    Ext_Window1 = runList['EXT_WINDOW_1'][runCount]
    Ext_Window2 = runList['EXT_WINDOW_2'][runCount]
    Ext_Window3 = runList['EXT_WINDOW_3'][runCount]

    Ext_Wall1 = runList['EXT_WALL_1_NAME'][runCount]
    Ext_Roof1 = runList['EXT_ROOF_1_NAME'][runCount]
    Ext_Floor1 = runList['EXT_FLOOR_1_NAME'][runCount]
    Ext_Door1 = runList['EXT_DOOR_1_NAME'][runCount]
    Int_Floor1 = runList['INT_FLOOR_1_NAME'][runCount]

    Ext_Wall2 = runList['EXT_WALL_2_NAME'][runCount]
    Ext_Roof2 = runList['EXT_ROOF_2_NAME'][runCount]
    Ext_Floor2 = runList['EXT_FLOOR_2_NAME'][runCount]
    Ext_Door2 = runList['EXT_DOOR_2_NAME'][runCount]
    Int_Floor2 = runList['INT_FLOOR_2_NAME'][runCount]

    Ext_Wall3 = runList['EXT_WALL_3_NAME'][runCount]
    Ext_Roof3 = runList['EXT_ROOF_3_NAME'][runCount]
    Ext_Floor3 = runList['EXT_FLOOR_3_NAME'][runCount]
    Ext_Door3 = runList['EXT_DOOR_3_NAME'][runCount]
    Int_Floor3 = runList['INT_FLOOR_3_NAME'][runCount]

    # Foundation interfaces
    fnd1 = runList['FOUNDATION_INTERFACE_1'][runCount]
    fnd1i = runList['FOUNDATION_INSULATION_1'][runCount]
    fnd1p = runList['FOUNDATION_PERIMETER_1'][runCount]
    fnd1d = runList['FOUNDATION_INSULATION_DEPTH_1'][runCount]

    fnd2 = runList['FOUNDATION_INTERFACE_2'][runCount]
    fnd2i = runList['FOUNDATION_INSULATION_2'][runCount]
    fnd2p = runList['FOUNDATION_PERIMETER_2'][runCount]
    fnd2d = runList['FOUNDATION_INSULATION_DEPTH_2'][runCount]

    fnd3 = runList['FOUNDATION_INTERFACE_3'][runCount]
    fnd3i = runList['FOUNDATION_INSULATION_3'][runCount]
    fnd3p = runList['FOUNDATION_PERIMETER_3'][runCount]
    fnd3d = runList['FOUNDATION_INSULATION_DEPTH_3'][runCount]


    foundationList = []
    if str(fnd1) != 'nan':
        foundationList = [(fnd1,fnd1i,fnd1d,fnd1p)]

    if str(fnd2) != 'nan':
        foundationList = [(fnd1,fnd1i,fnd1d,fnd1p),
                            (fnd2,fnd2i,fnd2d,fnd2p)]
    
    if str(fnd3) != 'nan':
        foundationList = [(fnd1,fnd1i,fnd1d,fnd1p),
                            (fnd2,fnd2i,fnd2d,fnd2p),
                            (fnd3,fnd3i,fnd3d,fnd3p)]

    # Schedule Based Inputs
    _, _, coolingOutageStart, coolingOutageEnd = get_outage_bounds(runList.iloc[[runCount]])
    outage1start = runList['OUTAGE_1_START'][runCount]
    outage1end = runList['OUTAGE_1_END'][runCount]
    outage2start = runList['OUTAGE_2_START'][runCount]
    outage2end = runList['OUTAGE_2_END'][runCount]
    outage1type = runList['1ST_OUTAGE'][runCount]
    
    # Weather Morph inputs
    MorphFactorDB1 = runList['MorphFactorDB1'][runCount]
    MorphFactorDP1 = runList['MorphFactorDP1'][runCount]
    MorphFactorDB2 = runList['MorphFactorDB2'][runCount]
    MorphFactorDP2 = runList['MorphFactorDP2'][runCount]
    # MorphType
    MorphType = runList['MORPH_TYPE'][runCount]

    # Controls 
    NatVentType  = str(runList['NAT_VENT_TYPE'][runCount])
    NatVentAvail = runList['NAT_VENT_AVAIL'][runCount]
    shadingAvail = runList['SHADING_AVAIL'][runCount]
    demandCoolingAvail = runList['DEMAND_COOLING_AVAIL'][runCount]

    # Mechanical Inputs
    natGasPresent = runList['NATURAL_GAS'][runCount]
    dhwFuel = runList['WATER_HEATER_FUEL'][runCount]
    mechSystemType = runList['MECH_SYSTEM_TYPE'][runCount]
    cooling_COP = runList["COOLING_COP"][runCount] if pd.notna(runList["COOLING_COP"][runCount]) else ""
    heating_COP = runList["HEATING_COP"][runCount] if pd.notna(runList["HEATING_COP"][runCount]) else ""
    vent_system_type = runList['VENT_SYSTEM_TYPE'][runCount]

    gridRegion = runList['GRID_REGION'][runCount]
    #==============================================================================================================================
    # 4. Base IDF
    #==============================================================================================================================
    open(testingFile_BR, "w").close()
    idfg = IDF(os.path.join(studyFolder, idfgName))
    ddy = IDF(ddyName)
    idf1 = IDF(testingFile_BR)

    # CHECKPOINT: IDFs constructed
    checkpoint(simulation_mgr)

    # Copy in geometry from input file

    for zone in idfg.idfobjects['Zone']:
        idf1.copyidfobject(zone)

    for srf in idfg.idfobjects['BuildingSurface:Detailed']:
        idf1.copyidfobject(srf)
    
    srf_dict = {}
    for srf in idf1.idfobjects['BuildingSurface:Detailed']:
        zone_name = srf.Zone_Name.split('|')
        srf.Zone_Name = zone_name[0]
        srf_dict[srf.Name] = zone_name[0]
    

    count = -1
    windowNames = []
    windows_by_zone = {}
    for fen in idfg.idfobjects['FenestrationSurface:Detailed']:
        idf1.copyidfobject(fen)
        count += 1
        windows = idf1.idfobjects['FenestrationSurface:Detailed'][count]
        if windows.Surface_Type == 'Window':
            windowNames.append(windows.Name)
            srf_name = windows.Building_Surface_Name
            window_zone = srf_dict[srf_name]
            existing_list = windows_by_zone.get(zone_name[0],[])
            windows_by_zone[window_zone] = existing_list + [windows.Name]

    # site shading

    for site in idfg.idfobjects['Shading:Site:Detailed']:
        idf1.copyidfobject(site)

    for bldg in idfg.idfobjects['Shading:Building:Detailed']:
        idf1.copyidfobject(bldg)

    # sizing data

    for bldg in ddy.idfobjects['SizingPeriod:DesignDay']:
        idf1.copyidfobject(bldg)
    
    # CHECKPOINT: Geometries copied in
    checkpoint(simulation_mgr)

    
    # High level model information
    simControl.Version(idf1)
    simControl.SimulationControl(idf1)
    simControl.Building(idf1,BaseFileName)
    simControl.CO2Balance(idf1)
    simControl.Timestep(idf1)
    simControl.RunPeriod(idf1)
    simControl.GeometryRules(idf1)

    modeled_zones = idf1.idfobjects['ZONE']
    DHW_CombinedGPM = 0

    unit_bedroom_dict = {}
    for zone in modeled_zones:
        zone_name = zone.Name.split('|')
        zone_type = zone_name[1] if len(zone_name)>1 else ""
        zone.Name = zone_name[0]
        # print(zone_name[4])
        zone.Floor_Area = (float(zone_name[4])/10.76391)
        if 'UNIT' in zone_type:
            unit_bedroom_dict[str(zone_name[0])] = int(zone_name[2][0])
            occ = 1 + float(zone_name[2][0])
            icfa_zone = zone.Floor_Area
            Nbr_zone = float(zone_name[2][0])
            fracHighEff = ihg_dict[float(zone_name[2][0])]['lighting efficacy']
            PhiusLights = (0.2 + 0.8*(4 - 3*fracHighEff)/3.7)*(455 + 0.8*icfa_zone*10.76391) * 0.8 * 1000 * (1/365) #power per day W use Phius calc
            PhiusMELs = ((413 + 69*Nbr_zone + 0.91*icfa_zone*10.76391)/365)*1000*0.8 #consumption per day per phius calc
            rangeElec = ((331 + 39*Nbr_zone)/365)*1000
            
            # DHW Calc per BA
            DHW_ClothesWasher = 2.3 + 0.78*Nbr_zone
            DHW_Dishwasher = 2.26 + 0.75*Nbr_zone
            DHW_Shower = 0.83*(14 + 1.17*Nbr_zone)
            DHW_Bath = 0.83*(3.5+1.17*Nbr_zone)
            DHW_Sinks = 0.83*(12.5+4.16*Nbr_zone)
            DHW_CombinedGPM = (DHW_ClothesWasher + DHW_Dishwasher + DHW_Shower + DHW_Bath + DHW_Sinks)*4.381E-8

            # Sizing loads from ASHRAE 1199-RP

            G_0s = 136  #in W
            G_0l = 20  #in W
            G_cfs = 2.2  #in W
            G_cfl = 0.22  #in W
            G_ocs = 22  #in W
            G_ocl = 12  #in W

            sizingLoadSensible = G_0s + G_cfs*icfa_zone + G_ocs*occ
            sizingLoadLatent = G_0l + G_cfl*icfa_zone + G_ocl*occ
            internalHeatGains.People(idf1, zone_name[0], occ)
            internalHeatGains.LightsMELsAppliances(idf1, zone_name[0], PhiusLights, PhiusMELs, fridge, rangeElec, 
                        clothesDryer,clothesWasher,dishWasher,tb)
            internalHeatGains.SizingLoads(idf1, zone_name[0], sizingLoadSensible, sizingLoadLatent)
            internalHeatGains.ThermalMass(idf1, zone_name[0], icfa_zone)

            envelope.infiltration(idf1, zone_name[0], infiltration_rate)

            envelope.WindowVentilation(idf1, zone_name[0], halfHeight, operableArea_N, operableArea_W, 
            operableArea_S, operableArea_E)

            # insert window sorting here

            zone_windows = windows_by_zone[zone_name[0]]
            windowNames_split = list(divide_chunks(zone_windows, 10))
            for i in range(len(windowNames_split)):
                windowNamesChunk = windowNames_split[i]
                envelope.WindowShadingControl(idf1, zone_name[0], (zone_name[0]+str(i)), windowNamesChunk)

            hvac.SizingSettings(idf1, zone_name[0])
            hvac.HVACControls(idf1, zone_name[0])
            hvac.ZoneMechConnections(idf1, zone_name[0])
            hvac.HVACBuilder(idf1, zone_name[0], vent_system_type, mechSystemType, heating_COP, cooling_COP)
            hvac.WaterHeater(idf1, zone_name[0], dhwFuel, DHW_CombinedGPM)
            renewables.demand_limiting(idf1, zone_name[0])
        # Al to do
        if 'STAIR' in zone_type:
            print(str(zone_name[0]) + ' is some Stairs')
        if 'CORRIDOR' in zone_type:
            print(str(zone_name[0]) + ' is some a Corridor')
    
    # export map of units to # beds for use in annual simulation
    unit_list = [unit for unit in unit_bedroom_dict.keys()]
    with open(os.path.join(tempFolder, f"{BaseFileName}_UnitBedrooms.json"), "w") as fp:
        json.dump(unit_bedroom_dict, fp)

    # Materials and constructions
    materials = pd.read_csv(os.path.join(databaseDir, 'Material Database.csv'))
    materialList = materials.shape[0]

    for item in range(materialList):
        envelope.materialBuilder(idf1, materials['NAME'][item], materials['ROUGHNESS'][item], 
                        materials['THICKNESS [m]'][item], materials['CONDUCTIVITY [W/mK]'][item],
                        materials['DENSITY [kg/m3]'][item], materials['SPECIFIC HEAT CAPACITY [J/kgK]'][item])
        
    glazingSpecs = pd.read_csv(os.path.join(databaseDir, 'Window Database.csv'))

    glazings = glazingSpecs.shape[0]

    for item in range(glazings):
        envelope.glazingBuilder(idf1, glazingSpecs['NAME'][item], glazingSpecs['U-FACTOR [W/m2K]'][item],glazingSpecs['SHGC'][item])

    # Constructions 

    constructions = constructionList.shape[0]

    for item in range(constructions):
        if str(constructionList['Outside_Layer'][item]) != 'nan':
            layers = [constructionList['Outside_Layer'][item],
            constructionList['Layer_2'][item],
            constructionList['Layer_3'][item],
            constructionList['Layer_4'][item],
            constructionList['Layer_5'][item],
            constructionList['Layer_6'][item],
            constructionList['Layer_7'][item],
            constructionList['Layer_8'][item],
            constructionList['Layer_9'][item],
            constructionList['Layer_10'][item]]

            layerList = [x for x in layers if str(x) != 'nan']
            envelope.constructionBuilder(idf1, constructionList['Name'][item],layerList)

    # Envelope inputs
    
    envelope.SpecialMaterials(idf1)
    envelope.FoundationInterface(idf1,foundationList)
    envelope.ShadeMaterials(idf1)
    envelope.AssignContructions(idf1, Ext_Wall1,Ext_Wall2,Ext_Wall3,
            Ext_Roof1,Ext_Roof2,Ext_Roof3,
            Ext_Floor1,Ext_Floor2,Ext_Floor3,
            Ext_Door1,Ext_Door2,Ext_Door3, 
            Int_Floor1,Int_Floor2,Int_Floor3,
            Ext_Window1,Ext_Window2,Ext_Window3)

    # Sizing settings:
    hvac.Curves(idf1)

    renewables.generators(idf1, PV_SIZE, PV_TILT, PV_AZIMUTH)

    internalHeatGains.ext_lights(idf1)

    outputs.SimulationOutputs(idf1)
    
    # save the current idf state as pass file
    idf1.saveas(passIDF)
    idf1 = IDF(passIDF)

    schedules.zeroSch(idf1, 'BARangeSchedule')
    schedules.zeroSch(idf1, 'Phius_Lighting')
    schedules.zeroSch(idf1, 'Phius_MELs')
    schedules.zeroSch(idf1, 'CombinedDHWSchedule')
    schedules.zeroSch(idf1, 'BAClothesDryerSchedule')
    schedules.zeroSch(idf1, 'BAClothesWasherSchedule')
    schedules.zeroSch(idf1, 'BADishwasherSchedule')
    schedules.ResilienceSchedules(idf1, outage1start, outage1end, outage2start, outage2end, 
                                  coolingOutageStart,coolingOutageEnd,NatVentAvail,
                                  demandCoolingAvail,shadingAvail,outage1type)
    
    schedules.ResilienceControls(idf1, unit_list, NatVentType)
    
    for zone in unit_list:
        hvac.ResilienceERV(idf1, zone, vent_system_type, occ, ervSense, ervLatent)
        schedules.VanosZoneCalculations(idf1, zone)

    weatherMorph.WeatherMorphSine(idf1, outage1start, outage1end, outage2start, outage2end,
            MorphFactorDB1, MorphFactorDP1, MorphFactorDB2, MorphFactorDP2, MorphType)

    # CHECKPOINT: before resilience simulation starts
    checkpoint(simulation_mgr)

    # save and return the resulting idf
    idf1.saveas(testingFile_BR)
    idf = IDF(testingFile_BR, epwFile)
    return idf


def process_resilience_simulation_output(si: SimInputs, case_id: int, simulation_mgr=None):
    """Collects intermediate information and exports it for easier access in annual simulation."""

    # infer case run details
    runList = si.run_list_df
    runCount = case_id
    studyFolder = si.study_folder
    batchFolder = si.batch_folder
    tempFolder = si.temp_folder
    BaseFileName = f"{si.batch_name}_{runList['CASE_NAME'][runCount]}"
    
    # load the results
    resil_sim_temp_results = os.path.join(batchFolder, f"{BaseFileName}_BRout.csv")
    hourly = pd.read_csv(resil_sim_temp_results)

    # combine columns
    hourly.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
    hourly[['Date2','Time']] = hourly.DateTime.str.split(expand=True)
    hourly['Date'] = hourly['Date2'].map(str)
    hourly['Time'] = (pd.to_numeric(hourly['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourly['Time'].str[2:]
    hourly['DateTime'] = hourly['Date'] + ' ' + hourly['Time']
    hourly['DateTime'] = pd.to_datetime(hourly['DateTime'], format="%m/%d %H:%M:%S", exact=True)

    # drop the warmup
    endWarmup = hourly[hourly['DateTime'] == '1900-01-01 00:00:00'].index[0]
    dropWarmup = [*range(0, endWarmup,1)]
    hourly = hourly.drop(index = dropWarmup)
    hourly = hourly.reset_index()

    # get outage start and ends
    heatingOutageStart,heatingOutageEnd,coolingOutageStart,coolingOutageEnd = get_outage_bounds(runList.iloc[[runCount]])
    
    heatingOutageStart1 = dt.strptime((str(heatingOutageStart)), '%d-%b') + timedelta(hours=24)
    coolingOutageStart1 = dt.strptime((str(coolingOutageStart)), '%d-%b') + timedelta(hours=24)
    heatingOutageEnd1 = dt.strptime((str(heatingOutageEnd)), '%d-%b') + timedelta(hours=23)
    coolingOutageEnd1 = dt.strptime((str(coolingOutageEnd)), '%d-%b') + timedelta(hours=23)

    maskh = (hourly['DateTime'] >= heatingOutageStart1) & (hourly['DateTime'] <= heatingOutageEnd1)
    maskc = (hourly['DateTime'] >= coolingOutageStart1) & (hourly['DateTime'] <= coolingOutageEnd1)

    hourlyHeat = hourly.loc[maskh]
    hourlyCool = hourly.loc[maskc]

    # export results
    hourlyHeat.to_csv(os.path.join(batchFolder, f"{BaseFileName}_BRHourlyHeat.csv"))
    hourlyCool.to_csv(os.path.join(batchFolder, f"{BaseFileName}_BRHourlyCool.csv"))

    # CHECKPOINT: intermediate processing finished
    checkpoint(simulation_mgr)


def annual_simulation_prep(si: SimInputs, case_id: int, simulation_mgr=None):
    """Generates and returns IDF for an annual simulation based on runlist inputs."""

    # CHECKPOINT: annual prep started
    checkpoint(simulation_mgr) 

    # infer case run details
    runList = si.run_list_df
    runCount = case_id
    batchFolder = si.batch_folder
    tempFolder = si.temp_folder
    BaseFileName = f"{si.batch_name}_{runList['CASE_NAME'][runCount]}"
    testingFile_BA = os.path.join(batchFolder, BaseFileName + "_BA.idf")
    epwFile = os.path.join(si.weather_db, runList['EPW'][runCount])

    # check for the output idf, return if not found (something went wrong)
    prev_sim_htm_results = os.path.join(batchFolder, f"{BaseFileName}_BRtbl.htm")
    prev_sim_idf = os.path.join(batchFolder, f"{BaseFileName}_BR.idf")
    prev_sim_temp_results = os.path.join(batchFolder, f"{BaseFileName}_BRout.csv")
    prev_sim_hourly_heat = os.path.join(batchFolder, f"{BaseFileName}_BRHourlyHeat.csv")
    prev_sim_hourly_cool = os.path.join(batchFolder, f"{BaseFileName}_BRHourlyCool.csv")
    if (not os.path.isfile(prev_sim_htm_results) or 
        not os.path.isfile(prev_sim_idf) or
        not os.path.isfile(prev_sim_temp_results) or
        not os.path.isfile(prev_sim_hourly_heat) or
        not os.path.isfile(prev_sim_hourly_cool)):
        print("WARNING: Could not locate all outputs from resilience simulation.")
        return

    # initialize idfs for simulation
    passIDF = os.path.join(batchFolder, BaseFileName + "_PASS.idf")
    idf1 = IDF(prev_sim_idf)
    idf2 = IDF(passIDF)

    # CHECKPOINT: IDFs constructed
    checkpoint(simulation_mgr)

    # compute outage starts
    outage1start = runList['OUTAGE_1_START'][runCount]
    outage1end = runList['OUTAGE_1_END'][runCount]
    outage2start = runList['OUTAGE_2_START'][runCount]
    outage2end = runList['OUTAGE_2_END'][runCount]
    _, _, coolingOutageStart, coolingOutageEnd = get_outage_bounds(runList.iloc[[runCount]])
    
    # get other controls info for schedule from runlist
    NatVentAvail = runList['NAT_VENT_AVAIL'][runCount]
    shadingAvail = runList['SHADING_AVAIL'][runCount]
    demandCoolingAvail = runList['DEMAND_COOLING_AVAIL'][runCount]

    # plug into schedules input
    schedules.AnnualSchedules(idf2, outage1start, outage1end, outage2start, outage2end, 
                    coolingOutageStart,coolingOutageEnd,NatVentAvail,
                    demandCoolingAvail,shadingAvail)
    
    # get annual erv info
    ervSense = runList["SENSIBLE_RECOVERY_EFF"][runCount]
    ervLatent = runList["LATENT_RECOVERY_EFF"][runCount]
    vent_system_type = runList['VENT_SYSTEM_TYPE'][runCount]

    # create schedules for units with windows
    with open(os.path.join(tempFolder, f"{BaseFileName}_UnitBedrooms.json"), "r") as fp:
        unit_bedroom_dict = json.load(fp)
        unit_list = [unit for unit in unit_bedroom_dict.keys()]
    schedules.AnnualControls(idf2, unit_list)

    # loop through zones for annual erv computation
    modeled_zones = idf1.idfobjects['ZONE']
    for zone in modeled_zones:
        zone_name = zone.Name
        occ = float(unit_bedroom_dict[str(zone_name)]) + 1
        hvac.AnnualERV(idf2, zone_name, vent_system_type, occ, ervSense, ervLatent)
        

    # get envelope information
    infiltration_rate = float(runList['INFILTRATION_RATE'][runCount])
    mechSystemType = runList['MECH_SYSTEM_TYPE'][runCount]
    dhwFuel = runList['WATER_HEATER_FUEL'][runCount]
    PV_SIZE = runList['PV_SIZE_[W]'][runCount]
  
    # get hourly temperature results
    hourlyHeat = pd.read_csv(prev_sim_hourly_heat)
    hourlyCool = pd.read_csv(prev_sim_hourly_cool)
    heatingBattery = (hourlyHeat['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778
    coolingBattery = (hourlyCool['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778

    # add envelope costs from construction database
    constructionList = pd.read_csv(si.construction_db, index_col="Name")
    icfa = fasthtml.tablebyname(open(prev_sim_htm_results, "r") , "Building Area")[1][1][1]
    for name, row in constructionList.iterrows():
        outerLayer = row['Outside_Layer']
        cost = row['Cost_Per_Area_[$/m2]']
        costSealing = row['Air_Sealing_Cost_[$/ft2 ICFA]']
        costBatt = row['Battery_Cost_[$/kWh]']
        costPV = row['PV_Cost_[$/W]']
        costMech = row['Mechanical Cost']
        
        # convert numeric input if given
        try: 
            name_val = float(name) 
        except ValueError:
            name_val = None

        if cost > 0 and str(outerLayer) != 'nan':
            envelope.costBuilder(idf2, name, '','Construction', name,'','',cost,'')
        
        if costSealing > 0 and name_val == infiltration_rate:            
            envelope.costBuilder(idf2, f"AIR SEALING = {name}",'','General',0,0,(costSealing*icfa),'',1)

        if costMech> 0 and name == mechSystemType:
            envelope.costBuilder(idf2, f"MECH_{name}",'','General',0,0,costMech,'',1)

        if costMech> 0 and dhwFuel in name:
            envelope.costBuilder(idf2, name,'','General',0,0,costMech,'',1)
        
        if costBatt > 0 and str(outerLayer) == 'nan':
            envelope.costBuilder(idf2, name,'' ,'General',0,0,(costBatt*max(heatingBattery,coolingBattery)),'',1)

        if costPV > 0 and str(outerLayer) == 'nan':
            envelope.costBuilder(idf2, name,'' ,'General',0,0,(costPV*PV_SIZE),'',1)

    # factor in appliances and lights cost to envelope
    with open(os.path.join(tempFolder, f"{BaseFileName}_IHGDict.json"), "r") as fp:
        ihg_dict = json.load(fp)
    
    for num_beds in unit_bedroom_dict.values():
        total_appliance_cost = ihg_dict[str(num_beds)]["applianceCost"]
        lights_cost = ihg_dict[str(num_beds)]["lightsCost"]
        envelope.costBuilder(idf2, 'APPLIANCES','','General',0,0,total_appliance_cost,'',1)
        envelope.costBuilder(idf2, 'LIGHTS','','General',0,0,lights_cost,'',1)

    schedules.TBschedules(idf2, unit_list)

    # CHECKPOINT: before annual simulation starts
    checkpoint(simulation_mgr)

    # save and return the resulting idf
    idf2.saveas(testingFile_BA)
    idf = IDF(testingFile_BA, epwFile)
    return idf


def process_annual_simulation_output(si: SimInputs, case_id: int, simulation_mgr=None):
    """Collects intermediate information and exports it for easier access in annual simulation."""

    # infer case run details
    runList = si.run_list_df
    runCount = case_id
    studyFolder = si.study_folder
    batchFolder = si.batch_folder
    BaseFileName = f"{si.batch_name}_{runList['CASE_NAME'][runCount]}"
    
    # load the results
    annual_sim_temp_results = os.path.join(batchFolder, f"{BaseFileName}_BAout.csv")
    hourly = pd.read_csv(annual_sim_temp_results)

    # combine columns
    hourly.rename(columns = {'Date/Time':'DateTime'}, inplace = True)
    hourly[['Date2','Time']] = hourly.DateTime.str.split(expand=True)
    hourly['Date'] = hourly['Date2'].map(str)
    hourly['Time'] = (pd.to_numeric(hourly['Time'].str.split(':').str[0])-1).astype(str).apply(lambda x: f'0{x}' if len(x)==1 else x) + hourly['Time'].str[2:]
    hourly['DateTime'] = hourly['Date'] + ' ' + hourly['Time']
    hourly['DateTime'] = pd.to_datetime(hourly['DateTime'], format="%m/%d %H:%M:%S", exact=True)

    # drop the warmup
    endWarmup = hourly[hourly['DateTime'] == '1900-01-01 00:00:00'].index[0]
    dropWarmup = [*range(0, endWarmup,1)]
    hourly = hourly.drop(index = dropWarmup)
    hourly = hourly.reset_index()

    # export results
    hourly.to_csv(os.path.join(batchFolder, f"{BaseFileName}_BAHourly.csv"))

    # CHECKPOINT: annual sim results processed
    checkpoint(simulation_mgr)


def batch_simulation(si: SimInputs, idfs, label: str, simulation_mgr=None):
    """Uses eppy batch run to perform resilience simulation"""
    runs = []
    for i, idf in enumerate(idfs):
        if idf is not None:
            # recover case name
            batch_name = si.batch_name
            case_name = si.run_list_df["CASE_NAME"][i]

            # recover energyplus version number
            idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
            idfversion.extend([0] * (3 - len(idfversion)))
            idfversionstr = '-'.join([str(item) for item in idfversion])

            # create kwargs dictionary
            options = {"readvars": True,
                       "output_prefix": f"{batch_name}_{case_name}_{label}",
                       "ep_version":idfversionstr}
            
            # prepare the run
            runs.append([idf, options])
    
    # run the simulation
    try:
        runIDFs([x for x in runs], processors=si.num_procs)
    except EnergyPlusRunError:
        msg = "EnergyPlus ran into an unexpected error. Please check .err files in the batch \
               folder and contact Phius if necessary."
        if simulation_mgr:
            simulation_mgr.raise_exception(msg)


    # CHECKPOINT: all runlist entries done simulating
    for _ in range(len(idfs)): checkpoint(simulation_mgr)


def compute_adorb_costs(si: SimInputs, case_id: int, simulation_mgr=None):
    """Prepare embodied carbon costs and other various inputs to compute adorb costs."""

    # infer run information
    runList = si.run_list_df
    runCount = case_id
    case_name = runList["CASE_NAME"][runCount]
    batchFolder = si.batch_folder
    BaseFileName = f"{si.batch_name}_{case_name}"
    databaseDir = si.database_dir

    # get explicit information from run list
    duration = int(runList['ANALYSIS_DURATION'][runCount])
    elecPrice = float(runList['ELEC_PRICE_[$/kWh]'][runCount])
    elec_sellback_price = float(runList['SELLBACK_PRICE_[$/kWh]'][runCount])
    natGasPresent = runList["NATURAL_GAS"][runCount]
    gasPrice = runList['GAS_PRICE_[$/THERM]'][runCount]
    annualBaseGas = float(runList["ANNUAL_GAS_CHARGE"][runCount])
    annualBaseElec = float(runList["ANNUAL_ELEC_CHARGE"][runCount])
    gridRegion = runList['GRID_REGION'][runCount]
    perfCarbonMeasures = str(runList["PERF_CARBON_MEASURES"][runCount])
    perfCarbonMeasures = perfCarbonMeasures.split(", ") if perfCarbonMeasures != "nan" else []
    nonPerfCarbonMeasures = str(runList["NON_PERF_CARBON_MEASURES"][runCount])
    nonPerfCarbonMeasures = nonPerfCarbonMeasures.split(", ") if nonPerfCarbonMeasures != "nan" else []
    carbonMeasures = perfCarbonMeasures + nonPerfCarbonMeasures
    appliance_list = str(runList['APPLIANCE_LIST'][runCount]).split(', ')
    case_country = runList['ENVELOPE_COUNTRY'][runCount]

    # gather files to use
    ba_htm_path = os.path.join(batchFolder, f"{BaseFileName}_BAtbl.htm")
    ba_hourly_path = os.path.join(batchFolder, f"{BaseFileName}_BAHourly.csv")
    ba_mtr_path = os.path.join(batchFolder, f"{BaseFileName}_BAmtr.csv")
    if (not os.path.isfile(ba_htm_path) or
        not os.path.isfile(ba_hourly_path) or 
        not os.path.isfile(ba_mtr_path)):
        print("WARNING: Could not locate all outputs from annual simulation.")
        return

    # load tables for lookup later
    construction_cost_est_table = fasthtml.tablebyname(open(ba_htm_path, "r") , "Construction Cost Estimate Summary")
    cost_line_item_detail_table = fasthtml.tablebyname(open(ba_htm_path, "r") , "Cost Line Item Details")
    annual_peak_values_table = fasthtml.tablebyname(open(ba_htm_path, "r") , "Annual and Peak Values - Electricity")

    # load info for annual electric and gas
    hourly = pd.read_csv(ba_hourly_path)
    monthlyMTR = pd.read_csv(ba_mtr_path)
    
    # compute annual electric consumption and CO2 emissions
    annualElec = ((hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum()*0.0000002778*elecPrice)-
                    (hourly['Whole Building:Facility Total Surplus Electricity Energy [J](Hourly)'].sum()*0.0000002778*elec_sellback_price)
                    +annualBaseElec)
    MWH = hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)']*0.0000000002778
    CO2_Elec_List = []
    for filename in sorted(os.listdir(os.path.join(databaseDir, 'CambiumFactors'))):
        if filename.endswith('.csv'):
            hourlyBAEmissions = pd.read_csv(os.path.join(databaseDir, 'CambiumFactors', filename))
            emissions = hourlyBAEmissions[str(gridRegion)]
            CO2_Elec = sum(MWH*emissions)
            CO2_Elec_List.append((CO2_Elec))
    annualCO2Elec = CO2_Elec_List    

    # compute annual gas consumption and CO2 emissions
    if natGasPresent == 1:
        monthlyMTR = monthlyMTR.drop(index=[0,1,2,3,4,5,6,7])
        annualGas = (((sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*gasPrice)+annualBaseGas)
        annualCO2Gas = (sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*12.7
    else:
        annualCO2Gas = annualGas = 0

    # compute carbon measure cost by year
    p_carbonDatabase = pd.read_csv(os.path.join(databaseDir, 'Carbon Correction Database.csv'))
    np_carbonDatabase = pd.read_csv(os.path.join(databaseDir, "Nonperformance Carbon Correction Database.csv"))
    carbonDatabase = pd.concat([p_carbonDatabase, np_carbonDatabase], ignore_index=True)
    countryEmissionsDatabase = pd.read_csv(os.path.join(databaseDir, 'Country Emission Database.csv'))
    firstCost = [float(construction_cost_est_table[1][9][2]),0]
    carbonMeasureCost, emCO2 = [], []

    # TODO: CLEAN UP LOOPS
    for measure in range(carbonDatabase.shape[0]):
        if carbonDatabase['Name'][measure] in carbonMeasures:
            carbonMeasureCost.append([carbonDatabase['Cost'][measure], carbonDatabase['Year'][measure]])
    carbonMeasureCost.append(firstCost)

    efUSA = countryEmissionsDatabase['EF [kg/$]'][0] # 0 for US, TODO: CHANGE TO USE COUNTRY INDEX
    for measure in range(carbonDatabase.shape[0]):
        if carbonDatabase['Name'][measure] in carbonMeasures:
            for country in range(countryEmissionsDatabase.shape[0]):
                if str(countryEmissionsDatabase['COUNTRY'][country]) == str(carbonDatabase['Country'][1]):
                    ef = countryEmissionsDatabase['EF [kg/$]'][country]
            emCO2.append([(carbonDatabase['Cost'][measure]*ef*(1-carbonDatabase['Labor Fraction'][measure])) + 
                            ((carbonDatabase['Cost'][measure]*efUSA*(carbonDatabase['Labor Fraction'][measure]))), carbonDatabase['Year'][measure]])
            # Labor fraction should be subtracted out and have USA EF applied

    for country in range(countryEmissionsDatabase.shape[0]):
        if str(countryEmissionsDatabase['COUNTRY'][country]) == str(runList['ENVELOPE_COUNTRY'][runCount]):
            efENV = countryEmissionsDatabase['EF [kg/$]'][country]
            emCO2first = ((firstCost[0] * (1-runList['ENVELOPE_LABOR_FRACTION'][runCount]) * efENV) + 
                (firstCost[0] * (runList['ENVELOPE_LABOR_FRACTION'][runCount]) * efUSA))
            emCO2firstCost = [emCO2first,0]
    emCO2.append(emCO2firstCost)

    # compute direct maintenance and embodied C02 for appliances
    dirMR = carbonMeasureCost
    constructionList = pd.read_csv(si.construction_db)
    constructionList['Name'] = constructionList['Name'].apply(lambda x: x.lower() if isinstance(x, str) else x)
    constructionList = constructionList.set_index("Name")
    countryEmissionsDatabase = countryEmissionsDatabase.set_index("COUNTRY")
    price_of_carbon = 0.25 # units: $/kg according to spec
    # TODO: AVOID HARDCODING CARBON MULTIPLE TIMES

    # define routine to compute the embodied CO2 and direct maintenance costs for ADORB
    def add_item_to_adorb_inputs(name, cost=None):
        emissions_factor = countryEmissionsDatabase.loc[case_country, 'EF [kg/$]']
        try:
            # cross-reference with construction list if item exists
            labor_fraction = constructionList.loc[name, "Labor_Fraction"]
            lifetime = int(constructionList.loc[name, "Lifetime"])
            if cost==None: cost = constructionList.loc[name, "Mechanical Cost"]
        except KeyError:
            print(f"WARNING: Could not find \"{name}\" in construction database.")
            return
        embodied_carbon_calc = (cost * (1 - labor_fraction)) * (emissions_factor * price_of_carbon)
        
        # add cost anytime item needs installed or replaced
        if lifetime != 0:
            for year in range(0, duration, lifetime):
                dirMR.append([cost, year])
                emCO2.append([embodied_carbon_calc, year])
        else:
            dirMR.append([cost, 0])
            emCO2.append([embodied_carbon_calc, 0])
    

    # extract cost line item subtotals
    cost_line_df = pd.DataFrame(cost_line_item_detail_table[1][1:],
                                columns=cost_line_item_detail_table[1][0]).iloc[:-1] # drop the last summation row

    # compute emCO2 and dirMR per non-zero line item
    cost_line_df_subgroup = cost_line_df[cost_line_df["Quantity."] > 0]
    for _, row in cost_line_df_subgroup.iterrows():

        # extract basic information
        item_name = row["Item Name"].lower()
        item_cost = row["SubTotal $"]

        # strip any mechanical labels if neccessary
        if item_name[:5] == "mech_": item_name = item_name[5:]

        # handle appliance breakdown after loop
        if item_name in ["appliances", "lights"] or item_name.startswith("air sealing"):
            continue
        
        # for all normal entries compute and add to emCO2 and dirMR list
        else:
            add_item_to_adorb_inputs(item_name, item_cost)
    
    # compute emCO2 and dirMR per each appliance/lights 
    for appliance_name in appliance_list:
        add_item_to_adorb_inputs(appliance_name.lower())

    # retrieve peak electric from table
    eTrans = float(annual_peak_values_table[1][1][4])

    # compute adorb cost
    adorb_results_location = si.results_folder
    adorb_graphs_location = si.graphs_folder
    adorb.adorb(BaseFileName, adorb_results_location, adorb_graphs_location,
                duration, annualElec, annualGas, annualCO2Elec, annualCO2Gas,
                dirMR, emCO2, eTrans, si.graphs_enabled)

    # CHECKPOINT: adorb calculation finished
    checkpoint(simulation_mgr)


def collect_individual_simulation_results(si: SimInputs, case_id: int, simulation_mgr=None):
    """Collect all output files from simulation and packs them into one report."""
    
    # infer run information
    runList = si.run_list_df
    runCount = case_id
    case_name = runList["CASE_NAME"][runCount]
    batchFolder = si.batch_folder
    tempFolder = si.temp_folder
    resultsFolder = si.results_folder
    BaseFileName = f"{si.batch_name}_{case_name}"

    # find all relevant files for this run
    br_htm_path = os.path.join(batchFolder, f"{BaseFileName}_BRtbl.htm")
    br_hourly_heat_path = os.path.join(batchFolder, f"{BaseFileName}_BRHourlyHeat.csv")
    br_hourly_cool_path = os.path.join(batchFolder, f"{BaseFileName}_BRHourlyCool.csv")
    ba_htm_path = os.path.join(batchFolder, f"{BaseFileName}_BAtbl.htm")
    ba_hourly_path = os.path.join(batchFolder, f"{BaseFileName}_BAHourly.csv")
    ba_mtr_path = os.path.join(batchFolder, f"{BaseFileName}_BAmtr.csv")
    adorb_results_path = os.path.join(resultsFolder, f"{BaseFileName}_ADORBresults.csv")
    unit_list_path = os.path.join(tempFolder, f"{BaseFileName}_UnitBedrooms.json")

    # info from BR htm tables
    try:
        heating_set_hours_table = fasthtml.tablebyname(open(br_htm_path, "r"), "Heating SET Hours")
        time_bin_table = fasthtml.tablebyname(open(br_htm_path, "r"), "Time Bin Results")
        heating_index_hours_table = fasthtml.tablebyname(open(br_htm_path, "r"), "Heat Index Hours")
            
        HeatingSET = float(heating_set_hours_table[1][1][1])
        Below2C = float(time_bin_table[1][39][2])
        Caution = float(heating_index_hours_table[1][1][2])
        ExtremeCaution = float(heating_index_hours_table[1][1][3])
        Danger = float(heating_index_hours_table[1][1][4])
        ExtremeDanger = float(heating_index_hours_table[1][1][5])
    except FileNotFoundError:
        HeatingSET = Below2C = Caution = ExtremeCaution = Danger = ExtremeDanger = "ERROR"

    # info from hourly heat
    try:
        hourlyHeat = pd.read_csv(br_hourly_heat_path)

        # save heating battery value
        heatingBattery = (hourlyHeat['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778
        
        # compute min drybulb and dewpoint temp for heating outage
        MinDBOut = min(hourlyHeat['Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'].tolist())
        MinDPOut = min(hourlyHeat['Environment:Site Outdoor Air Dewpoint Temperature [C](Hourly)'].tolist())
    except FileNotFoundError:
        heatingBattery = MinDBOut = MinDPOut = "ERROR"
    
    # info from hourly cool
    try:
        with open(unit_list_path, "r") as fp:
            unit_bedroom_dict = json.load(fp)
        
        hourlyCool = pd.read_csv(br_hourly_cool_path)

        # save cooling battery value
        coolingBattery = (hourlyCool['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum())*0.0000002778
        
        # compute total mora days
        mora_days_units = {}
        for unit in unit_bedroom_dict.keys():
            RH = hourlyCool[(str(unit).upper()+ ':Zone Air Relative Humidity [%](Hourly)')].tolist()
            Temp = hourlyCool[(str(unit).upper()+ ':Zone Air Temperature [C](Hourly)')].tolist()

            RHdays = [RH[x:x+24] for x in range(0, len(RH), 24)]
            TEMPdays = [Temp[x:x+24] for x in range(0, len(Temp), 24)]

            # TODO: ALL LISTS BELOW ARE UNUSED ONCE BUILT
            avgRH = []
            avgTemp = []
            moraDays = []
            moraPF = []
            moraTotalDays = 0
            for day in range(7):
                avgRH.append(mean(RHdays[day]))
                avgTemp.append(mean(TEMPdays[day]))
                moraDays.append((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2))
                moraPF.append(mean(TEMPdays[day])-((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2)))
                if (mean(TEMPdays[day])-((49.593 - 48.580*np.array(mean(RHdays[day])*0.01) +25.887*np.array(mean(RHdays[day])*0.01)**2))) > 0:
                    moraTotalDays = moraTotalDays+1
            mora_days_units[str(unit)] = moraTotalDays # TODO: ENSURE THAT UNIT IS A UNIQUE NAME
            vanos_col = str(unit).upper()+ '_VANOS:Schedule Value [](Hourly)'
            print(vanos_col)
            vanosTotalHours = sum(hourlyCool[vanos_col].tolist()) if vanos_col in hourlyCool.columns else 0
        
        # compute max drybulb and dewpoint temp for cooling outage
        MaxDBOut = max(hourlyCool['Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'].tolist())
        MaxDPOut = max(hourlyCool['Environment:Site Outdoor Air Dewpoint Temperature [C](Hourly)'].tolist())
    except FileNotFoundError:
        coolingBattery = moraTotalDays = MaxDBOut = MaxDPOut = "ERROR"

    # info from BA htm tables
    construction_df = pd.read_csv(si.construction_db, index_col="Name")
    construction_df.index = construction_df.index.str.upper()
    item_types = ["Exterior Wall", "Roof", "Exterior Floor", "Window", "Exterior Door"]
    other_items = ["AIR SEALING", "MECH", "DHW", "APPLIANCES", "PV COST", "BATTERY COST"]
    try:
        site_source_energy_table = fasthtml.tablebyname(open(ba_htm_path, "r"), "Site and Source Energy")
        annual_peak_values_table = fasthtml.tablebyname(open(ba_htm_path, "r"), "Annual and Peak Values - Electricity")
        construction_cost_est_table = fasthtml.tablebyname(open(ba_htm_path, "r"), "Construction Cost Estimate Summary")
        cost_line_item_detail_table = fasthtml.tablebyname(open(ba_htm_path, "r"), "Cost Line Item Details")
                    
        eui = float(site_source_energy_table[1][1][2])
        peakElec = float(annual_peak_values_table[1][1][4])
        firstCost = 0
        item_cost_dict = {key:0 for key in item_types+other_items}
        
        if "BASE" not in case_name:
            firstCost = float(construction_cost_est_table[1][9][2])
            for row in range(1, len(cost_line_item_detail_table[1])):
                item_name = cost_line_item_detail_table[1][row][2]
                item_cost = cost_line_item_detail_table[1][row][6]

                for key in other_items:
                    if item_name.startswith(key):
                        item_cost_dict[key] = item_cost
                        break
                else:
                    if item_name in construction_df.index:
                        item_type = construction_df.loc[item_name, "Type"]
                        try:
                            item_cost_dict[item_type] = item_cost_dict[item_type] + item_cost
                        except KeyError: pass

    except FileNotFoundError:
        eui = peakElec = firstCost = "ERROR"
        item_cost_dict = {item:"ERROR" for item in item_types}


    # info from BA hourly dataset
    try:
        hourly = pd.read_csv(ba_hourly_path)
        elecPrice = float(runList['ELEC_PRICE_[$/kWh]'][runCount])
        annualBaseElec = float(runList["ANNUAL_ELEC_CHARGE"][runCount])
        elec_sellback_price = float(runList['SELLBACK_PRICE_[$/kWh]'][runCount])
        annualElec = ((hourly['Whole Building:Facility Total Purchased Electricity Energy [J](Hourly)'].sum()*0.0000002778*elecPrice)-
                        (hourly['Whole Building:Facility Total Surplus Electricity Energy [J](Hourly)'].sum()*0.0000002778*elec_sellback_price)
                        +annualBaseElec)
    except FileNotFoundError:
        annualElec = "ERROR"

    # info from BA mtr dataset
    try:
        monthlyMTR = pd.read_csv(ba_mtr_path)
        natGasPresent = runList['NATURAL_GAS'][runCount]
        gasPrice = runList['GAS_PRICE_[$/THERM]'][runCount]
        annualBaseGas = float(runList["ANNUAL_GAS_CHARGE"][runCount])
        if natGasPresent == 1:
            monthlyMTR = monthlyMTR.drop(index=[0,1,2,3,4,5,6,7])
            annualGas = ((sum(monthlyMTR['NaturalGas:Facility [J](Monthly) ']*9.478169879E-9))*gasPrice)+(annualBaseGas)
        else:
            annualGas = 0
    except FileNotFoundError:
        annualGas = "ERROR"
    
    try:
        adorb_results_df = pd.read_csv(adorb_results_path)
        pv_dirEn_tot = adorb_results_df['pv_dirEn'].sum()
        pv_dirMR_tot = adorb_results_df['pv_dirMR'].sum()
        pv_opCO2_tot = adorb_results_df['pv_opCO2'].sum()
        pv_emCO2_tot = adorb_results_df['pv_emCO2'].sum()
        pv_eTrans_tot = adorb_results_df['pv_eTrans'].sum()
        adorbCost = pv_dirEn_tot + pv_dirMR_tot + pv_opCO2_tot + pv_emCO2_tot + pv_eTrans_tot
    except FileNotFoundError:
        adorbCost = pv_dirEn_tot = pv_dirMR_tot = pv_opCO2_tot = pv_emCO2_tot = pv_eTrans_tot = "ERROR"
    
    # collect results into dictionary
    results_dict = {
        "Run Name":case_name,
        "SET ≤ 12.2°C Hours (F)":HeatingSET,
        "Hours < 2°C [hr]":Below2C,
        "Hours Above Vanos Threshold [hr]":vanosTotalHours,
        "Total Deadly Days":moraTotalDays,
        "Min outdoor DB [°C]":MinDBOut,
        "Min outdoor DP [°C]":MinDPOut,
        "Max outdoor DB [°C]":MaxDBOut,
        "Max outdoor DP [°C]":MaxDPOut,
        "Caution (> 26.7, ≤ 32.2°C) [hr]":Caution,
        "Extreme Caution (> 32.2, ≤ 39.4°C) [hr]":ExtremeCaution,
        "Danger (> 39.4, ≤ 51.7°C) [hr]":Danger,
        "Extreme Danger (> 51.7°C) [hr]":ExtremeDanger,
        "EUI":eui,
        "Peak Electric Demand [W]":peakElec,
        "Heating Battery Size [kWh]":heatingBattery, 
        "Cooling Battery Size [kWh]":coolingBattery,
        "First Year Electric Cost [$]" : annualElec,
        "First Year Gas Cost [$]":annualGas,
        "First Cost [$]":firstCost,
        "Wall Cost [$]":item_cost_dict["Exterior Wall"],
        "Roof Cost [$]":item_cost_dict["Roof"],
        "Floor Cost [$]":item_cost_dict["Exterior Floor"],
        "Window Cost [$]":item_cost_dict["Window"],
        "Door Cost [$]":item_cost_dict["Exterior Door"],
        "Air Sealing Cost [$]":item_cost_dict["AIR SEALING"],
        "Mechanical Cost [$]":item_cost_dict["MECH"],
        "Water Heater Cost [$]":item_cost_dict["DHW"],
        "Appliances Cost [$]":item_cost_dict["APPLIANCES"],
        "PV Cost [$]":item_cost_dict["PV COST"],
        "Battery Cost [$]":item_cost_dict["BATTERY COST"],
        "Total ADORB Cost [$]":adorbCost,
        "pv_dirEn_tot":pv_dirEn_tot,
        "pv_dirMR_tot":pv_dirMR_tot,
        "pv_opCO2_tot":pv_opCO2_tot,
        "pv_emCO2_tot":pv_emCO2_tot,
        "pv_eTrans_tot":pv_eTrans_tot
    }
    
    # CHECKPOINT: results collected
    checkpoint(simulation_mgr)

    # export results and return file names
    results_df = pd.DataFrame(results_dict, index=[0])
    result_file_name = os.path.join(resultsFolder, f"{BaseFileName}_ResultsTable.csv")
    results_df.to_csv(result_file_name)
    return result_file_name


def collect_all_results(si: SimInputs, file_list, simulation_mgr=None):
    # collect every set of results and combine into one file
    filtered_file_list = [x for x in file_list if x is not None]
    df = pd.concat(map(pd.read_csv, filtered_file_list), ignore_index=True)
    df.to_csv(os.path.join(si.results_folder, f"{si.batch_name}_ResultsTable.csv"))

    # CHECKPOINT: all results collected
    for _ in range(len(file_list)): checkpoint(simulation_mgr)


def generate_graphs(si: SimInputs, case_id: int, simulation_mgr=None):
    """If designated, create graphs and visualizations of results."""
    # get basic information from simulation inputs
    caseName = si.run_list_df["CASE_NAME"][case_id]
    studyFolder = si.study_folder
    batchFolder = si.batch_folder
    tempFolder = si.temp_folder
    graphsFolder = si.graphs_folder
    BaseFileName = f"{si.batch_name}_{caseName}"

    # bring in datasets
    hourlyHeat = pd.read_csv(os.path.join(batchFolder, f"{BaseFileName}_BRHourlyHeat.csv"))
    hourlyCool = pd.read_csv(os.path.join(batchFolder, f"{BaseFileName}_BRHourlyCool.csv"))
    hourlyHeat['DateTime'] = pd.to_datetime(hourlyHeat['DateTime'], format="%Y-%m-%d %H:%M:%S", exact=True)
    hourlyCool['DateTime'] = pd.to_datetime(hourlyCool['DateTime'], format="%Y-%m-%d %H:%M:%S", exact=True)

    # get number of zones
    with open(os.path.join(tempFolder, f"{BaseFileName}_UnitBedrooms.json"), "r") as fp:
        unit_bedroom_dict = json.load(fp)
        unit_list = [unit for unit in unit_bedroom_dict.keys()]
    
    # construct lambda getter functions for column labels
    get_zone_air_temp_label = lambda x : f"{x.upper()}:Zone Air Temperature [C](Hourly)"
    get_zone_rel_hum_label = lambda x : f"{x.upper()}:Zone Air Relative Humidity [%](Hourly)"
    get_zone_std_eff_temp_label = lambda x : f"{x.upper()} OCCUPANTS:Zone Thermal Comfort Pierce Model Standard Effective Temperature [C](Hourly)"
    get_zone_heat_idx_label = lambda x : f"{x.upper()}:Zone Heat Index [C](Hourly)"
    get_zone_dry_bulb_label = lambda x : f"{x} Zone Dry Bulb [C]"
    get_zone_rh_label = lambda x : f"{x} Zone RH"
    get_zone_set_label = lambda x : f"{x} Zone SET"

    # compute the critical units (max and min average temperature)
    heating_outage_unit_results = {}
    cooling_outage_unit_results = {}
    for unit in unit_list:
        heating_outage_unit_results[unit] = mean(hourlyHeat[get_zone_air_temp_label(unit)])
        cooling_outage_unit_results[unit] = mean(hourlyCool[get_zone_air_temp_label(unit)])

    heating_sorted_keys = sorted(heating_outage_unit_results.keys(),key=lambda x: heating_outage_unit_results[x])
    cooling_sorted_keys = sorted(cooling_outage_unit_results.keys(),key=lambda x: cooling_outage_unit_results[x])

    heating_min_unit, heating_max_unit = heating_sorted_keys[0], heating_sorted_keys[-1]
    cooling_min_unit, cooling_max_unit = cooling_sorted_keys[0], cooling_sorted_keys[-1]

    # save columns for code readability
    heating_min_unit_air_temp = hourlyHeat[get_zone_air_temp_label(heating_min_unit)]
    heating_max_unit_air_temp = hourlyHeat[get_zone_air_temp_label(heating_max_unit)]
    heating_min_unit_rel_hum = hourlyHeat[get_zone_rel_hum_label(heating_min_unit)]
    heating_max_unit_rel_hum = hourlyHeat[get_zone_rel_hum_label(heating_max_unit)]
    heating_min_unit_std_eff_temp = hourlyHeat[get_zone_std_eff_temp_label(heating_min_unit)]
    heating_max_unit_std_eff_temp = hourlyHeat[get_zone_std_eff_temp_label(heating_max_unit)]
    heating_outdoor_air_temp = hourlyHeat["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]
    
    # create the figure and axes for heating graphs  
    fig = plt.figure(layout='constrained', figsize=(10, 10))
    fig.suptitle(f"{caseName}_Heating Outage Resilience", fontsize='x-large')
    ax = fig.subplot_mosaic([['temperature'],['rh'],['SET']])
    
    # plot graphs for hourly heat 
    x = hourlyHeat["DateTime"]
    ax['temperature'].plot(x,heating_outdoor_air_temp, label="Site Dry Bulb [C]", linestyle='dashed')

    # plot data for minimum heating unit
    color1 = "black" if heating_min_unit==heating_max_unit else "tab:orange"
    ax['temperature'].plot(x,heating_min_unit_air_temp, 
                            label=get_zone_dry_bulb_label(heating_min_unit), 
                            color=color1, 
                            linewidth=2)
    ax['rh'].plot(x,heating_min_unit_rel_hum, 
                    label=get_zone_rh_label(heating_min_unit), 
                    color=color1, 
                    linewidth=2)
    ax['SET'].plot(x,heating_min_unit_std_eff_temp, 
                    label=get_zone_set_label(heating_min_unit),
                    color=color1,
                    linewidth=2)

    # plot data for maximum heating unit (if more than one unit in the building)
    if heating_min_unit!=heating_max_unit:
        color2 = "tab:green"
        ax['temperature'].plot(x,heating_max_unit_air_temp,
                               label=get_zone_dry_bulb_label(heating_max_unit),
                               color=color2,
                               linewidth=2)
        ax['rh'].plot(x,heating_max_unit_rel_hum, 
                      label=get_zone_rh_label(heating_max_unit),
                      color=color2,
                      linewidth=2,
                      linestyle='dashdot')
        ax['SET'].plot(x,heating_max_unit_std_eff_temp,
                       label=get_zone_set_label(heating_max_unit),
                       color=color2,
                       linewidth=2)
        
    # set the y limit to capture all data comfortably
    ax['temperature'].set_ylim(min(min(heating_outdoor_air_temp), min(heating_min_unit_air_temp))-5,
                               max(max(heating_outdoor_air_temp), max(heating_max_unit_air_temp))+5)
    ax['rh'].set_ylim(0,100)
    ax['SET'].set_ylim(min(heating_min_unit_std_eff_temp)-5,
                       max(heating_max_unit_std_eff_temp)+5)
    
    # label axes
    ax['temperature'].set_ylabel('Temperature [C]')
    ax['temperature'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['temperature'].grid(True)
    
    ax['rh'].set_ylabel('Relative Humidity [%]')
    ax['rh'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['rh'].grid(True)

    ax['SET'].set_xlabel('Date')
    ax['SET'].set_ylabel('Standard Effective Temperature [°C]')
    ax['SET'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['SET'].grid(True)
    ax['SET'].axhline(12.2, color='crimson', linestyle='dashed')

    # export and clear
    heatingGraphFile = os.path.join(graphsFolder, BaseFileName + "_Heating Outage Resilience Graphs.png")
    fig.savefig(heatingGraphFile, dpi=300)
    fig.clf()

    # create figure and axes for cooling graphs
    fig.suptitle(f"{caseName}_Cooling Outage Resilience", fontsize='x-large')
    ax = fig.subplot_mosaic([['temperature'],['rh'],['HI']])

    # save columns for readability
    cooling_min_unit_air_temp = hourlyCool[get_zone_air_temp_label(cooling_min_unit)]
    cooling_max_unit_air_temp = hourlyCool[get_zone_air_temp_label(cooling_max_unit)]
    cooling_min_unit_rel_hum = hourlyCool[get_zone_rel_hum_label(cooling_min_unit)]
    cooling_max_unit_rel_hum = hourlyCool[get_zone_rel_hum_label(cooling_max_unit)]
    cooling_min_unit_heat_idx = hourlyCool[get_zone_heat_idx_label(cooling_min_unit)]
    cooling_max_unit_heat_idx = hourlyCool[get_zone_heat_idx_label(cooling_max_unit)]
    cooling_outdoor_air_temp = hourlyCool["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]
    
    # plot graphs for hourly heat 
    x = hourlyCool["DateTime"]
    ax['temperature'].plot(x,cooling_outdoor_air_temp, label="Site Dry Bulb [C]", linestyle='dashed')
    
    # plot data for minimum cooling unit
    color1 = "black" if cooling_min_unit==cooling_max_unit else "tab:orange"
    ax['temperature'].plot(x,cooling_min_unit_air_temp, 
                            label=get_zone_dry_bulb_label(cooling_min_unit), 
                            color=color1, 
                            linewidth=2)
    ax['rh'].plot(x,cooling_min_unit_rel_hum, 
                    label=get_zone_rh_label(cooling_min_unit), 
                    color=color1, 
                    linewidth=2)
    ax['HI'].plot(x,cooling_min_unit_heat_idx, 
                    label=get_zone_heat_idx_label(cooling_min_unit),
                    color=color1,
                    linewidth=2)

    # plot data for maximum cooling unit (if more than one unit in the building)
    if cooling_min_unit!=cooling_max_unit:
        color2 = "tab:green"
        ax['temperature'].plot(x,cooling_max_unit_air_temp,
                               label=get_zone_dry_bulb_label(cooling_max_unit),
                               color=color2,
                               linewidth=2)
        ax['rh'].plot(x,cooling_max_unit_rel_hum, 
                      label=get_zone_rh_label(cooling_max_unit),
                      color=color2,
                      linewidth=2,)
        ax['HI'].plot(x,cooling_max_unit_heat_idx,
                       label=get_zone_heat_idx_label(cooling_max_unit),
                       color=color2,
                       linewidth=2)

    # set the y limit to capture all data comfortably
    ax['temperature'].set_ylim(min(min(cooling_outdoor_air_temp), min(cooling_min_unit_air_temp))-5,
                               max(max(cooling_outdoor_air_temp), max(cooling_max_unit_air_temp))+5)
    ax['rh'].set_ylim(0,100)
    ax['HI'].set_ylim(min(cooling_min_unit_heat_idx)-5,
                      max(cooling_max_unit_heat_idx)+5)
    
    # label axes
    ax['temperature'].set_ylabel('Temperature [C]')
    ax['temperature'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['temperature'].grid(True)

    ax['rh'].set_ylabel('Relative Humidity [%]')
    ax['rh'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['rh'].grid(True)

    ax['HI'].set_xlabel('Date')
    ax['HI'].set_ylabel('Heat Index [°C]')
    ax['HI'].legend(ncol=2, loc='lower left', borderaxespad=0, fontsize='x-small')
    ax['HI'].grid(True)
    ax['HI'].axhline(26.7, color='seagreen', linestyle='dashed')
    ax['HI'].axhline(32.2, color='orange', linestyle='dashed')
    ax['HI'].axhline(39.4, color='crimson', linestyle='dashed')
    ax['HI'].axhline(51.7, color='darkmagenta', linestyle='dashed')

    # export and clear
    coolingGraphFile = os.path.join(graphsFolder, BaseFileName + "_Cooling Outage Resilience Graphs.png")
    fig.savefig(coolingGraphFile, dpi=300)
    fig.clf()


def cleanup_outputs(si: SimInputs):
    """If designated, remove files generated from energyplus (only keep aggregated results)."""
    # TODO: CLEANUP THE REST
    for path in os.listdir(si.temp_folder):
        os.remove(os.path.join(si.temp_folder, path))
    os.rmdir(si.temp_folder)

    # clean up the eplus output files if designated
    if si.del_files_enabled:
        for file in os.listdir(si.batch_folder):
            full_file_path = os.path.join(si.batch_folder, file)
            if os.path.isfile(full_file_path):
                os.remove(full_file_path)

def ranked_top_cases(results_path, num_top_cases=5):
    # read results into dataframe
    df = pd.read_csv(results_path)
    assert len(df)>0, "Results file does not contain any cases to review."

    # establish conditions for passing resilience
    condition_columns = ["Total Deadly Days_failBR", "Hours < 2°C [hr]_failBR", "SET ≤ 12.2°C Hours (F)_failBR"]
    df["Total Deadly Days_failBR"] = df["Total Deadly Days"].apply(lambda x: np.nan if x == "ERROR" else int(x)>0)
    df["Hours < 2°C [hr]_failBR"] = df["Hours < 2°C [hr]"].apply(lambda x: np.nan if x == "ERROR" else float(x)>0)
    df["SET ≤ 12.2°C Hours (F)_failBR"] = df["SET ≤ 12.2°C Hours (F)"].apply(lambda x: np.nan if x == "ERROR" else float(x)>216)
    df["Total ADORB Cost [$]_clean"] = df["Total ADORB Cost [$]"].apply(lambda x : np.nan if x == "ERROR" else float(x))

    # rounding to 2 decimals
    df['Total ADORB Cost [$]'] = df["Total ADORB Cost [$]"].apply(lambda x : f"{float(x):.2f}" if x != "ERROR" else x)
    df['First Cost [$]'] = df['First Cost [$]'].apply(lambda x : f"{float(x):.2f}" if x != "ERROR" else x)

    nan_check = df[condition_columns].isna().any(axis=1)
    bool_check = df[condition_columns].map(lambda x: isinstance(x, bool) and x==True).any(axis=1)
    df['Display Color'] = df.apply(lambda row: '#f7b5b5' if bool_check[row.name]
                                            else'#e3d8a1' if nan_check[row.name]  
                                            else None, axis=1)

    # sort by passing resilience and then by adorb cost
    df = df.sort_values(by=["Total Deadly Days_failBR",
                            "Hours < 2°C [hr]_failBR",
                            "SET ≤ 12.2°C Hours (F)_failBR",
                            "Total ADORB Cost [$]_clean"],
                        na_position="last",
                        ignore_index=True)
    
    # return the top sorted results
    if len(df) < num_top_cases:
        print(f"Results file contains less than {num_top_cases} rows. Only displaying {len(df)} rows.")
    return df.head(num_top_cases)
