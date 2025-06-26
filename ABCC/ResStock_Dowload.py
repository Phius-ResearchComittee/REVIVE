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
import os

try:
    base_link = 'https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock%2Fend-use-load-profiles-for-us-building-stock%2F2021%2Fresstock_tmy3_release_1%2Fbuilding_energy_models%2F/bldg'
    link_suffix = '-up00.osm.gz'
    model_folder = "D:/ABCC/Base Model Correlation"
    schedule_folder = "D:/ABCC"
except:
    print("ERROR: Please specify filename and url column name to download")
    sys.exit(0)


# 0000001
os.chdir(model_folder)

bldg_range = list(range(1,11,1))

urls = []

for bldg in bldg_range:
    padded_num = str(bldg).rjust(7, '0')
    url = (str(base_link) + str(padded_num) + str(link_suffix))
    urls.append(url)
    print(url)


# open csv file to read
def dowload(osm_url):
    try:
        print('downloading started')
        # wget.download(osm_url,out=model_folder) # downloading the file by sending the request to the URL
        urlretrieve(osm_url, str(osm_url.split('/')[-1]))
        # wget.download((osm_url.replace('.osm', '.csv').replace('building_energy_models', 'occupancy_schedules')),out=schedule_folder) # downloading the file by sending the request to the URL
        print("["+str(osm_url)+"] osm saved")
    except:
        print("["+str(osm_url)+"] osm not downloaded")

Parallel(n_jobs=8)(delayed(dowload)(osm_url) for osm_url in urls)
