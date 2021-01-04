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
    