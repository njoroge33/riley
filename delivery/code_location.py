from math import sin, cos, sqrt, atan2, radians
from geopy.geocoders import Nominatim
import json
import datetime

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
    return round(distance, 1)

def get_duration(start, stop):

    fmt = '%Y-%m-%d %H:%M:%S'

    start_time =datetime.datetime.strptime(start.strftime(fmt) , fmt)
    stop_time = datetime.datetime.strptime(stop.strftime(fmt) , fmt)
    diff_minutes = int((stop_time - start_time).total_seconds() // 60)
    duration = str(datetime.timedelta(minutes= diff_minutes)).split(':')

    if duration[0] == "0":
        return duration[1] + ' minutes'
    else:
        return duration[0] + ' hours' + ' ' + duration[1] + ' minutes'

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    

    