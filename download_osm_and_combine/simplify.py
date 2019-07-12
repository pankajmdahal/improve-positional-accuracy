# download from geofabric
import urllib
import pandas
import zipfile

#sampleURL = "http://download.geofabrik.de/north-america/us/alaska-latest-free.shp.zip"

state_names = pandas.read_csv('input/statenames.csv')
name_list = state_names['names'].tolist()

for names in name_list:
    link_url = "http://download.geofabrik.de/north-america/us/" + names + "-latest-free.shp.zip"
    urllib.urlretrieve(link_url, "intermediate/download.zip")
    print (names + " shape file downloaded. Unzipping...")
    zipfile.ZipFile("intermediate/download.zip", 'r').extractall('intermediate/shapefiles/' + names)
    print (names + " shape file extracted")
