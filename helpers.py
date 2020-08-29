import os
import re
import json
from flask import redirect, render_template, request, session
from functools import wraps
from ipstack import GeoLookup
import socket
import urllib

def sorry(message):
    return render_template("sorry.html", message=message)

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def location():
    # IPAddr = socket.gethostbyname(urllib.request.urlopen("https://ip.42.pl/raw").read())
    # geo_lookup = GeoLookup(os.getenv("API_KEY"))
    # location = geo_lookup.get_location(IPAddr)
    url = 'http://ipinfo.io/json'
    response = urllib.request.urlopen(url)
    data = json.load(response)
    city = data['city']
    country=data['country']
    return (city, country)

