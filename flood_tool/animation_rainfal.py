"""Live and historical flood monitoring data from the Environment Agency API"""
import requests
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cbook as cbook
import numpy as np
import folium

__all__  = ['GetData']

class Get(object):

    def __init__(self):
        self.dateTime = np.array(['2019-06-10T00:00:00Z', '2019-06-10T00:15:00Z', '2019-06-10T00:30:00Z',
                                '2019-06-10T00:45:00Z', '2019-06-10T01:00:00Z', '2019-06-10T01:15:00Z',
                                '2019-06-10T01:30:00Z', '2019-06-10T01:45:00Z', '2019-06-10T02:00:00Z',
                                '2019-06-10T02:15:00Z', '2019-06-10T02:30:00Z', '2019-06-10T02:45:00Z',
                                '2019-06-10T03:00:00Z', '2019-06-10T03:15:00Z', '2019-06-10T03:30:00Z',
                                '2019-06-10T03:45:00Z', '2019-06-10T04:00:00Z', '2019-06-10T04:15:00Z',
                                '2019-06-10T04:30:00Z', '2019-06-10T04:45:00Z', '2019-06-10T05:00:00Z',
                                '2019-06-10T05:15:00Z', '2019-06-10T05:30:00Z', '2019-06-10T05:45:00Z',
                                '2019-06-10T06:00:00Z', '2019-06-10T06:15:00Z', '2019-06-10T06:30:00Z',
                                '2019-06-10T06:45:00Z', '2019-06-10T07:00:00Z', '2019-06-10T07:15:00Z',
                                '2019-06-10T07:30:00Z', '2019-06-10T07:45:00Z', '2019-06-10T08:00:00Z',
                                '2019-06-10T08:15:00Z', '2019-06-10T08:30:00Z', '2019-06-10T08:45:00Z',
                                '2019-06-10T09:00:00Z', '2019-06-10T09:15:00Z', '2019-06-10T09:30:00Z',
                                '2019-06-10T09:45:00Z', '2019-06-10T10:00:00Z', '2019-06-10T10:15:00Z',
                                '2019-06-10T10:30:00Z', '2019-06-10T10:45:00Z', '2019-06-10T11:00:00Z',
                                '2019-06-10T11:15:00Z', '2019-06-10T11:30:00Z', '2019-06-10T11:45:00Z',
                                '2019-06-10T12:00:00Z', '2019-06-10T12:15:00Z', '2019-06-10T12:30:00Z',
                                '2019-06-10T12:45:00Z', '2019-06-10T13:00:00Z', '2019-06-10T13:15:00Z',
                                '2019-06-10T13:30:00Z', '2019-06-10T13:45:00Z', '2019-06-10T14:00:00Z',
                                '2019-06-10T14:15:00Z', '2019-06-10T14:30:00Z', '2019-06-10T14:45:00Z',
                                '2019-06-10T15:00:00Z', '2019-06-10T15:15:00Z', '2019-06-10T15:30:00Z',
                                '2019-06-10T15:45:00Z', '2019-06-10T16:00:00Z', '2019-06-10T16:15:00Z',
                                '2019-06-10T16:30:00Z', '2019-06-10T16:45:00Z', '2019-06-10T17:00:00Z',
                                '2019-06-10T17:15:00Z', '2019-06-10T17:30:00Z', '2019-06-10T17:45:00Z',
                                '2019-06-10T18:00:00Z', '2019-06-10T18:15:00Z', '2019-06-10T18:30:00Z',
                                '2019-06-10T18:45:00Z', '2019-06-10T19:00:00Z', '2019-06-10T19:15:00Z',
                                '2019-06-10T19:30:00Z', '2019-06-10T19:45:00Z', '2019-06-10T20:00:00Z',
                                '2019-06-10T20:15:00Z', '2019-06-10T20:30:00Z', '2019-06-10T20:45:00Z',
                                '2019-06-10T21:00:00Z', '2019-06-10T21:15:00Z', '2019-06-10T21:30:00Z',
                                '2019-06-10T21:45:00Z', '2019-06-10T22:00:00Z', '2019-06-10T22:15:00Z',
                                '2019-06-10T22:30:00Z', '2019-06-10T22:45:00Z', '2019-06-10T23:00:00Z',
                                '2019-06-10T23:15:00Z', '2019-06-10T23:30:00Z', '2019-06-10T23:45:00Z'])

        self.station_url = 'https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall'
        self.june_10_2019 = pd.read_csv('/System/Volumes/Data/Users/luhao/Downloads/readings-full-2019-06-10.csv')
        
    def get_data(self):
        station_json = requests.get(self.station_url).json()
        station_df = pd.read_csv(station_json['meta']['hasFormat'][0])
        ref_cor_df = station_df[['stationReference', 'easting', 'northing']]

        june_10_2019 = self.june_10_2019[self.june_10_2019['parameter'] == 'rainfall'].sort_values(by=['dateTime'])
        june_10_2019['easting'] = np.nan
        june_10_2019['northing'] = np.nan

        station_array = june_10_2019['stationReference'].values
        # station_df = june_10_2019
        select_df = ref_cor_df[ref_cor_df.isin(station_array)['stationReference']].set_index('stationReference')
        select_df = select_df.loc[~select_df.index.duplicated(keep='first')]

        station_df = june_10_2019[['stationReference', 'easting', 'northing']].set_index('stationReference')
        june_10_2019 = june_10_2019.drop(['easting', 'northing'], axis=1)
        station_df.update(select_df)

        june_10_2019 = june_10_2019.set_index('stationReference')
        want_df = pd.concat([june_10_2019, station_df], axis=1)
        want_df = want_df[['dateTime', 'value', 'easting', 'northing']]

        want_df = want_df.set_index('dateTime')
        want_df = want_df[want_df.index.isin(self.dateTime)]
        want_df.dropna(inplace=True)

        def get(dt):
            values = want_df[want_df.index == dt]['value'].values.astype(np.float64)
            eastings = want_df[want_df.index == dt]['easting'].values.astype(np.float64)
            northings = want_df[want_df.index == dt]['northing'].values.astype(np.float64)
            value_set.append(values)
            easting_set.append(eastings)
            northing_set.append(northings)
            return
        value_set = []
        easting_set = []
        northing_set = []
        np.vectorize(get)(self.dateTime)
        return want_df


def animate(data):
    want_df = data
    for dt in Get().dateTime:
        plt.style.use('ggplot')
        time_df = want_df[want_df.index == dt]
        x, y, c = time_df['easting'].astype(np.float64), time_df['northing'].astype(np.float64), time_df['value'].astype(np.float64)
        plt.scatter(x, y, c=c, s=20, alpha=0.7, cmap='YlGn')
        plt.title(dt)
        plt.colorbar()
        plt.pause(0.3)
        plt.clf()
    plt.show()
