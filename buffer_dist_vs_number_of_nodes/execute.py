import arcpy
import pandas

A = 0
B = 45000
diff = 1000

buffer_dist = range(A,B,diff)

input_nodes = "../shp/nodes/rail2mnodes.shp"
buffer_nodes = "../shp/nodes/railway_ln_nodes.shp"

input_nodesf = "if"
buffer_nodesf = "bf"

arcpy.MakeFeatureLayer_management(input_nodes,input_nodesf)
arcpy.MakeFeatureLayer_management(buffer_nodes,buffer_nodesf)


len_buffer_dict = {}

for dist in buffer_dist:
    if dist in len_buffer_dict.keys():
        continue
    print dist
    arcpy.SelectLayerByLocation_management(buffer_nodesf, "WITHIN_A_DISTANCE", input_nodesf, str(dist) + " Feet", "NEW_SELECTION")
    len_buffer_dict[dist] = len([_row_[0] for _row_ in arcpy.da.SearchCursor(buffer_nodesf, ['FID'])])

cumm_dict = {}


for i in range(len(buffer_dist)):
    if buffer_dist[i] == A:
        continue
    else:
        cumm_dict[buffer_dist[i]] = len_buffer_dict[buffer_dist[i]] - len_buffer_dict[buffer_dist[i-1]]






pandas.DataFrame.from_dict(cumm_dict, orient='index').to_csv("bufferdist_nodecount.csv")