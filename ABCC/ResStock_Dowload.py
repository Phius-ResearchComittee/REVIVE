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
    csvfilename = "D:/ABCC/550k_results_with_economics_allfuels_chars.csv/ABCC_resstock_download_short.csv"
    urlheader = "bldg_id"
    model_folder = "D:/ABCC"
    schedule_folder = "D:/ABCC"
except:
    print("ERROR: Please specify filename and url column name to download")
    sys.exit(0)

df = pd.read_excel(csvfilename)

urls = list(df['bldg_id'])

# open csv file to read
def dowload(osm_url):
    try:
        print('downloading started')
        wget.download(osm_url,out=model_folder) # downloading the file by sending the request to the URL
        # wget.download((osm_url.replace('.osm', '.csv').replace('building_energy_models', 'occupancy_schedules')),out=schedule_folder) # downloading the file by sending the request to the URL
        print("["+str(osm_url)+"] osm saved")
    except:
        print("["+str(osm_url)+"] osm not downloaded")

Parallel(n_jobs=8)(delayed(dowload)(osm_url) for osm_url in urls)
