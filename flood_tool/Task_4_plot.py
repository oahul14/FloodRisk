# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# import requests
# import json
# storm = pd.read_csv('readings-full-2019-06-11.csv', dtype = {'label': str, 'dateTime': str, 'unitName': str, 'stationReference': str,\
#     'parameter': str, 'valueType': str, 'value': str, 'period': str,\
#         'station': str, 'datumType':str, 'qualifier': str, 'date': str})


# # DF = pd.read_csv('resources/flood_probability.csv')

# # DF['prob_value'] = DF['prob_4band']

# # DF.loc[DF['prob_4band'] == 'Very Low', 'prob_value'] = 0
# # DF.loc[DF['prob_4band'] == 'Low', 'prob_value'] = 0.75
# # DF.loc[DF['prob_4band'] == 'Medium', 'prob_value'] = 1.75
# # DF.loc[DF['prob_4band'] == 'High', 'prob_value'] = 3

# # DF = DF.sort_values(by='prob_value')

# # plt.scatter(DF['X'], DF['Y'], s=DF['radius']/200,alpha=0.3,cmap='YlOrRd')





# data1 = storm.sort_values(by=['label', 'dateTime'])
# data1 = data1.drop('date', 1)
# data1 = data1.drop('measure', 1)
# data1 = data1.drop('datumType', 1)
# data1 = data1.drop('station', 1)
# rain = data1[((data1.qualifier == 'Tipping Bucket Raingauge') & (data1.period == '900'))]
# station = rain.drop_duplicates(['stationReference'], keep='last')
# ref = np.array(station['stationReference'])
# staref = pd.DataFrame(ref)
# staref.columns = ['stationReference']
# easti = []
# northi = []
# print(3)
# # For each channel, we access its information through its API
# count=0
# # for i in ref:
# #     rainfall = requests.get("https://environment.data.gov.uk/flood-monitoring/id/stations/" + i).json()
# #     if i == '068416':
# #         count += 1
# #     else:
# #         east = rainfall['items']['easting']
# #         north = rainfall['items']['northing']
# #         easti.append(east)
# #         northi.append(north)
# #         count += 1
# # easting = pd.DataFrame(easti)
# # northing = pd.DataFrame(northi)
# # staref = pd.concat([staref, easting], axis=1)
# # staref = pd.concat([staref, northing], axis=1)
# # staref.columns = ['stationReference', 'easting', 'northing']
# # print(2)
# # staref = staref.sort_values(by=['stationReference'])


# for i in range(0,24):
#     k = i
#     if i < 10:
#         k = '0' + str(i)
#     for j in range(0,60,15):
#         if j==0:
#             j = '00'
#         dates = '2019-06-11T' + str(k) + ':' + str(j) +':00Z'
#         print(dates)
#         rainpl = rain[(rain.dateTime == dates)]
#         rainpl = rainpl.sort_values(by=['stationReference'])
#         staref = staref.sort_values(by=['stationReference'])
#         if j==0:
#             j = 0
#         # print(1)
#         # staref.to_csv('rain.csv')
#         staref = pd.read_csv('rain.csv')
    
#         staref = staref.reset_index(drop=True)
#         rainpl = rainpl.reset_index(drop=True)
#         staref = staref.drop('ind', 1)
#         rainpl = rainpl.drop('label', 1)
#         rainpl = rainpl.drop('parameter', 1)
#         rainpl = rainpl.drop('unitName', 1)
#         rainpl = rainpl.drop('valueType', 1)
#         rainpl = rainpl.drop('qualifier', 1)
#         rainpl = rainpl.drop('stationReference', 1)
#         rainpl = rainpl.drop('period', 1)
        
#         new = pd.concat([rainpl, staref], axis=1)
#         new = new.sort_values(by=['stationReference'])
#         new['value'] = new['value'].astype(float)
#         print(new)
#         plt.scatter(new['easting'], new['northing'], s=15, alpha=1, c=new['value'], cmap='Reds', vmax=4, vmin=0)
#         plt.colorbar()
#         plt.pause(0.2)
#         plt.clf()


# # plt.show()
