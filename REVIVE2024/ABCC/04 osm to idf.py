# 2022.04.26 by jeannie
# reference1: https://unmethours.com/question/50707/how-to-export-osm-to-idf-with-the-command-line/
# reference2: https://nrel.github.io/OpenStudio-user-documentation/reference/command_line_interface/
# reference3: https://openstudio-sdk-documentation.s3.amazonaws.com/cpp/OpenStudio-3.3.0-doc/energyplus/html/classopenstudio_1_1energyplus_1_1_forward_translator.html#abc841f8b723b58e372729b534cff7942

import os
import openstudio

dir_name = "C:/Users/amitc_crl/OneDrive/Mitchell_ANL-Starr_2023/Models" # where osm files nested

for item in os.listdir(dir_name): # loop thru items in dir
    osm_name = os.path.join(dir_name,item) # osm file path .osm
    idf_name = osm_name.replace('.osm','.idf') # idf file path .idf
    # print(osm_name, idf_name) # in case to check if the paths are right
    # openstudio.energyplus.ForwardTranslator().translateModel(openstudio.osversion.VersionTranslator().loadModel(openstudio.path(osm_name)).get()).save(openstudio.path(idf_name), True) # brought from the reference
    translator = openstudio.osversion.VersionTranslator()
    model = translator.loadModel(osm_name)
    assert model.is_initialized()
    model = model.get()

    openstudio.energyplus.ForwardTranslator().translateModel(model).save((idf_name))







    # openstudio.energyplus.ForwardTranslator.translateModel(openstudio.osversion.VersionTranslator().loadModel(openstudio.path(osm_name)).get())

    # print("completed")