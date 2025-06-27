# 2024.02.06 by al
# unzips files

import os
import gzip
import shutil
from joblib import Parallel, delayed


model_folder = 'D:\ABCC\BMC2'
# schedule_folder = "C:/Users/amitc_crl/OneDrive/Mitchell_ANL-Starr_2023/Schedules/"
# models
os.chdir(model_folder)
item_list = os.listdir(model_folder)
# for item in item_list:

def unzip(item):
    try:
        with gzip.open(item, 'rb') as file_in:
            with open((os.path.splitext(item)[0]), 'wb') as file_out:
                shutil.copyfileobj(file_in,file_out)
        # os.remove(item)
    except:
        print('ERROR: ' + str(os.path.splitext(item)[0]))

Parallel(n_jobs=14)(delayed(unzip)(item) for item in item_list)
