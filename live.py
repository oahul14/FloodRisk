import pandas as pd
import numpy as np
import requests
import sys
from scipy.spatial.distance import cdist
from scipy.spatial import distance
# sys.path.insert(1, '../flood_tool')
import geo
import tool

a = pd.read_csv('./postcodes.csv')
b = pd.read_csv('./flood_probability.csv')
c = pd.read_csv('./property_value.csv')

LIVE_URL = "http://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall"
ARCHIVE_URL = "http://environment.data.gov.uk/flood-monitoring/archive/"
RAINFALL_URL = "https://environment.data.gov.uk/flood-monitoring/id/measures?parameter=rainfall"
# Historical Flood = "https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590"

l = requests.get(LIVE_URL) 

location = l.json()
location_csv = pd.read_csv(location['meta']['hasFormat'][0])
location_1 = location_csv.loc[:,['stationReference','long','lat','northing','easting']]
location_1 = location_1.drop_duplicates(subset='stationReference')


def FloodWarning(postcode):
    """Compute live flood warning for given list of postcode using rainfall and 
    flood probability data, calibrated to actual flood records from 2018-2019

    Parameters
    ----------
    postcode : numpy.ndarray of string
        UK postcode in 7-digit

    Returns
    -------
    dataframe sorted by level of flood warning:
        ['postcode','lat','long','X','Y','flood_probability','station','warning']
        For 'warning' 
            level 0 = safe zone, no flooding
            level 1 = small chance for flooding
            level 2 = medium chance for flooding
            level 3 = highest chance for flooding
    """
    
    DF = pd.DataFrame(columns=['postcode','Lat','Long','easting', 'northing','flood_probability','station','rainfall','warning'])
    DF['postcode'] = postcode
    # get Lat, Long from postcodes
    DF['Lat'] = tool.Tool(a, b, c).get_lat_long(postcode)[:,0]
    DF['Long'] = tool.Tool(a, b, c).get_lat_long(postcode)[:,1]
    # get easting northing from lat long
    DF['easting'], DF['northing'] = geo.get_easting_northing_from_lat_long(DF['Lat'].values,DF['Long'].values, radians=False)
    # get flood porbability from x, y
    DF.loc[:,['flood_probability']] = tool.Tool(a,b,c).get_easting_northing_flood_probability(DF['easting'].values, DF['northing'].values)
    DF['flood_probability'] = DF['flood_probability'].replace(['High', 'Medium', 'Low', 'Very Low', 'Zero'],[4, 3, 2, 1, 0]).values

    #call rainfall from rain station ID from x, y
    for i in range(len(DF)):
        DF.loc[i,['station']],DF.loc[i,['rainfall']]  = get_stationReference(DF.loc[i,'easting'], DF.loc[i,'northing'])
        #compute warning
        if DF.loc[i,['flood_probability']].values > (-.6496*DF.loc[i,['rainfall']].values + 4.6937):
            DF.loc[i,['warning']] = 3
        elif  DF.loc[i,['flood_probability']].values > (-.6496*DF.loc[i,['rainfall']].values + 3.4937):
            DF.loc[i,['warning']] = 2
        elif DF.loc[i,['flood_probability']].values > (-.6496*DF.loc[i,['rainfall']].values + 2.2937):
            DF.loc[i,['warning']] = 1
        else:  
            DF.loc[i,['warning']] = 0
    #en_ndarray = np.stack([DF['easting'].values,DF['northing'].values], axis=1)

    

    return DF.sort_values(by=['warning'], ascending=False)

def get_stationReference(easting,northing):
    """Derive rainfall station ID and accumulated daily rainfall in past 24 hrs

    Parameters
    ----------
    easting : numpy.ndarray of float
        OSGB36 Easting 
    northing : numpy.ndarray of float
        OSGB36 Northing 

    Returns
    -------
    stations : numpy.ndarray of string
        Rainfall station ID
    Rainfall : numpy.ndarray of float
        Accumulated rainfall measured from such rain gauge station in past 24 hr
    """
    pc = np.array([[easting,northing]])
    x_easting = location_1['easting'].values
    y_northing = location_1['northing'].values
    xy_ndarray = np.stack([x_easting, y_northing], axis=1)
    dist = cdist(pc,xy_ndarray,'euclidean').reshape(len(xy_ndarray),)
 
    location_1['dist'] = dist
    location_1['threshold'] = 10000
    stations = location_1['stationReference'][location_1['dist'].idxmin()]
   
    r = requests.get("https://environment.data.gov.uk/flood-monitoring/id/measures/"+str(stations)+"-rainfall-tipping_bucket_raingauge-t-15_min-mm/readings?_sorted&_limit=96")
    rainfall = r.json()
    rainfall_csv = pd.read_csv(rainfall['meta']['hasFormat'][0])
    rainfall_1 = rainfall_csv.loc[:,['dateTime','value']]
    rainfall_value = rainfall_1['value'].astype(np.float64).sum() 

    
    return stations, rainfall_value

# print(FloodWarning(np.array(['ME139BY','TN263BB', 'TN126TE','BR8 7RL','DA2 7EX', 'CT7 0NG'])))
inputa = a.loc[:20:2,['Postcode']].values
#print(inputa.flatten())
print(FloodWarning(inputa.flatten()))
