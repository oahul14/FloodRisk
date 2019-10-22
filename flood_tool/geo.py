"""Module implementing various geodetic transformation functions."""
import numpy as np
from numpy import array, sin, cos, tan, sqrt, pi, arctan2, floor

__all__ = ['get_easting_northing_from_lat_long',
           'WGS84toOSGB36']

class Ellipsoid(object):
    """Class acting as container for properties describing a terrestrial ellipsoid."""
    def __init__(self, a, b, F_0):
        self.a = a
        self.b = b
        self.n = (a-b)/(a+b)
        self.e2 = (a**2-b**2)/a**2
        self.F_0 = F_0
        self.H=0

class Datum(Ellipsoid):
    """Class acting as container for properties describing a map datum."""

    def __init__(self, a, b, F_0, phi_0, lam_0, E_0, N_0, H):
        super().__init__(a, b, F_0)
        self.phi_0 = phi_0
        self.lam_0 = lam_0
        self.E_0 = E_0
        self.N_0 = N_0
        self.H = H

def rad(deg, min=0, sec=0):
    """Convert degrees into radians."""
    return (deg+min/60.+sec/3600.)*(pi/180.)

def deg(rad, dms=False):
    """Convert radians into degrees."""
    d = rad*(180./pi)
    if dms:
        m = 60.0*(d%1.)
        return floor(d),  floor(m), round(60*(m%1.),4)
    else:
        return d

# Datum for the Ordenance Survey GB 1936 Datum, as used in the OS
# National grid

osgb36 = Datum(a = 6377563.396,
               b = 6356256.910,
               F_0 = 0.9996012717,
               phi_0 = rad(49.0),
               lam_0 = rad(-2.),
               E_0 = 400000,
               N_0 = -100000,
               H=24.7)

# Ellipsoid used for the WGS 1984 datum (i.e. for GPS coordinates)

wgs84 = Ellipsoid(a = 6378137, 
                  b = 6356752.3142,
                  F_0 = 0.9996)

def lat_long_to_xyz(latitude, longitude, radians=False, datum=osgb36):
    """Convert locations in latitude and longitude format to 3D on specified datum.

    Input arrays must be of matching length.
    
    Parameters
    ----------

    latitude: numpy.ndarray of floats
        latitudes to convert
    latitude: numpy.ndarray of floats
        latitudes to convert
    radians: bool, optional
        True if input is in radians, otherwise degrees assumed.
    datum: geo.Ellipsoid, optional
        Geodetic ellipsoid to work on

    Returns
    -------

    numpy.ndarray
        Locations in 3D (body Cartesian) coordinates.
    """
    if not radians:
        latitude = rad(latitude)
        longitude = rad(longitude)

    #nu = datum.a*datum.F_0/sqrt(1-datum.e2*sin(latitude)**2)
    nu = datum.a/sqrt(1-datum.e2*sin(latitude)**2)
  
    return array(((nu+datum.H)*cos(latitude)*cos(longitude),
                  (nu+datum.H)*cos(latitude)*sin(longitude),
                  ((1-datum.e2)*nu+datum.H)*sin(latitude)))

def xyz_to_lat_long(x, y, z, radians=False, datum=osgb36):
    """Convert locations in 3D to latitude longitude format on specified datum.

    Input arrays must be of matching length.
    
    Parameters
    ----------

    x: numpy.ndarray of floats
        x coordinate in body Cartesian 3D
    y: numpy.ndarray of floats
        z coordinate in body Cartesian 3D
    z: numpy.ndarray of floats
        z coordinate in body Cartesian 3D
    radians: bool, optional
        True if output should be in radians, otherwise degrees assumed.
    datum: geo.Ellipsoid, optional
        Geodetic ellipsoid to work on

    Returns
    -------

    latitude: numpy.ndarray
        Locations latitudes.
    longitude: numpy.ndarray
        Locations longitudes.
    """
    p = sqrt(x**2+y**2)

    ### invert for longitude
    longitude = arctan2(y, x)

    ### first guess at longitude
    latitude = arctan2(z,p*(1-datum.e2))

    ### Apply a few iterations of Newton Rapheson
    for _ in range(6):
        # nu = datum.a*datum.F_0/sqrt(1-datum.e2*sin(latitude)**2)
        nu = datum.a/sqrt(1-datum.e2*sin(latitude)**2)
        # dnu = -datum.a*datum.F_0*cos(latitude)*sin(latitude)/(1-datum.e2*sin(latitude)**2)**1.5
        dnu = -datum.a*cos(latitude)*sin(latitude)/(1-datum.e2*sin(latitude)**2)**1.5

        f0 = (z + datum.e2*nu*sin(latitude))/p - tan(latitude)
        f1 = datum.e2*(nu**cos(latitude)+dnu*sin(latitude))/p - 1.0/cos(latitude)**2
        latitude -= f0/f1

    if not radians:
        latitude = deg(latitude)
        longitude = deg(longitude)

    return latitude, longitude

class HelmertTransform(object):
    """Class to perform a Helmert Transform mapping (x,y,z) tuples from one datum to another.""" 
    
    def __init__(self, s, rx, ry, rz, T):

        self.T = T.reshape((3,1))
        
        self.M = array([[1+s, -rz, ry],
                        [rz, 1+s, -rx],
                        [-ry, rx, 1+s]])

    def __call__(self, X):
        """ Transform a point or point set using the Helmert Transform."""
        return self.T + self.M.dot(X.reshape((3,-1)))

WGS84toOSGB36transform = HelmertTransform(20.4894e-6,
                             -rad(0,0,0.1502),
                             -rad(0,0,0.2470),
                             -rad(0,0,0.8421),
                             array([-446.448, 125.157, -542.060]))



def WGS84toOSGB36(latitude, longitude, radians=False):
    """ Wrapper to transform (latitude, longitude) pairs from GPS to OS datum.
    
    Parameters
    ---------
    latitude: numpy.ndarray of floats
        latitudes to convert
    longitudes: numpy.ndarray of floats
        longitudes to convert
    radians: bool, optional
        True if input is in radians, otherwise degrees assumed.
    
    Returns
    -------
    latitudes: numpy.ndarray of floats
        OS latitudes in deg
    longitudes: numpy.ndarray of floats
        OS longitude in deg
    """
    if not radians:
        latitude = rad(latitude)
        longitude = rad(longitude)
    #convert WGS lat long to WGS X 
    Xwgs = lat_long_to_xyz(latitude, longitude, radians=True, datum=wgs84)
    #convert WGS X to OSGB X
    Xosgb = WGS84toOSGB36transform(Xwgs) 
    #convert Xosgb to OSGB lat long
    Lat_OS, Long_OS = xyz_to_lat_long(Xosgb[0], Xosgb[1], Xosgb[2], radians=True, datum=osgb36)

    return Lat_OS, Long_OS 


def get_easting_northing_from_lat_long(latitude, longitude, radians=False):
    """ Convert GPS (latitude, longitude) to OS (easting, northing).
    
    Parameters
    ----------
    latitude : sequence of floats
               Latitudes to convert.
    longitude : sequence of floats
                Lonitudes to convert.
    radians : bool, optional
              Set to `True` if input is in radians. Otherwise degrees are assumed
    
    Returns
    -------

    easting : ndarray of floats
              OS Eastings of input
    northing : ndarray of floats
              OS Northings of input

    References
    ----------

    A guide to coordinate systems in Great Britain 
    (https://webarchive.nationalarchives.gov.uk/20081023180830/http://www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/index.html)
    """ 
    #unit conversion
    if not radians:
        latitude = rad(latitude)
        longitude = rad(longitude)

    #convert WGS lat long to OS lat long
    Lat_OS, Long_OS = WGS84toOSGB36(latitude, longitude,radians=True)

    #convert OS lat long to Easting Northing
    rho = osgb36.a*osgb36.F_0*(1-osgb36.e2)/((1-osgb36.e2*sin(Lat_OS)**2)**(1.5))
    v = osgb36.a*osgb36.F_0/sqrt(1-osgb36.e2*sin(Lat_OS)**2)
    eta = sqrt(v/rho - 1)
    M = osgb36.b*osgb36.F_0*( 
        (1 + osgb36.n + 5/4*osgb36.n**2 + 5/4*osgb36.n**3)*(Lat_OS - osgb36.phi_0) - 
        (3*osgb36.n + 3*osgb36.n**2 + 21/8*osgb36.n**3)*sin(Lat_OS - osgb36.phi_0)*
        cos(Lat_OS + osgb36.phi_0) + (15/8*osgb36.n**2 + 15/8*osgb36.n**3)*
        sin(2*(Lat_OS - osgb36.phi_0))*cos(2*(Lat_OS + osgb36.phi_0)) - 35/24*
        osgb36.n**3*sin(3*(Lat_OS - osgb36.phi_0))*cos(3*(Lat_OS + osgb36.phi_0))
        )
    I = M + osgb36.N_0
    II = v/2*sin(Lat_OS)*cos(Lat_OS)
    III = v/24*sin(Lat_OS)*cos(Lat_OS)**3*(5 - tan(Lat_OS)**2 + 9*eta**2)
    IIIA = v/720*sin(Lat_OS)*cos(Lat_OS)**5*(61 - 58*tan(Lat_OS)**2 + tan(Lat_OS)**4)
    IV = v*cos(Lat_OS)
    V = v/6*cos(Lat_OS)**3*(v/rho - tan(Lat_OS)**2)
    VI = v/120*cos(Lat_OS)**5*(5 - 18*tan(Lat_OS)**2 + tan(Lat_OS)**4 + 14*eta**2 - 
        58*tan(Lat_OS)**2*eta**2 )
    
    E_OS = osgb36.E_0 + IV*(Long_OS - osgb36.lam_0) + V*(Long_OS - osgb36.lam_0)**3 + VI*(
        (Long_OS - osgb36.lam_0)**5)
    N_OS = I + II*(Long_OS - osgb36.lam_0)**2 + III*(Long_OS - osgb36.lam_0)**4 + IIIA*(
        (Long_OS - osgb36.lam_0)**6)
    return E_OS, N_OS 


# results = (get_easting_northing_from_lat_long(np.array([51.19707,51.271972]),np.array([1.385194,0.565622])))
# print(results[0])