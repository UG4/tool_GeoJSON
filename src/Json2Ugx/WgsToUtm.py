#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 20:17:10 2024

@author: zhongqiuyan

mathematic transform about WGS to UTM

"""




#import geojson
import pandas as pd
from utm.error import OutOfRangeError
#from math import cos, sin, tan, sqrt
import math
import utm
from pyproj import Proj, transform



# For most use cases in this module, numpy is indistinguishable
# from math, except it also works on numpy arrays
# Convert wgs84 to utm
try:
    import numpy as mathlib
    use_numpy = True
except ImportError:
    import math as mathlib
    use_numpy = False

__all__ = ['from_latlon']

K0 = 0.9996

E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1 - E)


M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
M3 = (15 * E2 / 256 + 45 * E3 / 1024)
M4 = (35 * E3 / 3072)


R = 6378137

ZONE_LETTERS = "CDEFGHJKLMNPQRSTUVWXX"




def in_bounds(x, lower, upper, upper_strict=False):
    if upper_strict and use_numpy:
        return lower <= mathlib.min(x) and mathlib.max(x) < upper
    elif upper_strict and not use_numpy:
        return lower <= x < upper
    elif use_numpy:
        return lower <= mathlib.min(x) and mathlib.max(x) <= upper
    return lower <= x <= upper


def check_valid_zone(zone_number, zone_letter):
    if not 1 <= zone_number <= 60:
        raise OutOfRangeError(
            'zone number out of range (must be between 1 and 60)')

    if zone_letter:
        zone_letter = zone_letter.upper()

        if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            raise OutOfRangeError(
                'zone letter out of range (must be between C and X)')


def mixed_signs(x):
    return use_numpy and mathlib.min(x) < 0 and mathlib.max(x) >= 0


def negative(x):
    if use_numpy:
        return mathlib.max(x) < 0
    return x < 0


def mod_angle(value):
    """Returns angle in radians to be between -pi and pi"""
    return (value + mathlib.pi) % (2 * mathlib.pi) - mathlib.pi


def from_latlon(latitude, longitude, force_zone_number=None, force_zone_letter=None):
    """This function converts Latitude and Longitude to UTM coordinate

        Parameters
        ----------
        latitude: float or NumPy array
            Latitude between 80 deg S and 84 deg N, e.g. (-80.0 to 84.0)

        longitude: float or NumPy array
            Longitude between 180 deg W and 180 deg E, e.g. (-180.0 to 180.0).

        force_zone_number: int
            Zone number is represented by global map numbers of an UTM zone
            numbers map. You may force conversion to be included within one
            UTM zone number.  For more information see utmzones [1]_

        force_zone_letter: str
            You may force conversion to be included within one UTM zone
            letter.  For more information see utmzones [1]_

        Returns
        -------
        easting: float or NumPy array
            Easting value of UTM coordinates

        northing: float or NumPy array
            Northing value of UTM coordinates

        zone_number: int
            Zone number is represented by global map numbers of a UTM zone
            numbers map. More information see utmzones [1]_

        zone_letter: str
            Zone letter is represented by a string value. UTM zone designators
            can be accessed in [1]_


       .. _[1]: http://www.jaworski.ca/utmzones.htm
    """
    if not in_bounds(latitude, -80, 84):
        raise OutOfRangeError(
            'latitude out of range (must be between 80 deg S and 84 deg N)')
    if not in_bounds(longitude, -180, 180):
        raise OutOfRangeError(
            'longitude out of range (must be between 180 deg W and 180 deg E)')
    if force_zone_number is not None:
        check_valid_zone(force_zone_number, force_zone_letter)

    lat_rad = mathlib.radians(latitude)
    lat_sin = mathlib.sin(lat_rad)
    lat_cos = mathlib.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    if force_zone_number is None:
        zone_number = latlon_to_zone_number(latitude, longitude)
    else:
        zone_number = force_zone_number

    if force_zone_letter is None:
        zone_letter = latitude_to_zone_letter(latitude)
    else:
        zone_letter = force_zone_letter

    lon_rad = mathlib.radians(longitude)
    central_lon = zone_number_to_central_longitude(zone_number)
    central_lon_rad = mathlib.radians(central_lon)

    n = R / mathlib.sqrt(1 - E * lat_sin**2)
    c = E_P2 * lat_cos**2

    a = lat_cos * mod_angle(lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * mathlib.sin(2 * lat_rad) +
             M3 * mathlib.sin(4 * lat_rad) -
             M4 * mathlib.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if mixed_signs(latitude):
        raise ValueError("latitudes must all have the same sign")
    elif negative(latitude):
        northing += 10000000

    return easting, northing, zone_number, zone_letter
# wgs84 (longitude,latitude)---- utm (northing,easting,zone number,zone letter)


def latitude_to_zone_letter(latitude):
    # If the input is a numpy array, just use the first element
    # User responsibility to make sure that all points are in one zone
    if use_numpy and isinstance(latitude, mathlib.ndarray):
        latitude = latitude.flat[0]

    if -80 <= latitude <= 84:
        return ZONE_LETTERS[int(latitude + 80) >> 3]
    else:
        return None


def latlon_to_zone_number(latitude, longitude):
    # If the input is a numpy array, just use the first element
    # User responsibility to make sure that all points are in one zone
    if use_numpy:
        if isinstance(latitude, mathlib.ndarray):
            latitude = latitude.flat[0]
        if isinstance(longitude, mathlib.ndarray):
            longitude = longitude.flat[0]

    if 56 <= latitude < 64 and 3 <= longitude < 12:
        return 32

    if 72 <= latitude <= 84 and longitude >= 0:
        if longitude < 9:
            return 31
        elif longitude < 21:
            return 33
        elif longitude < 33:
            return 35
        elif longitude < 42:
            return 37

    return int((longitude + 180) / 6) + 1


def zone_number_to_central_longitude(zone_number):
    return (zone_number - 1) * 6 - 180 + 3


def check_to_from_latlon(first_number, second_number):
    try:
        def from_latlon(latitude, longitude, force_zone_number=None, force_zone_letter=None):
            print('THIS TYPE IS WGS84, NOT UTM !!')

        from_latlon(second_number, first_number)

    except Exception as e:
        return False


def get_mid_zone_number(country_utm_zones):
    #One country usually has several UTM zones 
    #Choose the middle value of the number of zones
    sorted_zones = sorted(country_utm_zones)
    middle_index = len(sorted_zones) // 2

    if len(sorted_zones) % 2 == 0:
        middle_zone = sorted_zones[middle_index - 1]
    else:
        middle_zone = sorted_zones[middle_index]

    return middle_zone


def is_southern_hemisphere(zone_letter):
    #If is southern hemisphere, then return true
    return 'C' <= zone_letter.upper() <= 'M'


def get_projection(zone_number, zone_letter):
    #Dynamically create the EPSG code based on zone number and zone letter
    hemisphere_code = 327 if is_southern_hemisphere(zone_letter) else 326
    epsg_code = f"EPSG:{hemisphere_code}{zone_number}"
    return Proj(init=epsg_code)



def get_utm_coordinates(not_repeat):
    #Convert utm(easting, northing, zone_number, zone_letter) to (x,y)
    #Alwasys need to consider the utm zone number and the utm zone letter


    first_number = not_repeat[0][0]
    second_number = not_repeat[0][1]
    # print(first_number,second_number)

    check_to_from_latlon(first_number, second_number)
    #print('WGS84 convert to UTM:','\n',utm.from_latlon(first_number, second_number))
  

    utm_results = []
    country_utm_zones = []

    for tuple_item in not_repeat:

        first_number = tuple_item[0]
        second_number = tuple_item[1]

        utm_coordinates = utm.from_latlon(second_number, first_number)
        utm_results.append(utm_coordinates)
        country_utm_zones.append(utm_coordinates[2])

    #print('nooooooo!! utm_results!!',utm_results,len(utm_results),'\n')
    #print('nooooooo!! country_utm_zones!!',country_utm_zones,len(country_utm_zones),'\n')



    target_zone = get_mid_zone_number(country_utm_zones)

    new_utm_results = []
    for easting, northing, zone_number, zone_letter in utm_results:
        #Dynamically creat source and target projections based on the UTM zones
        src_proj = get_projection(zone_number, zone_letter)
        dst_proj = get_projection(target_zone, zone_letter)

        #Use the projections to transform coordinates
        x, y = transform(src_proj, dst_proj, easting, northing)    

        if is_southern_hemisphere(zone_letter):
            y = y -10000000
            new_utm_results.append((x, y))
        else:
            new_utm_results.append((x, y))

        #new_utm_results.append((easting, northing))

    #print(';;;utm_results!!!', utm_results,
          #'\n', 'target_zone', target_zone, '\n')
   
    #print('nooooooo!! new_utm_results!!',
          #new_utm_results, len(new_utm_results), '\n')
   
    
    df_utm = pd.DataFrame(columns=['utm_results', 'new_utm_results'])
    df_utm['utm_results'] = utm_results
    df_utm['new_utm_results'] = new_utm_results
    print('df_utm',df_utm)
    
    new_utm_coor = []
    for coordinate in new_utm_results:
        x, y, *rest = coordinate
        new_utm_coor.append((x, y))
    print('new_utm_coor', new_utm_coor, '\n', len(new_utm_coor), '\n')

    return new_utm_coor











































