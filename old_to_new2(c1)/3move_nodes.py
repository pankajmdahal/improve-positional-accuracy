# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
from parameters import *
import random
import numpy as np
import os
import multiprocessing
from functools import partial


#def main():
# retrieve values
all_ids_dist_dict = {}
arcpy.env.outputMFlag = "Disabled"
arcpy.env.outputZFlag = "Disabled"
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Network")

empty = "C:/gis/empty.shp"
empty_memory = "in_memory/e1"
arcpy.CopyFeatures_management(empty, empty_memory)

# arcpy.BuildNetwork_na(B1_ND)
filenames_list = os.listdir("./intermediate/")
for filename in filenames_list:
    var_name = filename.split(".")[0]
    print ((var_name + " = np.load('./intermediate/" + filename + "')"))
    exec (var_name + " = np.load('./intermediate/" + filename + "').item()") in globals()

# at least 3 connected and not a dangling node
removed_dict = {}
remove_list = isolated_ids.keys()
for a,b in old_node_connections_dict.iteritems():
    if a not in remove_list:
        if len([x for x in b if x in remove_list]) == 0: # none should be missing :)
            removed_dict[a] = b

curr_ids = [x for x, y in removed_dict.iteritems() if len(y) > 2]

try:
    curr_id_mnsod = all_ids_dist_dict
except:
    curr_id_mnsod = {}

#print curr_id_mnsod
for curr_id in curr_ids:
    if curr_id in curr_id_mnsod:
        continue
    curr_id_mnsod[curr_id] = get_id_mnsod(dangling_ids, all_ids_dist_dict, curnod_buffnod_dist_dict, old_node_connections_dict,
                 new_node_id_coordinates_dict, near_node_dict, old_node_id_coordinates_dict, curr_id)
    np.save('./intermediate/all_ids_dist_dict', np.array(dict(curr_id_mnsod)))

    # pool = multiprocessing.Pool()
    # func = partial(get_id_mnsod, dangling_ids, all_ids_dist_dict, curnod_buffnod_dist_dict, old_node_connections_dict,
    #                new_node_id_coordinates_dict, near_node_dict, old_node_id_coordinates_dict)
    # mnsod = pool.map(func, curr_ids)
    # pool.close()
    # pool.join()
    # curr_id_mnsod = {x: y for x, y in zip(curr_ids, mnsod)}
    #np.save('./intermediate/all_ids_dist_dict', np.array(dict(curr_id_mnsod)))

    # outputs

# if __name__ == "__main__":
#     main()
