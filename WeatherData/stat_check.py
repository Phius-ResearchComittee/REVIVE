import os
import datetime
from datetime import datetime
source_dir = 'D:/Boston'

files = os.listdir(source_dir)
os.chdir(source_dir)




temp_dicts = []

temp_dict = {}
for file in files:
    
    if ".stat" in str(file):
        with open(file, 'r') as stat_file:
            lines = stat_file.readlines()
            for row in lines:
                word = 'Extreme Cold Week Period selected'
                if row.find(word) != -1:
                    row = row.split(': ')
                    average_cold = float(row[1].split(', ')[1].split('= ')[1].replace('°C', '')) + (float(row[1].split(', ')[2].split('=')[1].replace('°C', '').replace('|', '')))
                    
                    temp_dict[file] = average_cold



temp = min(temp_dict.values())
res = [key for key in temp_dict if temp_dict[key] == temp]

print("Coldest Year : " + str(res))
print(temp_dict[res[0]])
coldest_stat = res[0]
coldest_epw = res[0].replace(".stat", ".epw")

temp_dict = {}
for file in files:
    if ".stat" in str(file):

        with open(file, 'r') as stat_file:
            lines = stat_file.readlines()
            for row in lines:
                word = 'Extreme Hot Week Period selected'
                if row.find(word) != -1:
                    row = row.split(': ')
                    average_cold = float(row[1].split(', ')[1].split('= ')[1].replace('°C', '')) - (float(row[1].split(', ')[2].split('=')[1].replace('°C', '').replace('|', '')))
                    
                    temp_dict[file] = average_cold



temp = max(temp_dict.values())
res = [key for key in temp_dict if temp_dict[key] == temp]

print("Hottest Year : " + str(res))
print(temp_dict[res[0]])
hottest_epw = res[0].replace(".stat", ".epw")
hottest_stat = res[0]



for file in files:
    if 'TMY' in file:
        tmy_epw = file


for file in files:
    if coldest_stat in file:
        year = file.split('_')[-1].replace('.stat', '')
        with open(file, 'r') as stat_file:
            lines = stat_file.readlines()
            for row in lines:
                word = 'Extreme Cold Week Period selected'
                if row.find(word) != -1:
                    row = row.split(': ')
                    row = row[1].split(', ')
                    row = row[0].split(':')
                    cold_start = datetime.strptime(((str(row[0]) + ' ' + str(year)).replace(' ', '-').replace('--','-')), "%b-%d-%Y")
                    cold_end = datetime.strptime(((str(row[1]) + ' ' + str(year)).replace(' ', '-').replace('--','-')), "%b-%d-%Y")


for file in files:
    if hottest_stat in file:
        year = file.split('_')[-1].replace('.stat', '')
        with open(file, 'r') as stat_file:
            lines = stat_file.readlines()
            for row in lines:
                word = 'Extreme Hot Week Period selected'
                if row.find(word) != -1:
                    row = row.split(': ')
                    row = row[1].split(', ')
                    row = row[0].split(':')
                    hot_start = datetime.strptime(((str(row[0]) + ' ' + str(year)).replace(' ', '-').replace('--','-')), "%b-%d-%Y")
                    hot_end = datetime.strptime(((str(row[1]) + ' ' + str(year)).replace(' ', '-').replace('--','-')), "%b-%d-%Y")


                  
    
for file in files:
    if coldest_epw in file:
        with open(file, 'r') as epw_file:
            cold_period = []
            date = (str(cold_start.strftime(',%#m,%#d')) + ',1,') 
            length = 0   
            while True:
                next_line = epw_file.readline()
                if date in next_line:
                    cold_period.append(next_line.strip())
                    while length < 168:
                        print('cold period')
                        next_line = epw_file.readline()
                        cold_period.append(next_line.strip())
                        length = len(cold_period)
                        if length >168:
                            break
                if not next_line:
                    break
ele = cold_period

for file in files:
    if hottest_epw in file:
        with open(file, 'r') as epw_file:
            hot_period = []
            date = (str(hot_start.strftime(',%#m,%#d')) + ',1,') 
            length = 0   
            while True:
                next_line = epw_file.readline()
                if date in next_line:
                    hot_period.append(next_line.strip())
                    while length < 168:
                        print('hot period')
                        next_line = epw_file.readline()
                        hot_period.append(next_line.strip())
                        length = len(hot_period)
                        if length >168:
                            break
                if not next_line:
                    break
# ele = hot_period.pop()


with open(tmy_epw, 'r') as epw_file:
    # lines = epw_file.readlines()
    tmy_header = []
    date = (str(cold_start.strftime(',%#m,%#d')) + ',1,')    
    while True:
        print('header')
        next_line = epw_file.readline()
        tmy_header.append(next_line.strip())
        if date in next_line:
            break

ele = tmy_header.pop()

with open(file, 'r') as epw_file:
    tmy_middle = []
    date1 = (str(cold_end.strftime(',%#m,%#d')) + ',24,') 
    date2 = (str(hot_start.strftime(',%#m,%#d')) + ',1,') 
    while True:
        next_line = epw_file.readline()
        if date1 in next_line:
            # tmy_middle.append(next_line.strip())
            print(next_line)
            while True:
                print('middle')
                next_line = epw_file.readline()
                tmy_middle.append(next_line.strip())
                # print(next_line)

                if date2 in next_line:
                    break
        if not next_line:
            break
ele = tmy_middle.pop()

with open(file, 'r') as epw_file:
    tmy_tail = []
    date1 = (str(hot_end.strftime(',%#m,%#d')) + ',24,') 
    while True:
        next_line = epw_file.readline()
        if date1 in next_line:
            # tmy_tail.append(next_line.strip())
            print(next_line)
            while True:
                print('tail')
                next_line = epw_file.readline()
                tmy_tail.append(next_line.strip())
                # print(next_line)

                if not next_line:
                    break
        if not next_line:
            break
ele = tmy_tail.pop()

# cold first
tmy_header = tmy_header + cold_period + tmy_middle + hot_period + tmy_tail

# hot first
# tmy_header = tmy_header + hot_period + tmy_middle + cold_period + tmy_tail

# open file
with open('gfg.epw', 'w+') as f:
    
    # write elements of list
    for items in tmy_header:
        f.write('%s\n' %items)
f.close() 