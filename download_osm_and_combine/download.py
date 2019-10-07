# download from geofabric
import urllib
import pandas
import zipfile
import os

#sampleURL = "http://download.geofabrik.de/north-america/us/alaska-latest-free.shp.zip"

state_names = pandas.read_csv('input/statenames.csv')
all_name_list = state_names['names'].tolist()

already_done_list = os.listdir("./intermediate/shapefiles")

name_list = [x for x in all_name_list if x not in already_done_list]

for names in name_list:
    if names == "california":
        continue
    print ("Working on " + names)
    if names in ['mexico']:
        link_url = "http://download.geofabrik.de/north-america/" + names + "-latest-free.shp.zip"
        if names == 'canada': #no canada data available in the website
            continue
    else:
        link_url = "http://download.geofabrik.de/north-america/us/" + names + "-latest-free.shp.zip"
    urllib.urlretrieve(link_url, "intermediate/download.zip")
    print (names + " shape file downloaded. Unzipping...")
    zipfile.ZipFile("intermediate/download.zip", 'r').extractall('intermediate/shapefiles/' + names)
    print (names + " shape file extracted")
