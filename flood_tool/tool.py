"""Locator functions to interact with geographic data"""
import pandas as pd
import numpy as np
import sys
from scipy.spatial import distance
# sys.path.insert(1, '../flood_tool')
from . import geo
# import geo


__all__ = ['Tool']

class Tool(object):
    """Class to interact with a postcode database file."""

    def __init__(self, postcode_file=None, risk_file=None, values_file=None):
        """
        Reads postcode and flood risk files and provides a postcode locator service.

        Parameters
        ---------

        postcode_file : str, optional
            Filename of a .csv file containing geographic location data for postcodes.
        risk_file : str, optional
            Filename of a .csv file containing flood risk data.
        postcode_file : str, optional
            Filename of a .csv file containing property value data for postcodes.
        """
        # self.postcode_file = pd.read_csv('/System/Volumes/Data/Users/luhao/OneDrive - Imperial College London/acse-4-flood-tool-nene/flood_tool/resources/postcodes.csv')
        # self.risk_file = pd.read_csv('/System/Volumes/Data/Users/luhao/OneDrive - Imperial College London/acse-4-flood-tool-nene/flood_tool/resources/flood_probability.csv')
        # self.values_file = pd.read_csv('/System/Volumes/Data/Users/luhao/OneDrive - Imperial College London/acse-4-flood-tool-nene/flood_tool/resources/property_values.csv')
        self.postcode_file = pd.read_csv(postcode_file)
        self.risk_file = pd.read_csv(risk_file)
        self.values_file = pd.read_csv(values_file)

    def clean_postcodes_to_7(self, postcode):
        '''Clean postcodes format to universal length of 7''' 
        if len(postcode) == 8 and ' ' in postcode:
            return postcode.replace(' ', '')
        elif len(postcode) == 6 and ' ' not in postcode:
            return postcode[:3]+' '+postcode[3:]
        elif len(postcode) == 6 and ' ' in postcode:
            return postcode.replace(' ', '  ')
        return postcode
    
    def clean_postcodes_to_space(self, postcode):
        if len(postcode) == 7 and ' ' not in postcode:
            return postcode[:4]+' '+postcode[4:]
        if len(postcode) == 5 and '  ' in postcode:
            return postcode.replace('  ', ' ')
        return postcode

    def get_lat_long(self, postcodes):
        """Get an array of WGS84 (latitude, longitude) pairs from a list of postcodes.

        Parameters
        ----------

        postcodes: sequence of strs
            Ordered sequence of N postcode strings

        Returns
        -------

        ndarray
            Array of Nx2 (latitude, longitdue) pairs for the input postcodes.
            Invalid postcodes return [`numpy.nan`, `numpy.nan`].
        """
        postcode_base = self.postcode_file

        postcodes = np.char.upper(np.array(postcodes).astype(str))
        postcodes = np.vectorize(self.clean_postcodes_to_7)(postcodes)
        select_df = postcode_base[postcode_base.isin(postcodes)['Postcode']]

        select_df = select_df.set_index(['Postcode'])
        latlng = pd.DataFrame(columns=('Latitude', 'Longitude'))
        postcodes_df = pd.DataFrame(postcodes)
        check_df = pd.concat([postcodes_df, latlng]).set_index([0])
        check_df.update(select_df)

        return check_df.values.astype(np.float64)


    def get_easting_northing_flood_probability(self, easting, northing):
        """Get an array of flood risk probabilities from arrays of eastings and northings.

        Flood risk data is extracted from the Tool flood risk file. Locations
        not in a risk band circle return `Zero`, otherwise returns the name of the
        highest band it sits in.

        Parameters
        ----------

        easting: numpy.ndarray of floats
            OS Eastings of locations of interest
        northing: numpy.ndarray of floats
            Ordered sequence of postcodes

        Returns
        -------

        numpy.ndarray of strs
            numpy array of flood probability bands corresponding to input locations.
        """
        # easting and northing are two lists
        easting = np.array(easting)
        northing = np.array(northing)
        en_df = pd.DataFrame({'Easting': easting, 'Northing': northing})
        prob_df = self.risk_file
        prob_df['num risk'] = prob_df['prob_4band']\
            .replace(['High', 'Medium', 'Low', 'Very Low'], [4, 3, 2, 1])
        x_easting = prob_df['X'].values
        y_northing = prob_df['Y'].values
        xy_ndarray = np.stack([x_easting, y_northing], axis=1)
        def get_prob(en_df_row):
            dist = distance.cdist(np.array([[en_df_row['Easting'], en_df_row['Northing']]])\
                , xy_ndarray).reshape(len(xy_ndarray),)
            prob_df['dist'] = dist
            prob_check = prob_df[prob_df['dist'] <= prob_df['radius']]['num risk']
            if prob_check.empty:
                prob_check = pd.Series(0)
            return prob_check
        prob_band = en_df.apply(get_prob, axis=1)
        prob_band = prob_band.fillna(0)
        prob_band['prob'] = prob_band.apply(np.max, axis=1)
        return prob_band['prob'].replace([4, 3, 2, 1, 0], \
            ['High', 'Medium', 'Low', 'Very Low', 'Zero']).values

    def get_sorted_flood_probability(self, postcodes):
        """Get an array of flood risk probabilities from a sequence of postcodes.

        Probability is ordered High>Medium>Low>Very low>Zero.
        Flood risk data is extracted from the `Tool` flood risk file.

        Parameters
        ----------

        postcodes: sequence of strs
            Ordered sequence of postcodes

        Returns
        -------

        pandas.DataFrame
            Dataframe of flood probabilities indexed by postcode and ordered from `High` to `Zero`,
            then by lexagraphic (dictionary) order on postcode. The index is named `Postcode`, the
            data column is named `Probability Band`. Invalid postcodes and duplicates
            are removed.
        """
        #import probability
        lat_lon = self.get_lat_long(postcodes)
        latitude = lat_lon[:, 0]
        longitude = lat_lon[:, 1]
        easting, northing = geo.get_easting_northing_from_lat_long(\
            latitude, longitude, radians=False)
        probability = pd.DataFrame(self.get_easting_northing_flood_probability\
            (easting, northing))
        probability.columns = ['Probability Band']
        # import postcode

        postcodes = np.char.upper(np.array(postcodes).astype(str))
        postcodes = np.vectorize(self.clean_postcodes_to_7)(postcodes)
        postcodes = pd.DataFrame(postcodes)
        postcodes.columns = ['Postcode']

        # join two data frames
        postcode = pd.concat([postcodes, probability], axis=1)

        #postcode = postcode[postcode['Probability Band'] != 'numpy.nan']
        postcode = postcode.drop_duplicates(['Postcode'], keep='last')

        # custom sorting
        postcode['Probability Band'] = pd.Categorical(postcode['Probability Band'], \
            ['High', 'Medium', 'Low', 'Very Low', 'Zero'])
        # sort my column then index
        postcode = postcode.sort_values(by=['Probability Band', 'Postcode'])
        postcode = postcode.set_index('Postcode')
        postcode.drop_duplicates()
        postcode.dropna(how='any', inplace=True)
        return postcode


    def get_flood_cost(self, postcodes):
        """Get an array of estimated cost of a flood event from a sequence of postcodes.
        Parameters
        ----------
        postcodes: sequence of strs
            Ordered collection of postcodes
        probability_bands: sequence of strs
            Ordered collection of flood probability bands
        Returns
        -------

        numpy.ndarray of floats
            array of floats for the pound sterling cost for the input postcodes.
            Invalid postcodes return `numpy.nan`.
        """

        property_base = self.values_file
        postcode_base = self.postcode_file
        # postcode_base['Postcode'] = postcode_base['Postcode'].apply(self.clean_postcodes_to_7)

        postcodes = np.char.upper(np.array(postcodes).astype(str))
        postcodes = np.vectorize(self.clean_postcodes_to_7)(postcodes)
        postcodes[np.isin(postcodes, postcode_base['Postcode'], invert=True)] = np.nan
        postcodes = np.char.upper(np.array(postcodes).astype(str))
        postcodes = np.vectorize(self.clean_postcodes_to_space)(postcodes)
        select_df = property_base[property_base.isin(postcodes)['Postcode']]\
            [['Postcode', 'Total Value']]
        select_df = select_df.set_index(['Postcode'])

        value_df = pd.DataFrame(columns=(['Total Value']))
        postcodes_df = pd.DataFrame(postcodes)
        check_df = pd.concat([postcodes_df, value_df]).set_index([0])
        check_df['Total Value'] = 0
        check_df.update(select_df)
        flood_cost = check_df.values.reshape(len(postcodes),)

        return flood_cost

    def get_annual_flood_risk(self, postcodes, probability_bands):
        """Get an array of estimated annual flood risk in pounds sterling per year of a flood
        event from a sequence of postcodes and flood probabilities.
        Parameters
        ----------
        postcodes: sequence of strs
            Ordered collection of postcodes
        probability_bands: sequence of strs
            Ordered collection of flood probabilities
        Returns
        -------

        numpy.ndarray
            array of floats for the annual flood risk in pounds sterling for the input postcodes.
            Invalid postcodes return `numpy.nan`.
        """
        probability_bands = pd.DataFrame(probability_bands).replace\
        (['High', 'Medium', 'Low', 'Very Low', 'Zero'], [0.1, 0.02, 0.01, 0.001, 0])\
        .values.reshape(len(probability_bands),)
        flood_cost = self.get_flood_cost(postcodes)

        return flood_cost*probability_bands*0.05

    def get_sorted_annual_flood_risk(self, postcodes):
        """Get a sorted pandas DataFrame of flood risks.
        Parameters
        ----------
        postcodes: sequence of strs
            Ordered sequence of postcodes
        Returns
        -------

        pandas.DataFrame
            Dataframe of flood risks indexed by (normalized) postcode and ordered by risk,
            then by lexagraphic (dictionary) order on the postcode. The index is named
            `Postcode` and the data column `Flood Risk`.
            Invalid postcodes and duplicates are removed.
        """
        # import risk
        lat_lon = self.get_lat_long(postcodes)
        latitude = lat_lon[:, 0]
        longitude = lat_lon[:, 1]
        easting, northing = geo.get_easting_northing_from_lat_long\
            (latitude, longitude, radians=False)
        probability_bands = self.get_easting_northing_flood_probability(easting, northing)
        risk = pd.DataFrame(self.get_annual_flood_risk(postcodes, probability_bands))
        risk.columns = ['Flood Risk']

        # import postcode
        postcodes = np.char.upper(np.array(postcodes).astype(str))
        postcodes = np.vectorize(self.clean_postcodes_to_7)(postcodes)
        postcodes = pd.DataFrame(postcodes)
        postcodes.columns = ['Postcode']

        # join two data frames
        postcode = pd.concat([postcodes, risk], axis=1)
        postcodes = postcodes.set_index('Postcode')
        postcode = postcode[postcode['Postcode'] != 'numpy.nan']
        postcode = postcode.drop_duplicates(['Postcode'], keep='last')

        # sort my column then index
        postcode = postcode.sort_values(by=['Flood Risk', 'Postcode'], ascending=[False, True])
        postcode = postcode.set_index('Postcode')
        postcode.dropna(how='any', inplace=True)
        return postcode
