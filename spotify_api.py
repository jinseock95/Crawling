# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import requests
import pandas as pd
import logging
import csv

global client_id
global client_secret

with open(os.path.join('..', 'Config.json'), 'r') as f:
    config = json.load(f)

client_id = config['Spotify']['client_id']
client_secret = config['Spotify']['client_secret']

def main():
    # artist_list = pd.read_csv('artist_list.csv', header = None)

    artists = []
    with open('artist_list.csv') as f:
        line = csv.reader(f)
        for l in line:
            artists.append(l[0])

    artistInfo = [get_artistInfo(artist) for artist in artists[:3]]

# API 접속
def get_API(url, headers, params = None):
    response = requests.get(url, params = params, headers = headers)

    try:
        response.json()
        return response

    except:
        return get_API(url, params, headers)
        
# headers
def get_headers(client_id, client_secret):

    endpoint = "https://accounts.spotify.com/api/token" # access token을 받기 위한 endpoint
    encoded = base64.b64encode("{}:{}".format(client_id, client_secret).encode('utf-8')).decode('ascii') # client_id 와 secret을 utf-8로 인코딩

    headers = {
        "Authorization": "Basic {}".format(encoded)
    }

    payload = {
        "grant_type": "client_credentials"
    }

    response = requests.post(endpoint, data = payload, headers = headers)
    try:
        data = json.loads(response.text)
    except:
        time.sleep(1)
        response = requests.post(endpoint, data = payload, headers = headers)
        data = json.loads(response.text)

    access_token = data['access_token']
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    return headers

# artist 아이디 수집
def get_artistID(query):
    endpoint = 'https://api.spotify.com/v1/search'
    headers = get_headers(client_id, client_secret)

    params = {
        'q' : query,
        'type' : 'artist',
        'limit' : 1
    }

    try:
        response = get_API(endpoint, params = params, headers = headers)
    except:
        logging.error(response.text)
        sys.exit(1)
        return 'ID error'

    if response.status_code != 200:

        if response.status_code == 429:
            logging.error(response.text)
            retry_time = json.loads(response.headers)['Retry-After']
            time.sleep(int(retry_time))
            response = get_API(endpoint, params = params, headers = headers)

        elif response.status_code == 401:
            logging.error(response.text)
            headers = get_headers(client_id, client_secret)
            response = get_API(endpoint, params = params, headers = headers)

        else:
            print(response.status_code, 'error')
            logging.error(response.text)
        
    artistId = json.loads(response.text)['artists']['items'][0]['id']
    return artistId

# artist 정보 수집
def get_artistInfo(query):
    try:
        artistId = get_artistID(query)
    except:
        return 'ID error'
    
    endpoint = 'https://api.spotify.com/v1/artists/{}'.format(artistId)
    headers = get_headers(client_id, client_secret)

    response = get_API(endpoint, headers = headers)
    data = json.loads(response.text)
    res = {}

    res['id'] = artistId
    res['name'] = data.get('name', None)
    res['followers'] = data['followers'].get('total', None)
    res['genres'] = '|'.join(data.get('genres', None))
    res['popularity'] = data.get('popularity', None)
    res['url'] = data.get('uri', None)
    try:
        res['image_url'] = data['images'][0].get('url', None)
    except:
        res['image_url'] = None

    return res

# 앨범 track 정보 수집
def get_tracks(artist_id, params):
    headers = get_headers(client_id, client_secret)
    endpoint = 'https://api.spotify.com/v1/artists/{}/top-tracks'.format(artist_id)

    response = get_API(endpoint, params = params, headers = headers)
    data = response.json()
    tracks = data['tracks']

    return tracks

def get_audio(artist_id):
    headers = get_headers(client_id, client_secret)
    endpoint = "https://api.spotify.com/v1/audio-features/?ids={}".format(artist_id)

    response = get_API(endpoint, headers = headers)
    data = response.json()
    audio = data['audio_features']

    return audio


if __name__ == '__main__':
    main()
