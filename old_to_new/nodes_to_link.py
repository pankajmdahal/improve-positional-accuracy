# creates links between given nodes (snapped from old network)
import arcpy
import pandas
from parameters import *
import numpy as np


arcpy.env.overwriteOutput = True  # overwrite files if its already present

df = pandas.read_csv(old_new_csv)
df = df[df['0'] != -99]
df = df.dropna()
conv_dict = dict(zip(df['Unnamed: 0'].tolist(), df['0'].astype(int).tolist()))


arcpy.env.overwriteOutput = True  # overwrite files if its already present

#first new network layer
arcpy.CheckOutExtension("Network")
arcpy.BuildNetwork_na(B1_ND)
#print("Network Rebuilt")
arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")


def add_route_to_layer(linkid, points, sumlayer):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "2 Meters", "", "", "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "2 Meters", "INCLUDE", "")
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", near_snap_dist)
        arcpy.SelectData_management(B1_route, "Routes")
        arcpy.FeatureToLine_management(B1_route+"/Routes", feature, "", "ATTRIBUTES")
        arcpy.CalculateField_management(feature, "FID_Routes", linkid, "PYTHON") #since ID field is not available
    except:
        print ("Route not found. 999999 Returned")
        return 999999
    arcpy.Merge_management([feature, sumlayer], temp2)
    arcpy.Copy_management(temp2, sumlayer)
    return 0

#links = old_links_cropped_shp
def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(temp1, old_nodes_shp, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("ID_1")] for row in arcpy.SearchCursor(temp2)]
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(linkid,[]).append(nodeid)
    return a


def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id,"SHAPE@XY"]) as curs:
        for _id_,xy in curs:
            new_dict[_id_]=xy
    return new_dict

def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]



arcpy.Copy_management(emptyshapefile, sumlayer_l)


new_node_id_coordinates_dict = get_coordinates(new_nodes_shp, "_ID_")
old_node_id_coordinates_dict = get_coordinates(snapped_old_nodes, "ID")

# dictionary of all connections between each node (in old network)
old_node_connections_dict = get_old_node_connections_dict(old_links_cropped_shp)

approved_nodes = {}
unapproved_nodes = {}

for l1, [n1,n2] in old_node_connections_dict.iteritems():
    print n1,n2
    # for i in range(20):
    try:
        c1,c2 = new_node_id_coordinates_dict[conv_dict[n1]], new_node_id_coordinates_dict[conv_dict[n2]]
    except:
        continue
    add_route_to_layer(l1, [c1, c2], sumlayer_l)
    approved_nodes[conv_dict[n2]] = 0

allnodes = old_node_connections_dict.values()
n = []
for x, y in allnodes:
    n.extend([x,y])

n = set(n)

unapproved_nodes = [x for x in allnodes if x not in n]


arcpy.MakeFeatureLayer_management(new_nodes_shp, "nns")
arcpy.SelectLayerByAttribute_management("nns", "NEW_SELECTION", get_where_clause("_ID_",approved_nodes.keys()))
arcpy.CopyFeatures_management("nns", new_new_nodes)