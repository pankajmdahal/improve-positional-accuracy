import arcpy

arcpy.env.overwriteOutput = True

feature = "C:/Users/pankaj/Desktop/Tools/shp/railway_ln_connected/railway_ln_connected.shp"

coordinates_to_ID_dict = {}
invalid_oids = []

def get_ID_from_coordinates(set_of_XY):
    if set_of_XY in coordinates_to_ID_dict.keys():
        # print("present")
        # print (coordinates_to_ID_dict[set_of_XY])
        return coordinates_to_ID_dict[set_of_XY]
    else:
        # print("absent")
        try:
            maxval = max(coordinates_to_ID_dict.values())
        except:
            maxval = 0
        coordinates_to_ID_dict[set_of_XY] = maxval + 1
        # print (maxval+1)
        return maxval + 1


# check if columns ANODE and BNODE exists
try:
    arcpy.AddField_management(feature, "ANODE", "LONG")
    arcpy.AddField_management(feature, "BNODE", "LONG")
except:
    print("ANODE and BNODE already present")

with arcpy.da.UpdateCursor(feature, ["OID@", "SHAPE@", "ANODE", "BNODE"]) as cursor:
    for row in cursor:
        # get start coordinates
        startXY = (row[1].firstPoint.X, row[1].firstPoint.Y)
        # get end coordinates
        endXY = (row[1].lastPoint.X, row[1].lastPoint.Y)
        row[2] = get_ID_from_coordinates(startXY)
        row[3] = get_ID_from_coordinates(endXY)
        print("{0},{1}".format(row[2],row[3]))
        # if type(row[2])!=int:
        #     row[2]=-1
        # if type(row[3])!=int:
        #     row[3]=-1
        cursor.updateRow(row)


point_shp = "C:/GIS/points.shp"
# plot nodes using the coordinates_to_ID_dict
# change the dataframe to a shapefile
points = arcpy.Point()
point_geometry = []
for (x, y), id in coordinates_to_ID_dict.iteritems():
    points.X = x
    points.Y = y
    points.M = id
    point_geometry.append(arcpy.PointGeometry(points, arcpy.SpatialReference(4326)))
arcpy.CopyFeatures_management(point_geometry, point_shp)

try:
    arcpy.AddField_management(point_shp, "ID", "SHORT")
except:
    print("ID")

coordinates_to_ID_dict_rounded = {(round(x, 4), round(y, 4)): ID for (x, y), ID in coordinates_to_ID_dict.iteritems()}

with arcpy.da.UpdateCursor(point_shp, ["OID@", "SHAPE@XY", "ID"]) as cursor:
    for row in cursor:
        dumm = row[1]
        rounded_coordinates = (round(dumm[0], 4), round(dumm[1], 4))
        row[2] = coordinates_to_ID_dict_rounded[rounded_coordinates]
        cursor.updateRow(row)
