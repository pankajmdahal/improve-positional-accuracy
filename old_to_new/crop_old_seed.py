# generating my own network using seed
import pandas
import arcpy
import os
import sys  # for printing . :D
from parameters import *

arcpy.env.overwriteOutput = True  # overwrite files if its already present

seed = 4317 #knoxville
depth = 10

arcpy.MakeFeatureLayer_management(old_links_shp, temp1f)

links = old_links_shp


def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(temp1, old_nodes_shp, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("ID_1")] for row in arcpy.SearchCursor(temp2)]
    # node_fid_id_dict = {row.getValue("ID"): row.getValue("FID") for row in arcpy.SearchCursor(old_nodes_shp)}
    link_to_fid_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(links)}
    # creating ID->ID dict
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(nodeid, []).append(link_to_fid_dict[linkid])
    b = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        b.setdefault(link_to_fid_dict[linkid], []).append(nodeid)
    link_to_link_dict = {}
    for linkid, [nodeid1, nodeid2] in b.iteritems():
        link_to_link_dict[linkid] = list(set(a[nodeid1] + a[nodeid2]) - set([linkid]))
    return link_to_link_dict


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


link_to_link_dict = get_old_node_connections_dict(old_links_shp)

new = [seed]
for i in range(depth):
    old = new
    temp = [link_to_link_dict[x] for x in old]
    new = [x for y in temp for x in y]
    new = list(set(new + old))

print "Old Links: {0}".format(new)

arcpy.SelectLayerByAttribute_management(temp1f, "NEW_SELECTION", get_where_clause("ID", new))
arcpy.CopyFeatures_management(temp1f, old_links_cropped_shp)
