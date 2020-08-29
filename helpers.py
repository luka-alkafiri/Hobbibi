import os
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
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    geo_lookup = GeoLookup(os.getenv("API_KEY"))
    location = geo_lookup.get_location(IPAddr)
    return (location["city"], location["country_name"])


# def ip():
#     hostname = socket.gethostname()
#     ## getting the IP address using socket.gethostbyname() method
#     ip_address = socket.gethostbyname(hostname)
#     ## printing the hostname and ip_address
#     print(f"IP Address: {ip_address}")

