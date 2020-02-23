#validates the nodes in the new network
import pandas as pd
from parameters import *
import arcpy

new_nodes_shpf = "nnshpf"


df = pd.read_csv(old_new_csv)

df = df[df['0'] != -99] #not found
df = df[df['0'] != -98] #dangling


conv_dict = dict(zip(df['Unnamed: 0'].tolist(), df['0'].astype(int).tolist()))

arcpy.MakeFeatureLayer_management(new_nodes_shp, new_nodes_shpf)


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]




arcpy.SelectLayerByAttribute_management(new_nodes_shpf, "NEW_SELECTION", get_where_clause("_ID_", conv_dict.values()))
arcpy.CopyFeatures_management(new_nodes_shpf, "C:/GIS/tempo.shp")


arcpy.Near_analysis("C:/GIS/tempo.shp", correct_nodes_shp)

