import os

source_dir = 'D:/Boston'

files = os.listdir(source_dir)
os.chdir(source_dir)

rows = []

list_file = open("Boston.lst", "w")

for file in files:
    if ".epw" in str(file):
        newName = str(file.split('-')[-1])
        newName = str(newName.replace('AP.', 'AP'))
        os.rename(file, newName)

input("wait")

files = os.listdir(source_dir)

for file in files:
    if ".epw" in str(file):
        rows.append(str(source_dir) + "/" + str(file) + "                 " + str(source_dir) + "/" + str(file.replace('.epw', '.stat')) + "\n")

list_file.writelines(rows)

list_file.close()




