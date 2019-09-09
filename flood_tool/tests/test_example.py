"""Test Module."""

import flood_tool
import numpy as np

def test_postcode_locator():

    loc = flood_tool.PostcodeLocator()

    assert (loc.get_postcode([[-0.176923, 51.498317]]) == np.array(['SW7 2AZ'])).all()

    assert (loc.get_long_lat(['SW7 2AZ']) == np.array([[-0.176923, 51.498317]])).all()

    assert (loc.get_easting_northing(['SW7 2AZ']) == np.array([[526645, 179284]])).all()

    
