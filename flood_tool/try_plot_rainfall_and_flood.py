import numpy as np
import pandas as pd
import requests
import sys
import csv
from scipy.spatial.distance import cdist
from scipy.spatial import distance
from pandas.core.frame import DataFrame
import matplotlib.pyplot as plt


LIVE_URL = "http://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall"
ARCHIVE_URL = "http://environment.data.gov.uk/flood-monitoring/archive/"
RAINFALL_URL = "https://environment.data.gov.uk/flood-monitoring/id/measures?parameter=rainfall"

l = requests.get(LIVE_URL) 

location = l.json()
location_csv = pd.read_csv(location['meta']['hasFormat'][0])
location_1 = location_csv.loc[:,['stationReference','long','lat','northing','easting']]
location_1 = location_1.drop_duplicates(subset='stationReference')

#grab the northing and easting

def get_stationReference(easting,northing):

    pc = np.array([[easting,northing]])
    x_easting = location_1['easting'].values
    y_northing = location_1['northing'].values
    xy_ndarray = np.stack([x_easting, y_northing], axis=1)
    dist = cdist(pc,xy_ndarray,'euclidean').reshape(len(xy_ndarray),)
 
    location_1['dist'] = dist
    #location_1['threshold'] = 10000
    stations = location_1['stationReference'][location_1['dist'].idxmin()]
    
    return stations


Need = pd.read_csv('./FloodHistory.csv', usecols=['DATE', 'easting', 'northing', 'FloodProb'])
Date = list(Need['DATE'])
Easting = list(Need['easting'])
Northing = list(Need['northing'])
FloodProb = list(Need['FloodProb'])

Station = []
Rainfall = []
for i in range(len(Easting)):
    stations = get_stationReference(Easting[i], Northing[i])
    Station.append(stations)
    

    ARCHIVE_CSV = 'http://environment.data.gov.uk/flood-monitoring/archive/readings-'+str(Date[i])+'.csv'
    archive_csv = pd.read_csv(ARCHIVE_CSV,low_memory=False)
    archive = archive_csv.loc[(archive_csv['measure'].str.contains('rainfall'))&(archive_csv['measure'].str.contains('t-15_min-mm'))&(archive_csv['measure'].str.contains(str(Station[i])))]

    #archive_station = archive.loc[archive['measure'].str.startswith('http://environment.data.gov.uk/flood-monitoring/id/measures/'+str(Station[i]), na=False)]

    sum_value = archive['value'].astype(np.float64).sum()
    Rainfall.append(sum_value)

plt.xlabel('Rainfall')
plt.ylabel('FloodProb')
plt.scatter(Rainfall, FloodProb)
plt.show()