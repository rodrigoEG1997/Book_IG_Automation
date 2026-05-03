import requests

def get_long_token(APP_ID, APP_SECRET, SHORT_TOKEN):

    url = "https://graph.facebook.com/v25.0/oauth/access_token"

    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": SHORT_TOKEN
    }

    response = requests.get(url, params=params)

    return response.json()

def refresh_token(APP_ID, APP_SECRET, LONG_TOKEN):
    url = "https://graph.facebook.com/v25.0/oauth/access_token"

    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": LONG_TOKEN
    }

    response = requests.get(url, params=params)
    return response.json()