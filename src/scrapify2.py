#!/usr/bin/python3
from spotipy import Spotify, util, client, oauth2
import sqlite3
import os
import sys
from pathlib import Path
import json

user = 'nishumvar'
scopes = "playlist-read-private playlist-read-collaborative user-follow-read user-library-read \
user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state \
user-read-currently-playing user-read-recently-played"
ccm = None
sp = Spotify()
dbname = "tpy.db"
db = None

dirs = {}

def ScrapeSetup():
    dirSetup(os.getcwd(), 'raw')
    dirSetup(dirs['raw'], 'savedtracks')
    dirSetup(dirs['raw'], 'savedalbums')
    dirSetup(dirs['raw'], 'savedartists')
    dirSetup(dirs['raw'], 'tracks')
    dirSetup(dirs['raw'], 'artists')
    dirSetup(dirs['raw'], 'albums')
    dirSetup(dirs['raw'], 'playlists')
    dirSetup(dirs['raw'], 'topartists_shortterm')
    dirSetup(dirs['raw'], 'topartists_mediumterm')
    dirSetup(dirs['raw'], 'topartists_longterm')
    dirSetup(dirs['raw'], 'toptracks_shortterm')
    dirSetup(dirs['raw'], 'toptracks_mediumterm')
    dirSetup(dirs['raw'], 'toptracks_longterm')

def dirSetup(p, s):
    dirs[s] = os.path.join(p, s)
    try:
        os.makedirs(dirs[s])
    except FileExistsError:
        pass
    return

def SaveJson(dir, fname, data):
    try:
        p = os.path.join(dir, fname)
        f = None
        if os.path.exists(p):
            os.unlink(p)
        f = open(p, 'w')
        print("writing to this file: {0}".format(p))
        json.dump(data, f)
        f.flush()
        f.close()
        return True
    except:
        return False
        
def RefreshSpotifyTokens():
    global sp, ccm
    if not os.path.exists('./.cache-'+user):
        access = util.prompt_for_user_token(user, scopes)
        sp = Spotify(auth=access['access_token'])
        return
    elif ccm is None:
        ccm = oauth2.SpotifyOAuth(
            os.getenv("SPOTIPY_CLIENT_ID"), os.getenv("SPOTIPY_CLIENT_SECRET"), os.getenv("SPOTIPY_REDIRECT_URI"), 
            cache_path='./.cache-nishumvar', scope=scopes)
    access = ccm.get_cached_token()
    sp = Spotify(auth=access['access_token'])
    return

def GetPage(func, endpoint_full, endpoint_short, off = 0, lim = 50):
    page = func(lim, off)
    print("Tried to fetch {2} offset {0}, limit {1}".format(off, lim, endpoint_full))
    if not page:
        print("Failed to retrieve page")
        return False
    else:
        print("Retrieved page, saving to disk")
        didSave = SaveJson(dirs[endpoint_short], "{2}_{0}_{1}.json".format(lim, off, endpoint_short), page)
        return page['next'] or not didSave

def GetAllPage(func, endpoint_full, endpoint_short):
    Cont = True
    offset = 0
    limit = 50
    while(Cont):
        Cont = GetPage(func, endpoint_full, endpoint_short, offset, limit)
        offset += limit
    print("Fetched All " + endpoint_full)

def GetFullItem(func, type, id):
    t = "{0}:{1}".format(type,id)
    dirs[t] = os.path.join(dirs['raw'], type+'s', id)
    try:
        os.makedirs(dirs[t])
    except FileExistsError:
        pass
       
def GetFullPlaylist(userid, id):
    p = os.path.join(dirs['raw'], 'playlists', id)
    ptracks = os.path.join(p, 'tracks')
    if not os.path.exists(p):
        os.makedirs(p)
        os.makedirs(ptracks)
    full = sp.user_playlist(userid, id)
    if not full:
        print("failed to get the full item")
        return False
    else:
        print ("Got the full item, saving...")
        return SaveJson(p, 'PlaylistDetails_{0}.json'.format(id), full)

def GetPlaylistsTracks(userid, id):
    p = os.path.join(dirs['raw'], 'playlists', id, 'tracks')
    if not os.path.exists(p):
        os.makedirs(p)
    Cont = True
    off = 0
    lim = 100
    while(Cont):
        page = sp.user_playlist_tracks(userid, id, limit=lim, offset=off)
        print("Tried to fetch {2} offset {0}, limit {1}".format(off, lim, "playlists tracks"))
        if not page:
            print("Failed to retrieve page")
            return False
        else:
            print("Retrieved page, saving to disk")
            didSave = SaveJson(p, "{2}_tracks_{0}_{1}.json".format(lim, off, id), page)
            Cont = page['next'] and didSave
            off += lim
    print("Fetched All Playlist Tracks: " + id)
    return True

def LoadAndReadPlaylists():
    p = dirs['playlists']
    pages = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]
    pls = []# (userid, playlistid)
    for page in pages:
        j = json.load(open(os.path.join(p, page), 'r'))
        for pl in j['items']:
            owner = pl['owner']['id']
            id = pl['id']
            pls.append((owner, id))
    return pls

def GetFullPlaylists():
    pls = LoadAndReadPlaylists()
    Cont = True
    for pl in pls:
        if not Cont:
            break
        else:
            Cont = GetFullPlaylist(pl[0], pl[1])

def GetFullPlaylistTracks():
    pls = LoadAndReadPlaylists()
    Cont = True
    for pl in pls:
        if not Cont:
            break
        else:
            Cont = GetPlaylistsTracks(pl[0], pl[1])

def AcquireInitialJson():
    #GetAllPage(sp.current_user_saved_tracks, "Saved Tracks", "savedtracks")
    #GetAllPage(sp.current_user_saved_albums, "Saved Albums", "savedalbums")
    #GetAllPage(sp.current_user_playlists, "Saved Playlists", "playlists")
    #GetFullPlaylists()
    #GetFullPlaylistTracks()
    return

def main():
    RefreshSpotifyTokens()
    ScrapeSetup()
    #AcquireInitialJson()
    return

if __name__ == '__main__':
    main()



# Scrape Saved Songs
