"""
Created on May 20, 2010

@author: pierregm
"""

import numpy as np


def select_stations_around_reference(stations, reference_longitude, reference_latitude, distance):
    """
    Select stations around a given point of reference

    Parameters
    ----------
    stations: ndarray
        A structured ndarray of stations. 
        The dtype of the array must at least contains the fields `'lat'` (for
        the latitude in decimal degrees) and `'lon'` (longitude in decimal degrees).
    reference_longitude: float
        Longitude of the reference point (in decimal degrees)
    reference_latitude: float
        Latitude of the reference point (in decimal degrees).
    distance: float
        Maximum distance around the reference (in miles)

    Returns
    -------
    selected_Stations: ndarray
        A structured ndarray of selected stations, with the same dtype as 
        the input ndarray and an additional field `'distance_from_ref'`.
    """
    equatorial_radius = 6378.137 / 1.609344
    deg_to_rad = np.pi / 180.
    # Get the coordinates of the reference in radians
    dlat_r = reference_latitude * deg_to_rad
    dlon_r = reference_longitude * deg_to_rad
    # Get the coordinates of the stations in radians
    dlat = stations['lat'] * deg_to_rad
    dlon = stations['lon'] * deg_to_rad
    # Compute the angular distances from the reference
    d = np.sin((dlat - dlat_r) / 2.) ** 2 + \
        np.cos(dlat) * np.cos(dlat_r) * np.sin((dlon - dlon_r) / 2.) ** 2
    d = 2 * np.arcsin(np.sqrt(d))
    # Reset to distances in mi
    d *= equatorial_radius
    # Find the stations at the appropriate distance
    selection = np.array((d <= distance), dtype=bool)
    stations = stations[selection]
    stations_dtype = stations.dtype
    ndtype = stations_dtype.descr + [('distance_from_ref', float)]
    selected_stations = np.empty(len(stations), dtype=ndtype)
    for name in stations_dtype.names:
        selected_stations[name] = stations[name]
    selected_stations['distance_from_ref'] = d[selection]
    selected_stations.sort(order='distance_from_ref')
    return selected_stations


def decimal_to_dms(a, tol=1e-6):
    """
    Transforms a decimal coordinate in a tuple (degrees, minutes, seconds)

    Parameters
    ----------
    a
    """

    a = np.array(a)
    (dd, mm) = divmod(np.abs(a), 1)
    problems = np.allclose(mm, 1, rtol=tol)
    if problems.any():
        try:
            np.putmask(mm, problems, 0)
            np.putmask(dd, problems, dd + 1)
        except TypeError:
            (dd, mm) = (dd + 1, 0)
    dd *= np.sign(a)
    (mm, ss) = divmod(mm * 60., 1.)
    problems = np.allclose(ss, 1., rtol=tol)
    if problems.any():
        try:
            np.putmask(ss, problems, 0)
            np.putmask(mm, problems, mm + 1)
        except TypeError:
            (mm, ss) = (mm + 1, 0)
    ss *= 60.
    return (dd, mm, ss)


def dms_to_decimal(dd, mm, ss):
    """
    Transforms a coordinate in (degrees, minutes, seconds) to decimal
    """
    (dd, mm, ss) = np.array([_ for _ in (dd, mm, ss)])
    rescale = np.sign(dd)
    dd = np.abs(dd)
    return rescale * (dd + mm / 60. + ss / 3600.)


def print_decimal_coordinates(coord, is_lat=True):
    """
    Given a decimal coordinate, returns a string in degree/minute/second
    """
    template = u"%(dd)02i\xB0%(letter)s %(mm)02i' %(ss)5.3f\""
    if is_lat:
        if coord >= 0:
            letter = "N"
        else:
            letter = "S"
    elif coord > 0:
        letter = "E"
    else:
        letter = "W"
    (dd, mm, ss) = decimal_to_dms(coord)
    dd = abs(dd)
    return template % locals()


from numpy.ma.testutils import *
if 1:
#def test_dms_to_decimal():
        "Test conversion between decimal and DDMMSS coordinates"
        coords = (31, 30, 0)
        test = dms_to_decimal(*coords)
        assert_almost_equal(decimal_to_dms(dms_to_decimal(*coords)),
                            np.array(coords))
        assert_almost_equal(test, 31.5)
        #
        coords = (-81, 30, 18)
        test = dms_to_decimal(*coords)
        assert_almost_equal(decimal_to_dms(dms_to_decimal(*coords)),
                            np.array(coords))
        assert_almost_equal(test, -81.505)

#def test_decimal_to_dms():
        coords = -81.505
        test = decimal_to_dms(coords)
        assert_almost_equal(test, np.array((-81, 30, 18)))
        #
        coords = 30.4
        test = decimal_to_dms(coords)
        assert_almost_equal(test, np.array((30, 24, 0)))
        #
        coords = -31.999999999999999
        test = decimal_to_dms(coords)
        assert_almost_equal(test, np.array((-32, 0, 0)))


#def test_print_dms():
        coord = -81.505
        test = print_decimal_coordinates(coord, is_lat=False)
        ctrl = u"81\xB0W 30' 18.000\""
        assert_equal(test, ctrl)
