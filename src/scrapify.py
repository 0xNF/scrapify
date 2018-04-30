#/usr/bin/python3
# n = 0 : Return only the first level data to fill each endpoint. 
#   This means that for each Simple artist returned from a given endpoint, we also fetch its Related Artists and Top Tracks;
#   and for each Simple Album returned we get that albums full tracks. 
#   Also, that means we will get all Categories, and for each track we get, we fetch the Audio Features object
# n = 1 : Return all of n = 0, and an additional set of API calls for each album, artist and track. 
# missing: categories, genres, users-top
# For each paging object of Playlists, store into [myplaylists]
    # For each Simple Playlist in a page of playlists, sto re into [Playlists], store playlist:user:id into [Ids]
        # For each PlaylistTrackObject in a Playlist, get the Track and  store into [Tracks], store track:id into [Ids]
            # For each Simple Album on a Track, store into [Simple Albums]
                # For each Simple Artist on an Album, store into [Simple Artists]
            # For each Simple Artist on a track, store into [Simple Artists]
# For each paging object of Saved Tracks, store into [savedsongs]
    # for each SavedTrack in the paging object, get the Track and store into [Tracks], store track:id into [Ids]
        # For each SimpleAlbum on a Track, store into [Simple Albums]
            # For each Simple Artist on an album, store into [Simple Artists]
        # For each SimpleArtist on a Track, store into [Simple Artists]
# For each Id not in [Ids] for each table we concern ourselves with...
# if n = 0, do nothing. We have successfully returned only a snapshot of the User.
# if n = 1:
    # For each Simple Album in [Simple Albums], get the Full Album, store into [Albums], store album:id into [Ids]
        # For Each Simple Artist in Full Album, store into [Simple Artists]
    # For each Simple Artist in [Simple Artists], get Full Artist, store  into [Artists], store artist:id into [Ids]
    # For each Simple Artist in [Simple Artists], get Artists Top Songs, store into [ArtistTopSongs], store artisttopsongs:id
    # For each Simple Artist in [Simple Artists], get Artists Related Artists, store into [RelatedArtists] store relatedartists:id
    # For each Track in 
    
from spotipy import Spotify, util, client, oauth2
import sqlite3
import os
import sys
from pathlib import Path

user = 'nishumvar'
scopes = "playlist-read-private playlist-read-collaborative user-follow-read user-library-read \
user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state \
user-read-currently-playing user-read-recently-played"

# Number of peripheral items to get
n = 1
# n = 0 : for a given Spotify Object, return only the Spotify Object
# n = 1 : for a given Spotify Object, return the object, and all of it's first-level connection
# n = 2 : for a given Spotify Object, return the object, its first-level connections, and their first-level connections
# n = 3 : ...etc

# Spotify Object Model items to request
items = [
    "tracks"
    "artists",
    "albums",
    "playlists",
    "categories",
    "audio_feastures",
    "audio_analysis",
]

Albums_Full = []
Albums_Simple = []
Artists_Full = []
Artists_Simple = []
Audio_Features = []
Categories = []
Copyrights = []
Cursors = []
Errors = []
External_IDs = []
External_URLs = []
Follows = []
Image = []
Paging = []
Images = []
Cursor_Based_Paging = []
Playlists_Full = []
Playlists_Simple = []
Playlist_TrackObject = []
Recommendations = []
Recommendation_Seeds = []
Saved_Tracks = []
Saved_Albums = []
Tracks_Full = []
Tracks_Simple = []
Track_Links = []
Users_Private = []
Users_Public = []
Play_Histories = []
Context = []

playlistPageQueue = []
artistPageQueue = []
albumPageQueue = []
savedTrackPageQueue = []

playlist_ids_retrieved = []
artists_ids_retrieved = []
album_ids_retrieved = []
track_ids_retrieved = []

ccm = None
sp = Spotify()

dbname = "tpy.db"
db = None
def makeSqliteOnDisk():
    print("checking for existance of Sqlite file")
    p = Path(os.getcwd(), dbname)
    if(p.exists()):
        print("Sqlite file existed at " + str(p))
        db = sqlite3.connect(dbname)
        return
    else:
        print("Sqlite file did not exist: created at" + str(p))
        db = sqlite3.connect(dbname)
        makeTable = """CREATE TABLE `SpotifyData` ( `spotfyId` TEXT NOT NULL, `data` TEXT, `query` TEXT, PRIMARY KEY(`spotfyId`) )"""
        db.execute(makeTable)
        return
    

def getUsersPlaylists():
    refreshSp()
    page0 = sp.current_user_playlists(50, 0)
    print(page0)
    #Exhaust the paging of Simple Playlists
    # Store into Simple Playlists
    # next function => pass each Simple Playlist into the GetFullPlaylist
    #       # Exhaust the paging of Playlist_Track_Object (Full_Track)    
    #       # Store into Full_Tracks
    return


def refreshSp():
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

def main():
    makeSqliteOnDisk()
    getUsersPlaylists()

if __name__ == "__main__":
    main()