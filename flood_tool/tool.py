"""Locator functions to interact with geographic data"""

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
        self.postcode_file = pd.read_csv('../flood_tool/resources/postcodes.csv')
        self.risk_file = pd.read_csv('../flood_tool/resources/flood_probability.csv')
        self.values_file = pd.read_csv('../flood_tool/resources/property_value.csv')
        pass


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
        def clean_postcodes(postcode):
            if len(postcode) == 8 and ' ' in postcode:
                return postcode.replace(' ', '')
            elif len(postcode) == 6 and ' ' not in postcode:
                return postcode[:3]+' '+postcode[3:]
            return postcode
        
        postcode_base = self.postcode_file
        postcode_base['Postcode'] = postcode_base['Postcode']

        postcodes = np.char.upper(postcodes.astype(str))
        postcodes = np.vectorize(clean_postcodes)(postcodes)
        select_df = postcode_base[postcode_base.isin(postcodes)['Postcode']]
        
        select_df = select_df.set_index(['Postcode'])
        latlng = pd.DataFrame(columns=('Latitude', 'Longitude'))
        postcodes_df = pd.DataFrame(postcodes)
        check_df = pd.concat([postcodes_df, latlng]).set_index([0]) 
        check_df.update(select_df)

        return check_df.values


    def get_easting_northing_flood_probability_band(self, easting, northing):
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
        amount = len(easting)
        prob_df = self.risk_file

        easting = easting.reshape(1, len(easting))
        XT = prob_df['X'].values.reshape(1, len(prob_df['X'])).T
        XT_easting = (XT-easting)*(XT-easting)

        northing = northing.reshape(1, len(northing))
        YT = prob_df['Y'].values.reshape(1, len(prob_df['X'])).T
        YT_northing = (YT-northing)*(YT-northing)
        point_dist = XT_easting+YT_northing

        radius_range = prob_df['radius'].apply(lambda rad: rad*rad).values
        radius_range = radius_range.reshape(len(radius_range), 1)        
        prob = prob_df.loc[:, ['prob_4band']]
        prob = prob.replace(['High', 'Medium', 'Low', 'Very Low'], [4, 3, 2, 1]).values
        col_names = ['Postcode'+str(i+1) for i in range(amount)]

        bool_mesh = (point_dist <= radius_range).astype(int)
        bool_df = pd.DataFrame(bool_mesh, columns=col_names)

        prob_band_array = (bool_df*prob).max(axis=0).replace( [4, 3, 2, 1, 0], ['High', 'Medium', 'Low', 'Very Low', 'Zero']).values

        return prob_band_array


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
        probability = pd.DataFrame(self.get_easting_northing_flood_probability(easting, northing))
        probability.columns = ['Probability Band']

        # import postcode
        postcodes = pd.DataFrame(postcodes)
        postcodes.columns = ['Postcode']

        # join two data frames
        postcode = pd.concat([postcodes, probability])
        postcodes = postcodes.set_index('Postcode')
        postcode = postcode[postcode['Postcode'] != 'numpy.nan']
        postcode = postcode.drop_duplicates(['Postcode'], keep='last')
        
        # format the postcode
        postcode['outward'] = postcode['Postcode'].apply(lambda x: x[0:4])
        postcode['outward'] = postcode['outward'].str.replace(" ", "")
        postcode['inward'] = postcode['Postcode'].apply(lambda x: x[4:7])
        postcode['Postcode'] = postcode['outward'] + ' ' + postcode['inward']
        postcode = postcode.drop('outward', 1)
        postcode = postcode.drop('inward', 1)

        # custom sorting
        postcode['Probability Band'] = pd.Categorical(postcode['Probability Band'], ["High", "Medium", "Low", "Very Low", "Zero"])

        # sort my column then index
        postcode = postcode.sort_values(by=['Probability Band', 'Postcode'])
        postcode = postcode.set_index('Postcode')

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
        cost = []
        postcodes = self.postcode_file['Postcode']
        a = len(postcode)
        
        #Postcode_test = ','.join(Postcode)
        Postcode = self.values_file['Postcode']
        Total_value = self.values_file['Total Value']

        #a = postcodes.count(',')
        #postcodes = postcodes.split(',')

        #print(postcodes[0])

        for i in range(a):
            if ' ' not in postcodes[i]:
                seq = (postcodes[i][:-3],postcodes[i][-3:])
                postcodes[i] = ' '.join(seq)

            if postcodes[i] in Postcode:
                p = Postcode.index(postcodes[i])
                cost.append(0.05 * float(Total_value[p]))
                print(cost[i])

            else:
                cost.append(np.nan)
                print(cost[i])

        return cost


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
        risk = []
        likelihood = []
        postcodes = self.get_sorted_flood_probability(postcodes)[:,0]
        probability_bands = self.get_sorted_flood_probability(postcodes)[:,1]
        
        Postcode = self.values_file['Postcode']

        a = len(postcodes)
        #postcodes_1 = postcodes.split(',')
        #probability_bands = probability_bands.split(',')
        #print(probability_bands)

        for i in range(a):
            if ' ' not in postcodes[i]:
                seq = (postcodes[i][:-3],postcodes[i][-3:])
                postcodes[i] = ' '.join(seq)
            else:
                pass

            if postcodes[i] in Postcode:
                if probability_bands[i] == 'Zero':
                    likelihood.append(0)
                elif probability_bands[i] == 'Very low':
                    likelihood.append(1/1000)
                elif probability_bands[i] == 'Low':
                    likelihood.append(1/100)
                elif probability_bands[i] == 'Medium':
                    likelihood.append(1/50)
                elif probability_bands[i] == 'High':
                    likelihood.append(1/10)
            else:
                return np.nan

            #print(postcodes)
            risk.append(likelihood[i] * get_flood_cost(postcodes)[i])
            #print(risk[i])

        return risk
        

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
        easting, northing = geo.get_easting_northing_from_lat_long(latitude, longitude, radians=False)
        probability_bands = self.get_easting_northing_flood_probability(easting, northing)
        risk = pd.DataFrame(self.get_annual_flood_risk(postcodes, probability_bands))
        risk.columns = ['Flood Risk']

        # import postcode
        postcodes = pd.DataFrame(postcodes)
        postcodes.columns = ['Postcode']

        # join two data frames
        postcode = pd.concat([postcodes, risk])
        postcodes = postcodes.set_index('Postcode')
        postcode = postcode[postcode['Postcode'] != 'numpy.nan']
        postcode = postcode.drop_duplicates(['Postcode'], keep='last')
        
        # format the postcode
        postcode['outward'] = postcode['Postcode'].apply(lambda x: x[0:4])
        postcode['outward'] = postcode['outward'].str.replace(" ","")
        postcode['inward'] = postcode['Postcode'].apply(lambda x: x[4:7])
        postcode['Postcode'] = postcode['outward'] + ' ' + postcode['inward']
        postcode = postcode.drop('outward', 1)
        postcode = postcode.drop('inward', 1)

        # sort my column then index
        postcode = postcode.sort_values(by=['Probability Band', 'Postcode'], ascending=[False, True])
        postcode = postcode.set_index('Postcode')
        return postcode
