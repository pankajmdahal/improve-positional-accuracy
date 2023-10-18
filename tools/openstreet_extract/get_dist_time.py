import urllib2
import json
import csv
import time
import datetime

"""
INPUTS:
    url: a request url
OUTPUTS: 
    the data returned by calling that url
"""


def request_data_from_url(url):
    req = urllib2.Request(url)
    success = False
    while success is False:
        try:
            # open the url
            response = urllib2.urlopen(req)
            # 200 is the success code for http
            if response.getcode() == 200:
                success = True
        except Exception, e:
            # if we didn't get a success, then print the error and wait 5 seconds before trying again
            print e
            time.sleep(5)
            print "Error for URL %s: %s" % (url, datetime.datetime.now())
            print "Retrying..."
    # return the contents of the response
    return response.read()


"""
INPUTS:
    api_key: authentication to GMaps that we're allowed to request this data
    origin: lat,long of origin
    destination: lat,long of destination
    frequency: how often to scrape the data
    duration: how long to scrape the data
OUTPUTS:
    nothing, simply continues to write data to spreadsheet
"""


def scrape_gmaps_data(api_key, origin, destination, frequency, duration):
    # we want to scrape the googlemaps website
    site = 'https://maps.googleapis.com/maps/api/'
    # we want to use the distancematrix service
    service = 'distancematrix/json?'
    # input origin and destination from the user
    locations = 'origins=%s&destinations=%s&departure_time=now&' % (origin, destination)
    # input api key from user
    key = 'key=%s' % (api_key)
    # construct request url
    request_url = site + service + locations + key
    with open('traffic_data.csv', 'wb') as file:
        # let w represent our file
        w = csv.writer(file)
        # write the header row
        w.writerow(["timestamp", "travel_time"])
        # get the travel time at regular intervals
        step = 1
        while (step <= int(duration * 60 / frequency)):
            # convert response to python dictionary
            data = json.loads(request_data_from_url(request_url))
            # extract travel time from response
            traffic_time = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
            # write to our spreadsheet
            w.writerow((datetime.datetime.now(), traffic_time))
            if step % 10 == 0:
                print str(step) + ' datapoints gathered ...'
            step += 1
            time.sleep(frequency * 60)



api_key = 'AIzaSyCPbyIS7GZYH0mX_RE7QAm_3fWOkAPi1Ps'
origin = '34.070243,-118.436293' #UCLA
destination = '32.881266,-117.233290' #UCSD
frequency = 1 #min
duration = 100 #hours


scrape_gmaps_data(api_key, origin, destination, frequency, duration)
