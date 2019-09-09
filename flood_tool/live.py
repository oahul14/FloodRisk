"""Interactions with live Environment Agency API."""


import sys
import urllib.request
import json

import numpy as np

EA_URL = "http://environment.data.gov.uk/flood-monitoring/id/stations"
POSTCODE_URL = "http://api.postcodes.io/postcodes/"

def data_as_json(base_url, *args, http_request=None, **parameters):
    url = base_url
    if parameters or args:
        url += '?%s'%('&'.join(list(args)+['%s=%s'%_ for _ in parameters.items()]))
    req = urllib.request.Request(url)
    print(url)
    if http_request:
        req.add_header('Content-Type', 'application/json')
    return json.load(urllib.request.urlopen(req, http_request))


def get_nearest(longitude, latitude, dist=10):
    """Get id of nearest station for a longitude & latitude."""

    data = data_as_json(EA_URL, parameter='rainfall',  
                    long=longitude, lat=latitude,
                        dist=10)

    d2_min = np.inf
    i_min = None

    for i, d in enumerate(data['items']):
        x,y = d['long'], d['lat']
        d2 = (x-longitude)**2+(y-longitude)**2

        if d2<d2_min:
            i_min = i

    if i is not None:
        return data['items'][i]['@id']
    else:
        raise ValueError


def get_rainfall(longitude, latitude):
    """Get rainfall readings for a longitude & latitude."""

    data_id = get_nearest(longitude, latitude, dist=10)

    rainfall_data = data_as_json(data_id+'/readings','_sorted',
                                 parameter='rainfall',
                                 startdate="2015-02-05",
                                 _limit=1)

    unitName = data_as_json(rainfall_data['items'][0]['measure'])['items']['unitName']

    return rainfall_data['items'][0]['value'], unitName
