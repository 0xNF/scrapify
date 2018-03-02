#/usr/bin/python3
from spotipy import Spotify, util, client, oauth2

user = 'nishumvar'
scopes = "playlist-read-private playlist-read-collaborative user-follow-read user-library-read \
user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state \
user-read-currently-playing user-read-recently-played"

# Number of peripheral items to get
nLevel = 1

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

token = util.prompt_for_user_token(user, scopes)
if token:
    sp = Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print(track['name'] + ' - ' + track['artists'][0]['name'])
else:
    print ("Can't get token for", user)