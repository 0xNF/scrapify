#!/usr/bin/python3
from spotipy import Spotify, util, client, oauth2
import sqlite3
import os
import sys
from pathlib import Path
import json
import re

user = 'nishumvar'
scopes = "playlist-read-private playlist-read-collaborative user-follow-read user-library-read \
user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state \
user-read-currently-playing user-read-recently-played"
ccm = None
sp = Spotify()
dbname = "tpy.db"
db = None

conn = sqlite3.connect(dbname)

ROrder = 1

# List of Directories to create and write json data to.
# Organized by Type. i.e.
# Playlists/{Playlist}/Tracks/{Tracks}
# Artists/{Artist}/Tracks/{Tracks}
#etc
dirs = {}

#Maps of which ResourceIds, organized by Type, that we've already seen and collected.   
CollectedArtists = []
CollectedAlbums = []
CollectedPlaylists = []
CollectedTracks = []
CollectedSavedTracks = []
CollectedSavedAlbums = []
CollectedUsers = []

# Queued resource ids to fetch Full versions of, and then append to StagedToAdd
QueuedArists = []
QueuedAlbums = []
QueuedPlaylists = []
QueuedTracks = []
QueuedSavedTracks = []
QueuedSavedAlbums = []
QueuedPlaylistTracks = []
QueuedUsers = []

# in-memory mappings
# format of:
#       {id : [list of ids]}
ArtistTrackMap = {}
ArtistAlbumMap = {}
AlbumTrackMap = {}
UserPlaylistMap = {}
UserSavedTracks = {}# [(added_at, trackid)

# Fully realized Json objects of items to add to respective tables
# Items moved from StagedToAdd get their ids appended to the appropriate Collected list
StagedToAdd_Tracks = []
StagedToAdd_Albums = []
StagedToAdd_Artists = []
StagedToAdd_SavedTracks = []
StagedToAdd_Playlists = []
StagedToAdd_PlaylistTracks = []
StagedToAdd_SavedAlbums = []
StagedToAdd_Users = []

def PopulateAlreadySeenItems():
    CollectedArtists = populate("ArtistId", "Artists")
    CollectedAlbums = populate("AlbumId", "Albums")
    CollectedPlaylists = populate("PlaylistId", "Playlists")
    CollectedTracks = populate("TrackId", "Tracks")
    CollectedUsers = populate("UserId", "Users")
    return

def populate(pkey, table):
    c = conn.cursor()
    q = "SELECT ? FROM {};".format(table)
    vals = (pkey,)
    c.execute(q, vals)
    ids = []
    for res in c.fetchall():
        ids.append(res)
    c.close()
    print("Found {} {} already fully populated in".format(len(ids), table))
    return ids

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)] 

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
    cachefname = './.cache-{}'.format(user)
    if not os.path.exists(cachefname):
        access = util.prompt_for_user_token(user, scopes)
        sp = Spotify(auth=access['access_token'])
        return
    elif ccm is None:
        ccm = oauth2.SpotifyOAuth(
            os.getenv("SPOTIPY_CLIENT_ID"), os.getenv("SPOTIPY_CLIENT_SECRET"), os.getenv("SPOTIPY_REDIRECT_URI"), 
            cache_path=cachefname, scope=scopes)
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

Artists_InsertedAsSimple = []
def InsertArtist(artist):
    q = "INSERT OR IGNORE INTO Artists \
        (ArtistId, Genres, Href, Name, Popularity, Uri) \
        VALUES (?, ?, ?, ?, ?, ?);"    
    aid = artist["id"] 
    genre = artist["genres"] if "genres" in artist else []    
    href = artist["href"] if "href" in artist else ""
    name = artist["name"] if "name" in artist else ""
    pop = artist["popularity"] if "popularity" in artist else 0
    uri = artist["uri"] if "uri" in artist else ""
    values = (artist["id"], genre, href, name, pop, uri)
    conn.execute(q, values)

    # external urls
    eu = artist["external_urls"]
    if eu is not None:
        q2 = "INSERT INTO External_Urls \
            (ResourceId, Type, Key, Value) \
            VALUES (?, ?, ?, ?);"
        valArr = []
        for key in eu.keys():
            val = eu[key]
            tup = (aid, artist["type"], key, val)
            valArr.append(tup)
        conn.executemany(q2, valArr)        
        conn.commit()

    # external ids
    ei = artist["external_ids"]
    if ei is not None:
        q3 = "INSERT INTO External_Ids \
            (ResourceId, Type, Key, Value) \
            VALUES (?, ?, ?, ?);"
        valArr2 = []
        for key in ei.keys():
            val = ei[key]
            tup = (aid, artist["type"], key, val)
            valArr.append(tup)
        conn.executemany(q3, valArr2)        
        conn.commit()            

    Artists_InsertedAsSimple.append(aid)
    return
    

# The goal of any ParseToQueue function is to assemble either:
# a) the full JObject of an item ready for inserting into the Database, or
# b) IDs of related items that need to be queued and then parsed themselves.
def ParseSavedSongsToQueue(fname):
    path = os.path.join(dirs["savedtracks"],fname)
    with open(path, 'r') as f:
        j = json.load(f)
        items = j["items"]
        if items is not None:
            for saved in items:
                track = saved["track"]
                trackid = track["id"]
                added_at = saved["added_at"]
                artists = track["artists"]
                album = track["album"]
                if trackid not in CollectedTracks and trackid not in QueuedTracks:                    
                    StagedToAdd_Tracks.append(track)
                    CollectedTracks.append(trackid) #set-like record of ids
                if trackid not in CollectedSavedTracks and trackid not in QueuedSavedTracks:
                    StagedToAdd_SavedTracks.append((trackid, added_at))
                    CollectedSavedTracks.append(trackid) #set-like record of ids
                if artists is not None:
                    for artist in artists:
                        artistId = artist["id"] # id
                        if artistId not in CollectedArtists and artistId not in QueuedArists:
                            QueuedArists.append(artistId) #set-like record of ids
                            # does not get appended to StagedToAdd_Artist because
                            # this is a Simple Artist. We need to get the Full Artist.
                if album is not None:
                    albumId = album["id"]
                    if albumId not in CollectedAlbums and albumId not in QueuedAlbums:
                        QueuedAlbums.append(albumId) #set-like record of ids
                        # does not get appened to StageToAdd_Album because
                        # this is a Simple Album. We need the Full Album.
    return

def ParseSavedAlbumsToQueue(fname):
    path = os.path.join(dirs["savedalbums"],fname)
    with open(path, 'r') as f:
        j = json.load(f)
        items = j["items"]
        if items is not None:
            for saved in items:
                added_at = saved["added_at"]
                album = saved["album"]
                albumid = album["id"]
                artists = album["artists"]
                if albumid not in CollectedAlbums and albumid not in QueuedAlbums:
                    StagedToAdd_Albums.append(album)
                    #Not added to Queued because it is a Full item
                if albumid not in CollectedSavedAlbums and albumid not in QueuedSavedAlbums:
                    StagedToAdd_SavedAlbums.append((albumid, added_at))
                    #Not added to queued because it is a Full item
                if artists is not None:
                    for artist in artists:
                        artistId = artist["id"] # id
                        if artistId not in CollectedArtists and artistId not in QueuedArists:
                            QueuedArists.append(artistId) #set-like record of ids
                            # does not get appended to StagedToAdd_Artist because
                            # this is a Simple Artist. We need to get the Full Artist.
                tracks = album["tracks"]["items"]
                if tracks is not None:
                    for track in tracks:
                        trackid = track["id"]
                        if trackid not in CollectedTracks:
                            CollectedTracks.append(trackid)
                        # TODO Some Mapping of Album : Song, because its a Full Track
    return

def ParsePlaylistTracksToQueue(fname):
    with open(fname, 'r') as f:
        j = json.load(f)
        items = j["items"]
        if items is not None:
            for pto in items:
                added_at = pto["added_at"]
                added_by = pto["added_by"] # Public User Object
                userid = added_by["id"]
                track = pto["track"]
                trackid = track["id"]
                if userid not in CollectedUsers and userid not in QueuedUsers:
                    QueuedUsers.append(added_by)
                if trackid not in CollectedTracks and trackid not in QueuedTracks:
                    StagedToAdd_Tracks.append(track) #these are full trackd
                    CollectedTracks.append(trackid)
                # TODO some mapping of Playlist : PlaylistTrack
    return


def AcquireInitialJson():
    GetAllPage(sp.current_user_saved_tracks, "Saved Tracks", "savedtracks")
    GetAllPage(sp.current_user_saved_albums, "Saved Albums", "savedalbums")
    GetAllPage(sp.current_user_playlists, "Saved Playlists", "playlists")
    GetFullPlaylists()
    GetFullPlaylistTracks()
    return


def RecurseParse(kind):
    if kind == "SavedSongs":
        listOfSavedSongFiles = os.listdir(dirs["savedtracks"])
        listOfSavedSongFiles.sort(key=natural_sort_key)
        for j in listOfSavedSongFiles:
            ParseSavedSongsToQueue(j)
             # break #TODO get rid of this later. Only for testing
    elif kind == "SavedAlbums":
        listofSavedAlbumFiles = os.listdir(dirs["savedalbums"])
        listofSavedAlbumFiles.sort(key=natural_sort_key)
        for j in listofSavedAlbumFiles:
            ParseSavedAlbumsToQueue(j)
             # break #TODO get rid of this later. Only for testing
        pass
    elif kind == "PlaylistTracks":
        listOfPlaylists = os.listdir(dirs["playlists"])
        for pl in listOfPlaylists:
            listofPTOs = os.listdir(os.path.join(dirs["playlists"], pl, "tracks"))
            listofPTOs.sort(key=natural_sort_key)
            for ptopage in listofPTOs:
                p = os.path.join(dirs["playlists"], pl, "tracks", ptopage)
                ParsePlaylistTracksToQueue(p)
    return

def ConstructInsertExternalTuples(externalurls, resourceid, type):
    insertVals = []
    if externalurls is not None:
        for key in externalurls.keys():
            val = externalurls[key]
            tup = (resourceid, type, key, val)
            insertVals.append(tup)
    return insertVals

def ConstructFollowerTuples(followerobj, resourceid, type):
    insertVals = []
    if followerobj is not None:
        insertVals.append((resourceid, type, followerobj["href"], followerobj["total"]))
    return insertVals
        
def ConstructImageTuple(imgArray, resourceid, type):
    insertVals = []
    if imgArray is not None:
        for img in imgArray:
            insertVals.append((resourceid, type, img["height"], img["width"], img["url"]))
    return insertVals

# Can't insert Saved Tracks without a User present.
def GetUser():
    resourceType = "user"
    user = sp.current_user()
    c = conn.cursor()
    c.execute("SELECT * FROM Users WHERE UserId = ?", (user["id"],))
    res = c.fetchone()
    if res is None or len(res) == 0:
        print ("No User entry in db for current user")
        q = "INSERT INTO Users (UserId, DisplayName, Href, Uri, Birthdate, Country, Email, Product) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        uid = user["id"]
        uri = user["uri"] if "uri" in user else "spotify:user:{}".format(uid)
        birthdate = user["birthdate"] if "birthdate" in user else None
        email = user["email"] if "email" in user else None
        href = user["href"] if "href" in user else "https://api.spotify.com/v1/users/{}".format(uid)
        followers = user["followers"] if "followers" in user else []
        displayname = user["display_name"] if "display_name" in user else None
        country = user["country"] if "country" in user else None
        product = user["product"] if "product" in user else None
        eu = user["external_urls"] if "external_urls" in user else None
        ei = user["external_ids"] if "external_ids" in user else None
        images = user["images"] if "images" in user else None

        # User Insert
        userinsertvals = (uid, displayname, href, uri, birthdate, country, email, product)
        c.execute(q, userinsertvals)

        # External Urls
        urlTuples = ConstructInsertExternalTuples(eu, uid, resourceType)
        if urlTuples is not None and len(urlTuples) > 0:
            q2 = "INSERT INTO External_Urls (ResourceId, Type, Key, Value) \
                    VALUES (?, ?, ?, ?);"
            c.executemany(q2, urlTuples)
        
        # External Ids
        idTuples = ConstructInsertExternalTuples(ei, uid, resourceType)
        if idTuples is not None and len(idTuples) > 0:
            q2 = "INSERT INTO External_Ids (ResourceId, Type, Key, Value) \
                    VALUES (?, ?, ?, ?);"
            c.executemany(q2, urlTuples)

        # Followers
        followTuple = ConstructFollowerTuples(followers, uid, resourceType)
        if followTuple is not None and len(followTuple) > 0:
            q3 = "INSERT INTO Followers (ResourceId, Type, Href, Total) \
                   VALUES (?, ?, ?, ?);"
            c.executemany(q3, followTuple)     

        # Images
        imageTuple = ConstructImageTuple(images, uid, resourceType)
        if imageTuple is not None and len(imageTuple) > 0:
            q4 = "INSERT INTO Images (ResourceId, Type, Height, Width, Url) \
                VALUES (?, ?, ?, ?, ?);"
            c.executemany(q4, imageTuple)  

        conn.commit()
    else:
        print ("Current user already existed in database.")
    return


def main():
    RefreshSpotifyTokens()
    ScrapeSetup()
    GetUser()
    #AcquireInitialJson()
    PopulateAlreadySeenItems()
    RecurseParse("SavedSongs")
    RecurseParse("SavedAlbums")
    RecurseParse("PlaylistTracks")
    print("Number of Queued Saved Tracks: {}".format(len(QueuedSavedTracks)))
    print("Number of Queued Albums: {}".format(len(QueuedAlbums)))
    print("Number of Queued Artists: {}".format(len(QueuedArists)))

    return

if __name__ == '__main__':
    main()



# Scrape Saved Songs
