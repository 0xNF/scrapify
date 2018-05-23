BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `Users` (
	`UserId`	TEXT,
	`DisplayName`	TEXT,
	`Href`	TEXT,
	`Uri`	TEXT,
	`Birthdate`	TEXT,
	`Country`	TEXT,
	`Email`	TEXT,
	`Product`	TEXT,
	PRIMARY KEY(`UserId`)
);
CREATE TABLE IF NOT EXISTS `UserPlaylistMap` (
	`UserId`	TEXT NOT NULL,
	`PlaylistId`	TEXT NOT NULL,
	PRIMARY KEY(`UserId`,`PlaylistId`),
	FOREIGN KEY(`PlaylistId`) REFERENCES `Playlists`(`PlaylistId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`)
);
CREATE TABLE IF NOT EXISTS `Tracks` (
	`TrackId`	TEXT,
	`AvailableMarkets`	TEXT NOT NULL,
	`DiscNumber`	INTEGER NOT NULL,
	`DurationMs`	BIGINT NOT NULL,
	`Explicit`	BOOLEAN NOT NULL,
	`Href`	TEXT NOT NULL,
	`IsPlayable`	BOOLEAN NOT NULL,
	`LinkedFrom`	TEXT,
	`Restrictions`	TEXT,
	`Name`	TEXT NOT NULL,
	`Popularity`	INTEGER,
	`PreviewUrl`	TEXT,
	`TrackNumber`	INTEGER NOT NULL,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`TrackId`)
);
CREATE TABLE IF NOT EXISTS `SavedTracks` (
	`UserId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`AdddedAt`	DATETIME,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`),
	PRIMARY KEY(`UserId`,`TrackId`)
);
CREATE TABLE IF NOT EXISTS `SavedArtists` (
	`UserId`	TEXT NOT NULL,
	`ArtistId`	TEXT NOT NULL,
	`AddedAt`	DATETIME,
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`),
	PRIMARY KEY(`UserId`,`ArtistId`),
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`)
);
CREATE TABLE IF NOT EXISTS `SavedAlbums` (
	`UserId`	TEXT NOT NULL,
	`AlbumId`	TEXT NOT NULL,
	`AddedAt`	DATETIME,
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`),
	PRIMARY KEY(`UserId`,`AlbumId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`)
);
CREATE TABLE IF NOT EXISTS `Playlists` (
	`PlaylistId`	TEXT,
	`Collaborative`	BOOLEAN NOT NULL,
	`Href`	TEXT NOT NULL,
	`Name`	TEXT NOT NULL,
	`Public`	BOOLEAN NOT NULL,
	`SnapshotId`	TEXT,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`PlaylistId`)
);
CREATE TABLE IF NOT EXISTS `PlaylistTracks` (
	`PlaylistTracksId`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`PlaylistId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`AddedAt`	DATETIME NOT NULL,
	`AddedBy`	TEXT NOT NULL,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`AddedBy`) REFERENCES `Users`(`UserId`),
	FOREIGN KEY(`PlaylistId`) REFERENCES `Playlists`(`PlaylistId`)
);
CREATE TABLE IF NOT EXISTS `PlayHistory` (
	`PlayHistoryId`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`UserId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`PlayedAt`	DATETIME NOT NULL,
	`ContextId`	TEXT,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`)
);
CREATE TABLE IF NOT EXISTS `Images` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Height`	INTEGER NOT NULL,
	`Width`	INTEGER NOT NULL,
	`Url`	TEXT NOT NULL,
	PRIMARY KEY(`ResourceId`,`Type`,`Url`)
);
CREATE TABLE IF NOT EXISTS `Followers` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Href`	TEXT,
	`Total`	INTEGER NOT NULL,
	PRIMARY KEY(`ResourceId`,`Type`)
);
CREATE TABLE IF NOT EXISTS `External_Urls` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Key`	TEXT NOT NULL,
	`Value`	TEXT,
	PRIMARY KEY(`ResourceId`,`Type`,`Key`)
);
CREATE TABLE IF NOT EXISTS `External_Ids` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Key`	TEXT NOT NULL,
	`Value`	TEXT,
	PRIMARY KEY(`ResourceId`,`Type`,`Key`)
);
CREATE TABLE IF NOT EXISTS `Copyrights` (
	`AlbumId`	TEXT,
	`Text`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	PRIMARY KEY(`AlbumId`)
);
CREATE TABLE IF NOT EXISTS `Categories` (
	`CategoryId`	TEXT,
	`Name`	TEXT NOT NULL,
	`Href`	TEXT NOT NULL,
	PRIMARY KEY(`CategoryId`)
);
CREATE TABLE IF NOT EXISTS `AudoFeatures` (
	`TrackId`	TEXT,
	`Acousticness`	DOUBLE,
	`AnalysisUrl`	TEXT NOT NULL,
	`Danceability`	DOUBLE,
	`DurationMs`	BIGINT,
	`Energy`	DOUBLE,
	`Instrumentalness`	DOUBLE,
	`Key`	INTEGER,
	`Liveness`	DOUBLE,
	`Loudness`	DOUBLE,
	`Mode`	INTEGER,
	`Speechiness`	DOUBLE,
	`Tempo`	DOUBLE,
	`TimeSignature`	INTEGER,
	`Uri`	TEXT,
	`Valence`	DOUBLE,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	PRIMARY KEY(`TrackId`)
);
CREATE TABLE IF NOT EXISTS `AudioAnalysis` (
	`TrackId`	TEXT,
	`Json`	TEXT NOT NULL,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	PRIMARY KEY(`TrackId`)
);
CREATE TABLE IF NOT EXISTS `Artists` (
	`ArtistId`	TEXT,
	`Genres`	TEXT NOT NULL,
	`Href`	TEXT NOT NULL,
	`Name`	TEXT NOT NULL,
	`Popularity`	INTEGER,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`ArtistId`)
);
CREATE TABLE IF NOT EXISTS `ArtistTrackMap` (
	`ArtistId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`),
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	PRIMARY KEY(`ArtistId`,`TrackId`)
);
CREATE TABLE IF NOT EXISTS `ArtistAlbumsMap` (
	`AlbumId`	TEXT NOT NULL,
	`ArtistId`	TEXT NOT NULL,
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`),
	PRIMARY KEY(`AlbumId`,`ArtistId`),
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`)
);
CREATE TABLE IF NOT EXISTS `Albums` (
	`AlbumId`	TEXT,
	`AlbumType`	TEXT NOT NULL,
	`AvailableMarkets`	TEXT NOT NULL,
	`Href`	TEXT NOT NULL,
	`Label`	TEXT,
	`Name`	TEXT NOT NULL,
	`ReleaseDate`	TEXT,
	`ReleaseDatePrecision`	TEXT,
	`Restrictions`	TEXT,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`AlbumId`)
);
CREATE TABLE IF NOT EXISTS `AlbumTrackMap` (
	`AlbumId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	PRIMARY KEY(`AlbumId`,`TrackId`),
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`),
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`)
);
COMMIT;
