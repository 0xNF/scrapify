#!/usr/bin/python3
import json
import math
import os
import re
import sqlite3
import sys
from pathlib import Path

from spotipy import Spotify, client, oauth2, util

user = 'nishumvar'
scopes = "playlist-read-private playlist-read-collaborative user-follow-read user-library-read \
user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state \
user-read-currently-playing user-read-recently-played"
ccm = None
sp = Spotify()
dbname = "tpy.db"
db = None

CurrentUserMarket = 'US'

conn = sqlite3.connect(dbname)

ROrder = 1
CurrentROrder = 1

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
StagedToAdd_PlaylistTracks = {} # Format of {PlaylistId: [ListOfTracks]}
StagedToAdd_SavedAlbums = []
StagedToAdd_Users = []
StagedToAdd_AlbumTracks = {} # Format of {AlbumId: [ListOfTracks]}
StagedToAdd_AlbumArtists = {} # FOrmat of {albumId: [ListOfArtistIds]}

def PopulateAlreadySeenItems():
    CollectedArtists.extend(populate("ArtistId", "Artists"))
    CollectedAlbums.extend(populate("AlbumId", "Albums"))
    CollectedPlaylists.extend(populate("PlaylistId", "Playlists"))
    CollectedTracks.extend(populate("TrackId", "Tracks"))
    CollectedUsers.extend(populate("UserId", "Users"))
    # TODO read Artists/Albums/Tracks dir, parse ids and add to Collected
    # this will prevent duplicate runs from queuing up the same ids that are already
    # downloaded and awaiting parsing
    return

def populate(pkey, table):
    c = conn.cursor()
    q = "SELECT {} FROM {};".format(pkey, table)
    ids = []
    for row in c.execute(q):
        ids.append(row[0])
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
    

# The goal of any ParseToQueue function is to assemble either:
# a) the full JObject of an item ready for inserting into the Database, or
# b) IDs of related items that need to be queued and then parsed themselves.
def ParseSavedSongsToQueue(fname, order):
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

def ParseSavedAlbumsToQueue(fname, order):
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
                        if albumid not in StagedToAdd_AlbumTracks:
                            StagedToAdd_AlbumTracks[albumid] = [trackid]
                        else:
                            StagedToAdd_AlbumTracks[albumid].append(trackid)
                # addme = (albumid, added_at)
                # if addme not in StagedToAdd_SavedAlbums:
                #     StagedToAdd_SavedAlbums[albumid] = [addme]
                # else:
                #     StagedToAdd_SavedAlbums[albumid].append(addme)
    return

def ParsePlaylistToQueue(fname, playlistid, order):
    if playlistid not in CollectedPlaylists and playlistid not in StagedToAdd_Playlists:
        with open(fname, 'r') as f:
            j = json.load(f)       
            StagedToAdd_Playlists.append(j)
            # collaborative = j["collaborative"]
            # href = j["href"]
            # name = j["name"]
            # followers = j["followers"]
            # description = j["description"]
            # owner = j["owner"]
            # snapshotid = j["snapshot_id"]
            # images = j["images"]
            # primary_color = j["primary_color"]
            # uri = j["uri"]
            # external_urls = j["external_urls"]
            # public = j["public"]
    return


def ParsePlaylistTracksToQueue(fname, playlistid, order):
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
                if userid not in CollectedUsers:
                    StagedToAdd_Users.append(added_by)
                    CollectedUsers.append(userid)
                if trackid not in CollectedTracks and trackid not in QueuedTracks:
                    StagedToAdd_Tracks.append(track) #these are full tracks
                    CollectedTracks.append(trackid)
                addme = (added_at, userid, trackid)
                if playlistid not in StagedToAdd_PlaylistTracks:
                    StagedToAdd_PlaylistTracks[playlistid] = [addme]
                else:
                    StagedToAdd_PlaylistTracks[playlistid].append(addme)
    return


def AcquireInitialJson():
    GetAllPage(sp.current_user_saved_tracks, "Saved Tracks", "savedtracks")
    GetAllPage(sp.current_user_saved_albums, "Saved Albums", "savedalbums")
    GetAllPage(sp.current_user_playlists, "Saved Playlists", "playlists")
    GetFullPlaylists()
    GetFullPlaylistTracks()
    return


def RecurseParseAll():
    RecurseParse("SavedSongs", CurrentROrder)
    RecurseParse("SavedAlbums", CurrentROrder)
    RecurseParse("Playlists", CurrentROrder)
    RecurseParse("PlaylistTracks", CurrentROrder)
    print("Number of Staged Saved Tracks: {}".format(len(StagedToAdd_SavedTracks)))
    print("Number of Staged Tracks: {}".format(len(StagedToAdd_Tracks)))
    print("Number of Staged Users: {}".format(len(StagedToAdd_Users)))
    print("Number of Staged Artists: {}".format(len(StagedToAdd_Artists)))
    print("Number of Staged Albums: {}".format(len(StagedToAdd_Albums)))
    print("Number of Staged Album Tracks: {}".format(len(StagedToAdd_AlbumTracks)))
    print("Number of Staged Playlists: {}".format(len(StagedToAdd_Playlists)))
    print("Number of Staged Playlist Tracks: {}".format(len(StagedToAdd_PlaylistTracks)))
    print("Number of Staged Saved Albums: {}".format(len(StagedToAdd_SavedAlbums)))


    print("Number of Queued Albums: {}".format(len(QueuedAlbums)))
    print("Number of Queued Artists: {}".format(len(QueuedArists)))
    print("Number of Staged Playlists: {}".format(len(StagedToAdd_Playlists)))
    return

def RecurseParse(kind, CurrentROrder):
    if kind == "SavedSongs":
        listOfSavedSongFiles = os.listdir(dirs["savedtracks"])
        listOfSavedSongFiles.sort(key=natural_sort_key)
        for j in listOfSavedSongFiles:
            ParseSavedSongsToQueue(j, CurrentROrder)
             # break #TODO get rid of this later. Only for testing
    elif kind == "SavedAlbums":
        listofSavedAlbumFiles = os.listdir(dirs["savedalbums"])
        listofSavedAlbumFiles.sort(key=natural_sort_key)
        for j in listofSavedAlbumFiles:
            ParseSavedAlbumsToQueue(j, CurrentROrder)
             # break #TODO get rid of this later. Only for testing
    elif kind == "Playlists":
        listOfPlaylists = [x for x in os.listdir(dirs["playlists"]) if os.path.isdir(os.path.join(dirs["playlists"], x))]
        for pl in listOfPlaylists:
            p = os.path.join(dirs["playlists"], pl)
            listOfDetails = [os.path.join(p,x) for x in os.listdir(p) if os.path.isfile(os.path.join(p, x))]
            for detail in listOfDetails:
                ParsePlaylistToQueue(detail, pl, CurrentROrder)
    elif kind == "PlaylistTracks":
        listOfPlaylists = os.listdir(dirs["playlists"])
        listOfPlaylists = [x for x in listOfPlaylists if os.path.isdir(os.path.join(dirs["playlists"], x))]
        for pl in listOfPlaylists:            
            listofPTOs = os.listdir(os.path.join(dirs["playlists"], pl, "tracks"))
            listofPTOs.sort(key=natural_sort_key)
            for ptopage in listofPTOs:
                p = os.path.join(dirs["playlists"], pl, "tracks", ptopage)
                ParsePlaylistTracksToQueue(p, pl, CurrentROrder)
    return

def ConstructCopyrightTuples(copyrights, albumid):
    """Returns listOf(albumid, text, type)"""
    insertvals = []
    if copyrights and len(copyrights) > 0 :
        for c in copyrights:
            t = (albumid, c["text"], c["type"])
            insertvals.append(t)
    return insertvals

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

def InsertTrackRelinks(relinktuples):
    resourceType = "track"
    q = "INSERT OR IGNORE INTO TrackRelinks(TrackId, UnavailableMarket, AvailableTrackId) VALUES (?, ?, ?);"
    c = conn.cursor()
    c.executemany(q, relinktuples)
    c.close()
    conn.commit()
    return

def InsertSavedTracks(listOfSavedTracks):
    q = "INSERT OR IGNORE INTO SavedTracks (UserId, TrackId, AddedAt, IsLocal) VALUES (?,?,?,?)"
    tups = []
    for saved in listOfSavedTracks:
        uid = user
        added_at = saved[1]
        trackid = saved[0]
        local = False
        tup = (uid, trackid, added_at, local)
        tups.append(tup)
    c = conn.cursor()
    c.executemany(q,tups)
    c.close()
    conn.commit()
    print("Inserted {} saved tracks into db".format(len(listOfSavedTracks)))
    return

def InsertAlbumTracks(listOfAlbumTracks):
    q = "INSERT OR IGNORE INTO AlbumTrackMap (AlbumId, TrackId) VALUES (?, ?);"
    tups = []
    for albumid in listOfAlbumTracks.keys():
        trackids = listOfAlbumTracks[albumid]
        for trackid in trackids:
            m = (albumid, trackid)
            tups.append(m)
    c = conn.cursor()
    c.executemany(q, tups)
    c.close()
    conn.commit()
    print("Inserted {} album-track mappings into database".format(len(listOfAlbumTracks)))
    return

def InsertPlaylistTracks(listOfPlaylistTracks):
    q = "INSERT OR IGNORE INTO PlaylistTracks(PlaylistId, TrackId, AddedAt, AddedBy) VALUES (?, ?, ?, ?);"
    tups = []
    for playlistid in listOfPlaylistTracks.keys():
        lst = listOfPlaylistTracks[playlistid] # (added_at, userid, trackid)
        for tracks in lst:
            m = (playlistid, tracks[2], tracks[0], tracks[1])
            tups.append(m)
    c = conn.cursor()
    c.executemany(q, tups)
    c.close()
    conn.commit()
    print("Inserted {} playlist tracks into database".format(len(listOfPlaylistTracks)))
    return

def InsertArtistAlbums(listOfArtistAlbums):
    q = "INSERT OR IGNORE INTO ArtistAlbumsMap (AlbumId, ArtistId) VALUES (?, ?);"
    tups = []
    for albumid in listOfArtistAlbums.keys():
        artistids = listOfArtistAlbums[albumid]
        for artistid in artistids:
            m = (albumid, artistid)
            tups.append(m)
    c = conn.cursor()
    c.executemany(q, tups)
    c.close()
    conn.commit()
    print("Inserted {} artist-album mappings into database".format(len(listOfArtistAlbums)))
    return

def InsertTracks(listOfTracks):
    resourceType = "track"
    q = "INSERT OR IGNORE INTO Tracks (TrackId, AvailableMarkets, DiscNumber, DurationMs,\
                                     Explicit, Href, IsPlayable, Restrictions, \
                                     Name, Popularity, PreviewUrl, TrackNumber, Uri) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    trackTuples = []
    relinkTuples = []
    for track in listOfTracks:
        trackid = track["id"]
        markets = ','.join(track["available_markets"])
        disc = track['disc_number'] if 'disc_number' in track else 1
        duration = track['duration_ms'] if 'duration_ms' in track else 0
        explicit = track['explicit'] if 'explicit' in track else False
        href = track['href'] if 'href' in track else ''
        playable = track['is_playable'] if 'is_playable' in track else True
        linkedfrom = track['linked_from'] if 'linked_from' in track else None
        restrictions = track['restrictions'] if 'restrictions' in track else None
        name = track['name']
        popularity = track['popularity'] if 'popularity' in track else None
        prev = track['preview_url'] if 'preview_url' in track else None
        tracknumber = track['track_number'] if 'track_number' in track else 1
        uri = track['uri'] if 'uri' in track else 'spotify:track:{}'.format(trackid)

        if linkedfrom is not None:
            tup = (linkedfrom['id'], CurrentUserMarket, trackid)
            relinkTuples.append(tup)
        trackTuples.append((trackid, markets, disc, duration, explicit, href, playable, restrictions, name, popularity, prev, tracknumber, uri))
    c = conn.cursor()
    c.executemany(q, trackTuples)
    conn.commit()
    InsertTrackRelinks(relinkTuples)
    print("inserted {} tracks to db".format(len(listOfTracks)))
    return

def InsertAlbums(listOfAlbums):
    resourceType = "album"
    albumTups = []
    externalUrlTuples = []
    externalIdTuples = []
    imageTuples = []
    copyrightTuples = []
    q = "INSERT OR IGNORE INTO ALBUMS \
                    (AlbumId, AlbumType, AvailableMarkets, Href, Label, Name, ReleaseDate, ReleaseDatePrecision, Restrictions, Uri, Popularity)\
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    for album in listOfAlbums:
        aid = album["id"]
        atype = album["album_type"] if "album_type" in album else "album"
        markets = ",".join(album["available_markets"])
        href = album["href"]
        label = album["label"]
        name = album["name"]
        rdate = album["release_date"]
        rdatep = album["release_date_precision"]
        restrictions = album["restrictions"] if "restrictions" in album else None
        uri = album["uri"]
        ei = album["external_ids"] if "external_ids" in album else None
        eu = album["external_urls"] if "external_urls" in album else None
        images = album["images"] if "images" in album else None
        copyrights = album["copyright"] if "copyright" in album else None
        popularity = album["popularity"] if "popularity" in album else None

        # Album
        atup = (aid, atype, markets, href, label, name, rdate, rdatep, restrictions, uri, popularity)
        albumTups.append(atup)

        # External Urls
        urlTuples = ConstructInsertExternalTuples(eu, aid, resourceType)
        externalUrlTuples.extend(urlTuples)    

        # External Ids
        idTuples = ConstructInsertExternalTuples(ei, aid, resourceType)
        externalIdTuples.extend(idTuples)

        # Images
        imageTuple = ConstructImageTuple(images, aid, resourceType)
        imageTuples.extend(imageTuple)      

        # Copyrights
        copyrightTuple = ConstructCopyrightTuples(copyrights, aid)
        copyrightTuples.extend(copyrightTuple)


    c = conn.cursor()
    c.executemany(q, albumTups)  

    # External Urls
    if externalUrlTuples is not None and len(externalUrlTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Urls (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalUrlTuples)

    # External Ids
    if externalIdTuples is not None and len(externalIdTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Ids (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalIdTuples) 

    # Images
    if imageTuples is not None and len(imageTuples) > 0:
        q4 = "INSERT OR IGNORE INTO Images (ResourceId, Type, Height, Width, Url) \
            VALUES (?, ?, ?, ?, ?);"
        c.executemany(q4, imageTuples)  

    # Copyrights
    if copyrightTuples is not None and len(copyrightTuples) > 0:
        q5 = "INSERT OR IGNORE INTO Copyrights (AlbumId, Text, Type) VALUES (?, ?, ?);"
        c.executemany(q5, copyrightTuples)

    c.close()
    conn.commit()
    print("Inserted {} albums into db".format(len(listOfAlbums)))
    return

def InsertSavedAlbums(listOfSavedAlbums):
    q = "INSERT OR IGNORE INTO SavedAlbums (UserId, AlbumId, AddedAt) VALUES (?,?,?)"
    tups = []
    for saved in listOfSavedAlbums:
        uid = user
        added_at = saved[1]
        albumid = saved[0]
        tup = (uid, albumid, added_at)
        tups.append(tup)
    c = conn.cursor()
    c.executemany(q,tups)
    conn.commit()
    print("Inserted {} saved albums into db".format(len(listOfSavedAlbums)))
    return

def InsertArtists(listOfArtists):
    resourceType = "artist"
    artistTups = []
    externalUrlTuples = []
    externalIdTuples = []
    followerTuples = []
    imageTuples = []
    q = "INSERT OR IGNORE INTO Artists \
        (ArtistId, Genres, Href, Name, Popularity, Uri) \
        VALUES (?, ?, ?, ?, ?, ?);"    
    for artist in listOfArtists:
        aid = artist["id"] 
        genre = artist["genres"] if "genres" in artist else []    
        href = artist["href"] if "href" in artist else ""
        name = artist["name"] if "name" in artist else ""
        pop = artist["popularity"] if "popularity" in artist else 0
        uri = artist["uri"] if "uri" in artist else ""
        eu = artist["external_urls"] if "external_urls" in artist else None
        ei = artist["external_ids"] if "external_ids" in artist else None
        images = artist["images"] if "images" in artist else None
        followers = artist["followers"] if "followers" in artist else None

        # Artist
        artistTup = (artist["id"], genre, href, name, pop, uri)
        artistTups.append(artistTup)

        # External Urls
        urlTuples = ConstructInsertExternalTuples(eu, aid, resourceType)
        externalUrlTuples.extend(urlTuples)    

        # External Ids
        idTuples = ConstructInsertExternalTuples(ei, aid, resourceType)
        externalIdTuples.extend(idTuples)

        # Followers
        followTuple = ConstructFollowerTuples(followers, aid, resourceType)
        followerTuples.extend(followTuple)

        # Images
        imageTuple = ConstructImageTuple(images, aid, resourceType)
        imageTuples.extend(imageTuple)      

    c = conn.cursor()
    c.executemany(q, artistTups)  

        # External Urls
    if externalUrlTuples is not None and len(externalUrlTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Urls (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalUrlTuples)

    # External Ids
    if externalIdTuples is not None and len(externalIdTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Ids (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalIdTuples)

    # Followers
    if followerTuples is not None and len(followerTuples) > 0:
        q3 = "INSERT OR IGNORE INTO Followers (ResourceId, Type, Href, Total) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q3, followerTuples)     

    # Images
    if imageTuples is not None and len(imageTuples) > 0:
        q4 = "INSERT OR IGNORE INTO Images (ResourceId, Type, Height, Width, Url) \
            VALUES (?, ?, ?, ?, ?);"
        c.executemany(q4, imageTuples)  
    c.close()
    conn.commit()
    print("Inserted {} artists into db".format(len(listOfArtists)))
    return

def InsertPlaylists(listOfPlaylists):
    resourceType = "playlist"
    q = "INSERT OR IGNORE INTO Playlists (PlaylistId, Collaborative, Href, Name, Public, SnapshotId, Uri, OwnerId, Description) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
    playlistTups = []
    externalUrlTuples = []
    externalIdTuples = []
    followerTuples = []
    imageTuples = []
    for playlist in listOfPlaylists:
        pid = playlist["id"]
        eu = playlist["external_urls"] if "external_urls" in playlist else None
        ei = playlist["external_ids"] if "external_ids" in playlist else None
        followers = playlist["followers"] if "followers" in playlist else None
        images = playlist["images"] if "images" in playlist else None
        collab = playlist["collaborative"] if "collaborative" in playlist else False
        href = playlist["href"]
        name = playlist["name"]
        description = playlist["description"]
        owner = playlist["owner"]["id"]      
        public = playlist["public"] if "public" in playlist else True
        snapshot = playlist["snapshot_id"]
        uri = playlist["uri"]

        # Playlist Insert
        ptup = (pid, collab, href, name, public, snapshot, uri, owner, description)
        playlistTups.append(ptup)

        # External Urls
        urlTuples = ConstructInsertExternalTuples(eu, pid, resourceType)
        externalUrlTuples.extend(urlTuples)    

        # External Ids
        idTuples = ConstructInsertExternalTuples(ei, pid, resourceType)
        externalIdTuples.extend(idTuples)

        # Followers
        followTuple = ConstructFollowerTuples(followers, pid, resourceType)
        followerTuples.extend(followTuple)

        # Images
        imageTuple = ConstructImageTuple(images, pid, resourceType)
        imageTuples.extend(imageTuple)  

    c = conn.cursor()
    c.executemany(q, playlistTups)

    # External Urls
    if externalUrlTuples is not None and len(externalUrlTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Urls (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalUrlTuples)

    # External Ids
    if externalIdTuples is not None and len(externalIdTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Ids (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalIdTuples)

    # Followers
    if followerTuples is not None and len(followerTuples) > 0:
        q3 = "INSERT OR IGNORE INTO Followers (ResourceId, Type, Href, Total) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q3, followerTuples)     

    # Images
    if imageTuples is not None and len(imageTuples) > 0:
        q4 = "INSERT OR IGNORE INTO Images (ResourceId, Type, Height, Width, Url) \
            VALUES (?, ?, ?, ?, ?);"
        c.executemany(q4, imageTuples)  

    print("Inserted {} playlists into database".format(len(playlistTups)))
    c.close()
    conn.commit()
    return    

def InsertUsers(listOfUsers):
    resourceType = "user"
    c = conn.cursor()
    q = "INSERT OR IGNORE INTO Users (UserId, DisplayName, Href, Uri, Birthdate, Country, Email, Product) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    usersToInsert = []
    externalUrlTuples = []
    externalIdTuples = []
    followerTuples = []
    imageTuples = []
    for user in listOfUsers:
        uid = user["id"]
        uri = user["uri"] if "uri" in user else "spotify:user:{}".format(uid)
        birthdate = user["birthdate"] if "birthdate" in user else None
        email = user["email"] if "email" in user else None
        href = user["href"] if "href" in user else "https://api.spotify.com/v1/users/{}".format(uid)
        followers = user["followers"] if "followers" in user else None
        displayname = user["display_name"] if "display_name" in user else None
        country = user["country"] if "country" in user else None
        product = user["product"] if "product" in user else None
        eu = user["external_urls"] if "external_urls" in user else None
        ei = user["external_ids"] if "external_ids" in user else None
        images = user["images"] if "images" in user else None
        # User Insert
        userinsertvals = (uid, displayname, href, uri, birthdate, country, email, product)
        usersToInsert.append(userinsertvals)

        # External Urls
        urlTuples = ConstructInsertExternalTuples(eu, uid, resourceType)
        externalUrlTuples.extend(urlTuples)    

        # External Ids
        idTuples = ConstructInsertExternalTuples(ei, uid, resourceType)
        externalIdTuples.extend(idTuples)

        # Followers
        followTuple = ConstructFollowerTuples(followers, uid, resourceType)
        followerTuples.extend(followTuple)

        # Images
        imageTuple = ConstructImageTuple(images, uid, resourceType)
        imageTuples.extend(imageTuple)        

    c.executemany(q, usersToInsert)
    print("Inserted {} users into database".format(len(usersToInsert)))

    # External Urls
    if externalUrlTuples is not None and len(externalUrlTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Urls (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalUrlTuples)

    # External Ids
    if externalIdTuples is not None and len(externalIdTuples) > 0:
        q2 = "INSERT OR IGNORE INTO External_Ids (ResourceId, Type, Key, Value) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q2, externalIdTuples)

    # Followers
    if followerTuples is not None and len(followerTuples) > 0:
        q3 = "INSERT OR IGNORE INTO Followers (ResourceId, Type, Href, Total) \
                VALUES (?, ?, ?, ?);"
        c.executemany(q3, followerTuples)     

    # Images
    if imageTuples is not None and len(imageTuples) > 0:
        q4 = "INSERT OR IGNORE INTO Images (ResourceId, Type, Height, Width, Url) \
            VALUES (?, ?, ?, ?, ?);"
        c.executemany(q4, imageTuples)  

    c.close()
    conn.commit()
    return

def InsertStagedUsers():
    InsertUsers(StagedToAdd_Users)
    StagedToAdd_Users.clear()
    return

def InsertStagedTracks():
    InsertTracks(StagedToAdd_Tracks)
    StagedToAdd_Tracks.clear()

def InsertStagedSavedTracks():
    InsertSavedTracks(StagedToAdd_SavedTracks)
    StagedToAdd_SavedTracks.clear()

def InsertStagedArtists():
    InsertArtists(StagedToAdd_Artists)
    StagedToAdd_Artists.clear()

def InsertStagedAlbums():
    InsertAlbums(StagedToAdd_Albums)
    StagedToAdd_Albums.clear()

def InsertStagedSavedAlbums():
    InsertSavedAlbums(StagedToAdd_SavedAlbums)
    StagedToAdd_SavedAlbums.clear()

def InsertStagedAlbumTracks():
    InsertAlbumTracks(StagedToAdd_AlbumTracks)
    StagedToAdd_AlbumTracks.clear()

def InsertStagedPlaylists():
    InsertPlaylists(StagedToAdd_Playlists)
    StagedToAdd_Playlists.clear()

def InsertStagedPlaylistTracks():
    InsertPlaylistTracks(StagedToAdd_PlaylistTracks)
    StagedToAdd_PlaylistTracks.clear()

def InsertStagedArtistAlbums():
    InsertArtistAlbums(StagedToAdd_AlbumArtists)
    StagedToAdd_AlbumArtists.clear()

def InsertStagedAll():
    InsertStagedUsers()
    InsertStagedTracks()
    InsertStagedSavedTracks()
    InsertStagedArtists()
    InsertStagedAlbums()
    InsertStagedSavedAlbums()
    InsertStagedAlbumTracks()
    InsertStagedArtistAlbums()
    InsertStagedPlaylists()
    InsertStagedPlaylistTracks()
    return

# Can't insert Saved Tracks or Playlists without a User present.
def GetUser():
    global CurrentUserMarket
    user = sp.current_user()
    CurrentUserMarket = user['country'] if 'country' in user else 'US'
    c = conn.cursor()
    c.execute("SELECT * FROM Users WHERE UserId = ?", (user["id"],))
    res = c.fetchone()
    if res is None or len(res) == 0:
        print ("No User entry in db for current user")
        InsertUsers([user])
    else:
        print ("Current user already existed in database.")
    return

def Dq(queued,collected, spcall, keyword, lim=50):
    ReadyToGo = []    
    for id in queued:
        if id not in collected:
            ReadyToGo.append(id)
    for id in ReadyToGo:
        queued.remove(id)
    batches = [
         [
             ReadyToGo[(x*lim)+y]
             for y in
             range(min(lim,len(ReadyToGo)-(x*lim)))
         ] 
         for x in 
         range(math.ceil(len(ReadyToGo)/lim))
    ]
    print("{} batches in queue".format(len(batches)))
    startAt = len(os.listdir(dirs[keyword])) # for when it rate limits us.
    for i,batch in enumerate(batches[startAt:]):
        print("fetching batch {}".format(startAt+i))
        res = spcall(batch)
        SaveJson(dirs[keyword], "{}_{}.json".format(keyword, startAt+i), res)
    return

def DqArtists():
    Dq(QueuedArists, CollectedArtists, sp.artists, 'artists')
    return
    



# Flow:
#   0) Create DB if not exist
#   1) Refresh/Acquire Tokens
#   2) Setup Scrape Dirs
#   3) Get the Current User + save to DB
#   4) Acquire initial JSON files
#   5) Populate RAM with ids of already collected items
#   6) RecuerseParse Saved Songs
#   7) RecurseParse SavedAlbums
#   8) RecurseParse PlaylistTracks 
#   ...
#   8a) if currentROrder > ROrder, stop. # not true for first run.
#   8b) for d in dirs: RecurseParse(d)
#   8c) For queuedItem in QueuedItems: DL(QueuedItem)
#   9) Write Staged items to Database
#   ....
#   9a) if currentROrder > ROrder, stop.
#   10) For queuedItem in QueuedItems: DL(queuedItem)
#   11) for d in dirs: RecurseParse(d)
#   12) Write Staged Items to Database.


def main():
    global CurrentROrder
    RefreshSpotifyTokens()
    ScrapeSetup()
    GetUser()
    #AcquireInitialJson()
    PopulateAlreadySeenItems()
    RecurseParseAll()
    InsertStagedAll()
    DqArtists()
    CurrentROrder += 1

    return

if __name__ == '__main__':
    main()
