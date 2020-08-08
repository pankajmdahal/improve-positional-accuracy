# creates links between given FIPS to calculate distance,time
import arcpy
import pandas

arcpy.env.overwriteOutput = True


ND = "./output/highway_ln1_ND.nd"
snapped_dumm = "C:/GIS/dumm.shp"
fips = 'C:/Users/pankaj/Desktop/RAIL/gis/standards/FIPS.shp'
alllinks = "./output/highway_ln1.shp"
feature = "C:/GIS/feature.shp"  # i guess this is just a temporary layer/ no worries

arcpy.Copy_management(fips, snapped_dumm)


# snap FIPS to nearest links
arcpy.Snap_edit(snapped_dumm, [[alllinks, "EDGE", "100 Miles"]])
arcpy.MakeRouteLayer_na(ND, "Route", "resist") # update the network dataset if required (this is not required generally)

# temporary files
m = "C:/GIS/m.shp"
sr = arcpy.SpatialReference(102005)

#make arrangements for both distance and time
def get_dist_AB(fips_a, fips_b):
    arcpy.Select_analysis(snapped_dumm, m, 'FIPS = {0} OR FIPS = {1}'.format(fips_a,fips_b))
    arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "5000 Kilometers", "", "B1 SHAPE;B1_ND_Junctions SHAPE",
                          "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "5 Meters", "INCLUDE", "B1 #;B1_ND_Junctions #")
    try:
        arcpy.Solve_na("Route", "SKIP", "TERMINATE", "5000 Kilometers")
    except:
        return [9999999,9999999]
    arcpy.SelectData_management("Route", "Routes")
    #arcpy.CopyFeatures_management("Route/Routes", feature)
    arcpy.FeatureToLine_management("Route/Routes", feature)
    dummy = [ [row[0],row[1]*0.000621371] for row in arcpy.da.SearchCursor(feature, ['Total_resi', "SHAPE@LENGTH"], spatial_reference=sr)][0]
    return dummy



OD = pandas.ExcelFile("../shortest_dist/GNBC 2017 Traffic OD Test1.xlsx").parse("GNBC 2017 Traffic")
name_to_FIPS_df = pandas.ExcelFile("../shortest_dist/FIPS.xls").parse("FIPS")
name_to_FIPS_df.columns = ["FIPS", "COUNTY", "STATE"]
name_to_FIPS_df["temp"]=name_to_FIPS_df["COUNTY"].astype(str)+","+name_to_FIPS_df["STATE"].astype(str)
name_to_FIPS_df = name_to_FIPS_df.set_index("temp")
name_to_FIPS_df = name_to_FIPS_df["FIPS"]
county_to_fips_dict = name_to_FIPS_df.to_dict()

#get OFIPS and DFIPS
OD["OFIPS"] = OD['Ostate'].map(county_to_fips_dict)
OD["DFIPS"] = OD['Dstate'].map(county_to_fips_dict)
OD = OD.fillna(0)
OD['dist'] = ''
OD['time'] = ''



arcpy.CheckOutExtension("Network")
for i in range(len(OD)):
    # origin = 47047
    # destination = 47093
    #origin = int(OD["OFIPS"][i])
    #destination = int(OD["DFIPS"][i])
    time, distance = get_dist_AB(origin,destination)
    print("{0}->{1}:[Distance:{2}, Time:{3} hrs]".format(origin,destination,distance,time))
    OD["dist"][i] = distance
    OD["time"][i] = time



OD.to_csv("aaa.csv",encoding='utf-8-sig')