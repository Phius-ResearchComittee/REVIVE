# 2024.02.06 by al
# unzips files

import os
import gzip
import shutil
from zipfile import ZipFile
import pathlib

schedule_folder = "D:/ABCC/Base Model Correlation"


# GZ Files
# os.chdir(schedule_folder)
# item_list = os.listdir(schedule_folder)
# for item in item_list:
#     # try:
#         with gzip.open(item, 'rb') as file_in:
#             with open((os.path.splitext(item)[0]), 'wb') as file_out:
#                 print(os.path.splitext(item)[0])
#                 shutil.copyfileobj(file_in,file_out)
#         # os.remove(item)
#     # except:
#         # print('ERROR: ' + str(os.path.splitext(item)[0]))



# ZIP Files
os.chdir(schedule_folder)
item_list = os.listdir(schedule_folder)
for item in item_list:
       
    try:
        with ZipFile(item, 'r') as zObject:
            zObject.extractall(path=os.path.splitext(item)[0])
            # os.remove(item)
    except:
        print('ERROR: ' + str(os.path.splitext(item)[0]))


os.chdir(schedule_folder)
folder_list = os.listdir(schedule_folder)
folder_path = (os.path.realpath(schedule_folder))

for folder in folder_list:
    folder_contents = os.listdir(folder)
    bldg = str(folder.split('-')[0])
    for item in folder_contents:
        if '.csv' in item:
            os.rename((str(os.path.realpath(folder)) + '//' + str(item)), (str(os.path.realpath(folder)) + '\\' + str(item)).replace('schedules.csv', str(bldg) + '.csv'))
            shutil.copy((str(os.path.realpath(folder)) + '\\' + str(item)).replace('schedules.csv', str(bldg) + '.csv'), (str(folder_path) + '\\' + str(bldg) + '.csv'))