# Scrapify
A script to create a small snapshot of Spotify in a SQLite database, pivoted aruond your users Saved Tracks and playlists.
Useful for doing analysis or for hosting mock-spotify servers for testing.

# Schema
Currently, Scrapify populated the following object models, along with their constituent sub-objects, i.e., copyrights and images.

* Artists
* Artists Albums / Albums Artists
* Albums
* Album Tracks
* Tracks
* Audio Features
* Playlists
* Playlist Tracks
* Users
* User's Followed Artists
* User's Saved Tracks
* User's Saved Albums


For a complete view of the schema, see the `schemaonly.sql` file.


## Usage
### Dependencies
* Python 3
* Spotipy

Replace the `user` field with your username.

```bash
./scrapify.py
```

The final output is a `tpy.db` sqlite file in the same directory containing a lot of spotify information. Scrapify grabs first and second order information about artists and albums from your library and playlists.

## Rate limiting note
If you get rate limited, just run the tool again after the limit expires. It can pick up from places it left off from provided you do not delete any of the files created under `src/raw`.

When you feel like you have a sufficently populated `tpy.db`, you are free to delete the whole `src/raw` directory.


# Bugs
* Double parses artists and albums on multiple runs. This is mitigated by the fact that it doesn't multiple-insert into the sqlite database.

# TODO's
* Categories
* Category Playlists
* Featured Playlists
* Audio Analyses