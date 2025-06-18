# 2022.04.26 by jeannie
# updated 2024.02.06 by al
# reference1: https://gist.github.com/krisrak/2cd4230682997d399c33a1b24c266521
# reference2: https://likegeeks.com/downloading-files-using-python/
# Updated 2024.

import sys
import csv
import wget
import pandas as pd
from urllib.request import urlretrieve
from joblib import Parallel,delayed 


try:
    csvfilename = "D:/ABCC/550k_results_with_economics_allfuels_chars.csv/ABCC_resstock_download 55k sch.csv"
    urlheader = "bldg_id"
    model_folder = "D:/ABCC"
    schedule_folder = "D:/ABCC"
except:
    print("ERROR: Please specify filename and url column name to download")
    sys.exit(0)

# open csv file to read
with open(csvfilename, 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    for row_index,row in enumerate(csv_reader): #iterate on all rows in csv
        if row_index == 0: #find the urlheader to download in first row
            osm_url_col_num = None
            for col_index,col in enumerate(row):
                if col == urlheader:
                    osm_url_col_num = col_index
            if osm_url_col_num is None:
                print("ERROR: urlheader name not found")
                sys.exit(0)
            continue
        osm_urls = row[osm_url_col_num]
        try:
            print('downloading started')
            wget.download(osm_urls,out=model_folder) # downloading the file by sending the request to the URL
            # wget.download((osm_urls.replace('.osm', '.csv').replace('building_energy_models', 'occupancy_schedules')),out=schedule_folder) # downloading the file by sending the request to the URL
            print("["+str(row_index)+"] osm saved")
        except:
            print("["+str(row_index)+"] osm not downloaded")