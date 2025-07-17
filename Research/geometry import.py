import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF

idfName = "C:/EnergyPlusV9-5-0/ExampleFiles/MultiStory.idf"
iddName = "C:/EnergyPlusV9-5-0/Energy+.idd"

IDF.setiddname(iddName)

def importZonesFromGeometry(idfname):
    zone_name_list = []
    idf1 = IDF(idfName)

    for object in idf1.idfobjects['Zone']:
        zone_name_list.append(str(object.Name))

    return zone_name_list

zones = importZonesFromGeometry(idfName)

print(zones)