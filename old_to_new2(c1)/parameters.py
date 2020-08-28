import pandas
import arcpy


arcpy.env.overwriteOutput = True
arcpy.env.outputMFlag = "Disabled"
# Set the outputZFlag environment to Disabled
arcpy.env.outputZFlag = "Disabled"

arcpy.CheckOutExtension("Network")

curr_node_buff_node_dist = 5

sr_p = arcpy.SpatialReference(102039)
sr_g = arcpy.SpatialReference(4326)

# what portion of the new network has to be considered? This would significantly reduce the size of network dataset and consequently reduce execution time
old_link_buffer_clip_distance = "10 Miles"

clip_state_list = ["'TN'", "'NC'", "'SC'", "'GA'", "'FL'", "'AL'", "'MS'"]

near_snap_dist = "2 Mile"  # the distance to which the old nodes has to snapped to the new network
network_buffer_dist = 5

extent_switch = 1  # set this to one if the new network is significantly bigger

# generic shapefiles :)
old_links_shp = "../../RAIL11/RAIL/gis/old_links.shp"  # old 1995 linkss
new_links_shp = './shp/railway_ln_connected.shp'

# all of these are temporary
new_nodes_shp = './shp/intermediate/nodes_new.shp'
new_links_clipped = './shp/intermediate/new_links_clipped.shp'
snapped_old_nodes = './shp/intermediate/snapped_old_nodes.shp'
old_links_cropped_shp = './shp/intermediate/cropped_old_network.shp'
temp1f = "temp1f"
all_area_shp = "../shp/clip_area/all.shp"
all_area_shp_f = "allarea"

# temporary/intermediate files
o = "in_memory/o"  # temporary files
d = "in_memory/d"
m = "in_memory/m"

feature = "C:/GIS/feature.shp"  # i guess this is just a temporary layer/ no worries
temp = "C:/GIS/temp.shp"
temp1 = "C:/GIS/temp1.shp"
temp2 = "C:/GIS/temp2.shp"
temp3 = "C:/GIS/temp3.shp"

# for validation
correct_nodes_shp = './shp/allnodes.shp'
emptyshapefile = "./shp/intermediate/empty.shp"
new_new_nodes = "./shp/intermediate/_new_nodes.shp"
old_nodes_shp = './shp/intermediate/nodes_old.shp'

# network dataset files
B1_ND = "./shp/intermediate/B1_ND.nd"
B1_route = "B1_route"

# csv files
old_new_csv = "./csv/old_new_dict.csv"
route_not_found_csv = "./csv/route_not_found.csv"
min_max_csv = "./csv/min_max.csv"
multiple_minimum_csv = "./csv/multiple_minimum.csv"

new_l = new_links_clipped


def get_dist(points, current_id, buffer_id):
    if points[0] == points[1]:  # if both the snapped connecting node and the point being tested is the same
        return [], 0
    arcpy.MakeFeatureLayer_management(new_l, "newlf")
    arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")
    # print current_id
    # print buffer_id
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(sr_g)
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "", "INCLUDE", "")  # just in case
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "")
    except:
        return {}, 99999
    #arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "")

    arcpy.SelectData_management(B1_route, "Routes")
    arcpy.FeatureToLine_management(B1_route + "/Routes", feature, "", "ATTRIBUTES")
    arcpy.AddField_management(feature, "curr_id", "LONG")
    arcpy.AddField_management(feature, "buffer_id", "LONG")
    arcpy.CalculateField_management(feature, "curr_id", current_id, "PYTHON")
    arcpy.CalculateField_management(feature, "buffer_id", buffer_id, "PYTHON")
    arcpy.SelectLayerByLocation_management("newlf", "WITHIN", feature)
    _list_ = [f[0] for f in arcpy.da.SearchCursor("newlf", '_ID_')]
    return _list_, ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH', "", sr_p)][0]) / 1604.34


# creates links in GIS and returns linkIDs
def get_distance1(ids_of_connecting_nodes, current_id, buffer_id, new_node_id_coordinates_dict,
                  old_node_id_coordinates_dict):
    # print current_id
    no_overlapping_found_flag = 0
    dist = 0
    count_dict = {}
    for id in ids_of_connecting_nodes:
        # print ("{0}->{1}".format(buffer_id, id))
        pair = new_node_id_coordinates_dict[buffer_id], old_node_id_coordinates_dict[id]
        list_of_links, currdist = get_dist(pair, current_id, buffer_id)
        if currdist == 999999:
            route_not_found_dict[buffer_id] = id
        dist += currdist
        for link in list_of_links:
            if link in count_dict:
                count_dict[link] = count_dict[link] + 1
            else:
                count_dict[link] = 1
    try:
        id, max_count = sorted(count_dict.items(), key=lambda item: item[1])[-1]
    except:
        return dist, 0
    if max_count == 1:  # only the routes that are not overlapped (the size of the shapefile is limited)
        no_overlapping_found_flag = 1
        # comment this if you dont want a shapefile
        # try:
        #    arcpy.Append_management(feature, empty_memory)
        # except: #if its the first time
        #     arcpy.CopyFeatures_management(feature, empty_memory)
    return dist, no_overlapping_found_flag


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def get_id_mnsod(dangling_ids, all_ids_dist_dict, curnod_buffnod_dist_dict, old_node_connections_dict,
                 new_node_id_coordinates_dict, near_node_dict, old_node_id_coordinates_dict, current_id):
    print("Old Node ID: {0}".format(current_id))
    if current_id in all_ids_dist_dict:
        ids_distance_dict = all_ids_dist_dict[current_id]
    else:
        ids_distance_dict = {}  # each id and its sum of distances to connecting nodes on all buffers
    try:
        buffer_nodes = curnod_buffnod_dist_dict[current_id]
    except:
        print ("No buffer nodes found")
        return {99999: [99999,99999]}
    sorted_buffer_nodes = sorted(buffer_nodes.items(), key=lambda item: item[1])

    sorted_buffer_nodes = [x for x in sorted_buffer_nodes if x not in dangling_ids]

    print("{0}: {1}".format(current_id, sorted_buffer_nodes))
    ids_of_connecting_nodes = old_node_connections_dict[current_id]
    # the isolated nodes is removed because there would be no route to the node (saves time)
    # ids_of_connecting_nodes = list(set([x for x in ids_of_connecting_nodes if x not in isolated_ids]))
    print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))  # in old network
    # remove the buffer_node_ids that are not in the snapped_removed_ids
    # buffer_node_ids
    for buffer_id, distance in sorted_buffer_nodes:
        if distance > near_node_dict[current_id][1]:  # cannot be too close
            break
        if buffer_id in ids_distance_dict:
            # print ("sum of paths known for bufferid: {0}".format(buffer_id))
            continue
        else:  # id not present (check if further going necessary
            dist1, overlap_flag = get_distance1(ids_of_connecting_nodes, current_id, buffer_id,
                                                new_node_id_coordinates_dict, old_node_id_coordinates_dict)
            ids_distance_dict[buffer_id] = [dist1, overlap_flag]
    return ids_distance_dict
    # save dictionaries as numpy objects
