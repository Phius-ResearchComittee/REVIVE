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
    base_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_tmy3_release_1/building_energy_models/upgrade%3D0/bldg'
    link_suffix = '-up00.zip'
    model_folder = "D:/ABCC"
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
