# Json Intermediate Save Format = Endpoint_xxx.json
# 1. Scrape Saved Songs until Next = Null. Save to raw/savedsongs/fname.json
# 2. Scrape Saved Albums until Next = Null. Save to raw/savedalbums/fname.json
# 3. Scrape Saved Artists until Next = Null. Save to raw/savedartists/fname.json
# 4. Scrape My Playlists until Next = Null. Save to raw/playlists/fname.json
# 5. For each Playlist, scrape songs until Next = Null.  Save to raw/playlists/playlistname/fname.json


# 6. For each Saved Song:
#       a) for each artist...
#           1) !AlreadyDoneArtists.Contains(ArtistId) ? ArtistsDict.add(ArtistId, ResourceUrl);alreadyDoneArtsits.add(ArtistId) : null;
#           2) Add to ArtistTrackMap (ArtistId, TrackId); #on conflict ignore
#       b) for each album...
#           1) !AlreadyDoneAlbums.Contains(AlbumId) ? AlbumDict.add(AlbumId, ResourceUrl) : null
#           2) Add to AlbumTrackMap(AlbumId, TrackId); # cn conflcit ignore
#       c) add to SavedSongs Table: (UserId, songid, addedat); # oci
#       d) because SavedTracks are full track objects: #oci for all
#           1) Add to Tracks Table: (TrackId, AvailableMarkets, disc_number, duration_ms, explicit, Href, is_playable, linked_from, restrictions, name, Popularity, preview_url, track_number, uri);
#           2) Add to External_Urls table: (TrackId, type:'track', key, value); #type is for join purposes as Spotify does not guarantee an Id is unique across Object Model Types
#           3) Add to External_Ids table: (TrackId, type:'track', key, value); #type is see above
#       e) add to AlreadyDoneTracks.add(TrackId);

# 7. For each Saved Album...
#       a) If !AlreadyDoneAlbums.Contains(SavedAlbum.Album.AlbumId): Because SavedAlbums are full Album Objects:
#           1) Add to Albums Table: (AlbumId, album_type, AvailableMarkets, Genres, Href, Label, name, release_date, release_date_precision, restrictions, uri)
#           2) Add to External_Urls table: (AlbumId, type:'album', key, value); #type is for join purposes as Spotify does not guarantee an Id is unique across Object Model Types
#           3) Add to External_Ids table: (AlbumId, type:'album', key, value); #type is see above
#           4) Add to Copyrights Table: (AlbumId, text, type);
#           5) Add to Images Table: (AlbumId, type: 'album', height, width, url); #type is see above
#           6) Add to AlreadyDoneAlbums.Add(SavedAlbum.Album.AlbumId)
#       b) For each Artist...
#           1) !AlreadyDoneArtists.Contains(ArtistId) ? ArtistsDict.add(ArtistId, ResourceUrl);alreadyDoneArtsits.add(ArtistId) : null;
#           2) add to ArtistAlbumMap Table: (AlbumId, ArtistId);
#       c) add to SavedAlbums Table: (UserId, AlbumId, addedat);

#
#
# 9. For each Simple Playlist:
#       f) Add to User Table: (UserId, display_name, Href, uri)
#       a) Add to PlaylistsTable: (playlistid, collaborative, Href, name, Public, SnapshotId, uri);
#       b) Add to ExternalUrls Table: (playlistid, type: 'playlist', key, value);
#       c) Add to Images Table: (playlistid, type: 'playlist', height, width, url);
#       d) Add to PlaylistsDict.Add([playlistid, UserId], resourceurl);
#       g) Add to External_Urls table: (UserId, type:'user', key, value); #type is for join purposes as Spotify does not guarantee an Id is unique across Object Model Types
#       h) Add to Images Table: (UserId, type: 'user', height, width, url); #type is see above
#       i) Add to Followers Table: (UserId, type:user, Href, total);
#       e) Add to UserPlaylistMap Table (UserId, playlstid);

# 
# 10. For each Song in Full Playlist:
#       a) Add to PlaylistTrack Table: (playlistid, addedat, addedby, is_local, TrackId);
#       b) because PlaylistTrack.Track are full track objects:
#           1) Add to Tracks Table: (TrackId, AvailableMarkets, disc_number, duration_ms, explicit, Href, is_playable, linked_from, restrictions, name, Popularity, preview_url, track_number, uri);
#           2) Add to External_Urls table: (TrackId, type:'track', key, value); #type is for join purposes as Spotify does not guarantee an Id is unique across Object Model Types
#           3) Add to External_Ids table: (TrackId, type:'track', key, value); #type is see above
#           4) for each Artist:
#               a) Add to ArtistTrackMap (ArtistId, TrackId);
#               b) ArtistDict.add(ArtistId, resourceurl);
#           5) for each Album:
#               a) Add to AlbumTrackMap (AlbumId, TrackId);
#               c) AlbumDict.add(AlbumId, resourceurl);
#
# 11. For each Artist in ArtistDict:
#       a) Add To Artists Table: (ArtistId, Genres, Href name, Popularity, uri);
#       b) for each Album...
#           c) if not in AlreadyDoneAlbums, add to AlbumDict.Add(AlbumId, resourceurl);

