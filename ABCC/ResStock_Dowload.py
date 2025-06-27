# 2022.04.26 by jeannie
# updated 2024.02.06 by al
# reference1: https://gist.github.com/krisrak/2cd4230682997d399c33a1b24c266521
# reference2: https://likegeeks.com/downloading-files-using-python/
# Updated 2024.

import os
import wget
from joblib import Parallel, delayed

# Config
base_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_tmy3_release_1/building_energy_models/bldg'
           
link_suffix = '-up00.osm.gz'
model_folder = "D:/ABCC/BMC2" # add desired download loaction EX:A:/PHIUS/ABCC/Base Model Correlation
schedule_folder = "C:/test/schedule"   #add schedule folder

# Ensure folders exist
os.makedirs(model_folder, exist_ok=True)
os.makedirs(schedule_folder, exist_ok=True)

# Generate URLs
bldg_range = range(1, 550001)  # 0000001 to 0000010
urls = [
    f"{base_link}{str(bldg).rjust(7, '0')}{link_suffix}"
    for bldg in bldg_range
]

# Download function
def download(osm_url):
    try:
        print(f"Downloading: {osm_url}")
        wget.download(osm_url, out=model_folder)
        print(f"\nSaved: {osm_url}")
    except Exception as e:
        print(f"Failed to download {osm_url}: {e}")

# Parallel Download
Parallel(n_jobs=14)(delayed(download)(url) for url in urls)

