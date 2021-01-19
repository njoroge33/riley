from math import sin, cos, sqrt, atan2, radians
from geopy.geocoders import Nominatim
import json

def code_location(location_name):
    geolocator = Nominatim(user_agent="deli")
    location = geolocator.geocode(location_name)
    print(location.address)
    address = location.address
    lat = location.latitude
    long = location.longitude
    # {"address": str(location.address), "lat": str(location.latitude), "long": str(location.longitude)}
    loc = dict()
    loc["address"] = address
    loc["lat"] = lat
    loc["long"] = long
    print(loc)
    return loc

def get_distance(start, stop):
    R = 6373.0

    lat1 = radians(start['lat'])
    lon1 = radians(start['long'])
    lat2 = radians(stop['lat'])
    lon2 = radians(stop['long'])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 2)

    