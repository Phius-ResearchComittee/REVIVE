# 2024.02.06 by al
# unzips files

import os
import gzip
import shutil

model_folder = 'D:/ABCC/Base Model Correlation'
# schedule_folder = "C:/Users/amitc_crl/OneDrive/Mitchell_ANL-Starr_2023/Schedules/"
# models
os.chdir(model_folder)
item_list = os.listdir(model_folder)
for item in item_list:
    try:
        with gzip.open(item, 'rb') as file_in:
            with open((os.path.splitext(item)[0]), 'wb') as file_out:
                shutil.copyfileobj(file_in,file_out)
        # os.remove(item)
    except:
        print('ERROR: ' + str(os.path.splitext(item)[0]))

# # schedules
# os.chdir(schedule_folder)
# item_list = os.listdir(schedule_folder)
# for item in item_list:
#     try:
#         with gzip.open(item, 'rb') as file_in:
#             with open((os.path.splitext(item)[0]), 'wb') as file_out:
#                 shutil.copyfileobj(file_in,file_out)
#         # os.remove(item)
#     except:
#         print('ERROR: ' + str(os.path.splitext(item)[0]))
