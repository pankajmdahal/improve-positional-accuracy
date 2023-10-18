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
ID_ordered_list = []
for (x, y), id in coordinates_to_ID_dict.iteritems():
    points.X = x
    points.Y = y
    ID_ordered_list.append(id)
    point_geometry.append(arcpy.PointGeometry(points, arcpy.SpatialReference(4326)))

arcpy.CopyFeatures_management(point_geometry, point_shp)

try:
    arcpy.AddField_management(point_shp, "ID", "SHORT")
except:
    print("ID added")

i=0
with arcpy.da.UpdateCursor(point_shp, ["OID@", "SHAPE@XY", "ID"]) as cursor:
    for row in cursor:
        row[2] = ID_ordered_list[i]
        i = i+1
        cursor.updateRow(row)