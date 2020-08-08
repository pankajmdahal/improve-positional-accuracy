import pandas
import arcpy
import os
import sys  # for printing . :D

arcpy.env.overwriteOutput = True

level_count_dict = {}

buffer_increment = [20,40,60,80,100,120,140,160,180,200]

base_network = "input/railway_ln_connected.shp"
comparing_network = "input/NARN_LINE_03162018.shp"

base_network_f = "bnf"
comparing_network_f = "cnf"

memory_m1 = "C:/GIS/memorym1.shp"
memory_m2 = "C:/GIS/memorym2.shp"


arcpy.MakeFeatureLayer_management(base_network, base_network_f)
arcpy.MakeFeatureLayer_management(comparing_network, comparing_network_f)

for buffer in buffer_increment:
    arcpy.SelectLayerByAttribute_management(comparing_network_f, "NEW_SELECTION") #, '"FID" = 100000000000'), "INVERT")
    arcpy.Buffer_analysis(comparing_network_f, memory_m1, str(buffer) + " Feet")
    arcpy.Dissolve_management(memory_m1, memory_m2)
    arcpy.SelectLayerByLocation_management(base_network_f, "COMPLETELY_WITHIN", "in_memory/m2", "", "NEW_SELECTION")
    fids_list = [_row_[0] for _row_ in arcpy.da.SearchCursor(base_network_f, ['FID'])]
    level_count_dict[buffer] = len(fids_list)


