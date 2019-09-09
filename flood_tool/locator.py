"""Example module in template package."""

import numpy as np
import os
import pandas

### temporary import
from scipy.spatial import ckdtree

__all__ = ['PostcodeLocator']

class PostcodeLocator(object):
    """Class to interact with a postcode database file."""

    def __init__(self, postcode_file=(os.path.dirname(__file__)
                                      +'/resources/LondonPostcodes.csv')):
    
        self.update(postcode_file)

    def update(self, postcode_file=None):
        """Update the postcode finder."""

        if postcode_file:
            self._postcodedb = pandas.read_csv(postcode_file)
        self._finder = ckdtree.cKDTree(self._postcodedb[['Longitude','Latitude']])
        return self

    def get_postcode(self, location_list):
        """Get an array of the postcodes nearest an array of locations in longitude-latitude format. 
    """

        idx = self._finder.query(location_list)[1]
        return self._postcodedb['Postcode 1'].get_values()[idx]

    def get_values_by_postcode(self, postcodes, keys):
        """Get an orderd array of values at list of postcodes."""

        data = self._postcodedb.loc[self._postcodedb['Postcode 1'].isin(postcodes)]
        data = data.set_index('Postcode 1')
        return data.loc[postcodes, keys].values

    def get_long_lat(self, postcodes):
        """Get an array of (longitude, latitude) tuples from a list of postcodes."""

        return self.get_values_by_postcode(postcodes, ['Longitude', 'Latitude'])

    def get_easting_northing(self, postcodes):
        """Get an array of (easting, northing) tuples from a list of postcodes."""

        return self.get_values_by_postcode(postcodes, ['Easting', 'Northing'])

