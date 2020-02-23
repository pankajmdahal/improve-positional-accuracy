# seed should be in linkFIDs
# generating my own network using seed
import pandas
import arcpy
import os
import sys  # for printing . :D
from parameters import *

arcpy.env.overwriteOutput = True  # overwrite files if its already present

def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.CopyFeatures_management(temp1, temp2)
    arcpy.DeleteIdentical_management(temp2, ['Shape'])
    arcpy.SpatialJoin_analysis(temp1, temp2, temp3, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    linkfid_to_node_fid_list = [[row.getValue("ORIG_FID"), row.getValue("ORIG_FID_1")] for row in
                                arcpy.SearchCursor(temp3)]
    # creating ID->ID dict
    a = {}  # nodefid->(linkfid1, linkfid2, linkfid3, ...)
    for linkfid, nodefid in linkfid_to_node_fid_list:
        a.setdefault(nodefid, []).append(linkfid)
    b = {}  # linkid->(nodeid, nodeid)
    for linkfid, nodefid in linkfid_to_node_fid_list:
        b.setdefault(linkfid, []).append(nodefid)
    link_to_link_dict = {}
    for linkid, [nodeid1, nodeid2] in b.iteritems(): #if this line throws error, its because of the link has at least one multipart feature
        link_to_link_dict[linkid] = list(set(a[nodeid1] + a[nodeid2]) - set([linkid]))
    return link_to_link_dict


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


link_to_link_dict = get_old_node_connections_dict(old_links_shp)

new = [seed]
while True:
    if len(new) >=sample_size :
        break
    old = new
    temp = [link_to_link_dict[x] for x in old]
    new = [x for y in temp for x in y]
    new = list(set(new + old))

print "Old Links: {0}".format(new)

arcpy.MakeFeatureLayer_management(old_links_shp, temp1f)
arcpy.SelectLayerByAttribute_management(temp1f, "NEW_SELECTION", get_where_clause("FID", new))
arcpy.CopyFeatures_management(temp1f, old_links_cropped_shp)
