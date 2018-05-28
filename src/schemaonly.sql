BEGIN TRANSACTION;
DROP TABLE IF EXISTS `Users`;
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
DROP TABLE IF EXISTS `UserFollowedArtists`;
CREATE TABLE IF NOT EXISTS `UserFollowedArtists` (
	`UserId`	TEXT NOT NULL,
	`ArtistId`	TEXT NOT NULL,
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`) ON DELETE CASCADE,
	PRIMARY KEY(`UserId`,`ArtistId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `Tracks`;
CREATE TABLE IF NOT EXISTS `Tracks` (
	`TrackId`	NUMERIC,
	`AvailableMarkets`	TEXT NOT NULL,
	`DiscNumber`	INTEGER NOT NULL,
	`DurationMs`	BIGINT NOT NULL,
	`Explicit`	BOOLEAN NOT NULL,
	`Href`	TEXT NOT NULL,
	`IsPlayable`	BOOLEAN NOT NULL,
	`Restrictions`	TEXT,
	`Name`	TEXT NOT NULL,
	`Popularity`	INTEGER,
	`PreviewUrl`	TEXT,
	`TrackNumber`	INTEGER NOT NULL,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`TrackId`)
);
DROP TABLE IF EXISTS `TrackRelinks`;
CREATE TABLE IF NOT EXISTS `TrackRelinks` (
	`TrackId`	TEXT NOT NULL,
	`UnavailableMarket`	TEXT NOT NULL,
	`AvailableTrackId`	TEXT NOT NULL,
	FOREIGN KEY(`AvailableTrackId`) REFERENCES `Tracks`(`TrackId`) ON DELETE CASCADE,
	PRIMARY KEY(`TrackId`,`UnavailableMarket`,`AvailableTrackId`)
);
DROP TABLE IF EXISTS `SavedTracks`;
CREATE TABLE IF NOT EXISTS `SavedTracks` (
	`UserId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`AddedAt`	DATETIME,
	`IsLocal`	INTEGER NOT NULL,
	PRIMARY KEY(`UserId`,`TrackId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`),
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`)
);
DROP TABLE IF EXISTS `SavedArtists`;
CREATE TABLE IF NOT EXISTS `SavedArtists` (
	`UserId`	TEXT NOT NULL,
	`ArtistId`	TEXT NOT NULL,
	`AddedAt`	DATETIME,
	PRIMARY KEY(`UserId`,`ArtistId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`),
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`)
);
DROP TABLE IF EXISTS `SavedAlbums`;
CREATE TABLE IF NOT EXISTS `SavedAlbums` (
	`UserId`	TEXT NOT NULL,
	`AlbumId`	TEXT NOT NULL,
	`AddedAt`	DATETIME,
	PRIMARY KEY(`UserId`,`AlbumId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`),
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`)
);
DROP TABLE IF EXISTS `Playlists`;
CREATE TABLE IF NOT EXISTS `Playlists` (
	`PlaylistId`	TEXT,
	`Collaborative`	BOOLEAN NOT NULL,
	`Href`	TEXT NOT NULL,
	`Name`	TEXT NOT NULL,
	`Public`	BOOLEAN NOT NULL,
	`SnapshotId`	TEXT,
	`Uri`	TEXT NOT NULL,
	`OwnerId`	TEXT NOT NULL,
	`Description`	TEXT,
	FOREIGN KEY(`OwnerId`) REFERENCES `Users`(`UserId`),
	PRIMARY KEY(`PlaylistId`)
);
DROP TABLE IF EXISTS `PlaylistTracks`;
CREATE TABLE IF NOT EXISTS `PlaylistTracks` (
	`PlaylistId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`AddedAt`	DATETIME NOT NULL,
	`AddedBy`	TEXT NOT NULL,
	FOREIGN KEY(`AddedBy`) REFERENCES `Users`(`UserId`),
	PRIMARY KEY(`PlaylistId`,`TrackId`,`AddedAt`,`AddedBy`),
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`PlaylistId`) REFERENCES `Playlists`(`PlaylistId`)
);
DROP TABLE IF EXISTS `PlayHistory`;
CREATE TABLE IF NOT EXISTS `PlayHistory` (
	`PlayHistoryId`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`UserId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	`PlayedAt`	DATETIME NOT NULL,
	`ContextId`	TEXT,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`UserId`) REFERENCES `Users`(`UserId`)
);
DROP TABLE IF EXISTS `Images`;
CREATE TABLE IF NOT EXISTS `Images` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Height`	INTEGER NOT NULL,
	`Width`	INTEGER NOT NULL,
	`Url`	TEXT NOT NULL,
	PRIMARY KEY(`ResourceId`,`Type`,`Url`)
);
DROP TABLE IF EXISTS `Followers`;
CREATE TABLE IF NOT EXISTS `Followers` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Href`	TEXT,
	`Total`	INTEGER NOT NULL,
	PRIMARY KEY(`ResourceId`,`Type`)
);
DROP TABLE IF EXISTS `FeaturedPlaylists`;
CREATE TABLE IF NOT EXISTS `FeaturedPlaylists` (
	`Message`	TEXT NOT NULL,
	`PlaylistId`	TEXT NOT NULL,
	PRIMARY KEY(`Message`,`PlaylistId`),
	FOREIGN KEY(`PlaylistId`) REFERENCES `Playlists`(`PlaylistId`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `External_Urls`;
CREATE TABLE IF NOT EXISTS `External_Urls` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Key`	TEXT NOT NULL,
	`Value`	TEXT,
	PRIMARY KEY(`ResourceId`,`Type`,`Key`)
);
DROP TABLE IF EXISTS `External_Ids`;
CREATE TABLE IF NOT EXISTS `External_Ids` (
	`ResourceId`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	`Key`	TEXT NOT NULL,
	`Value`	TEXT,
	PRIMARY KEY(`ResourceId`,`Type`,`Key`)
);
DROP TABLE IF EXISTS `Copyrights`;
CREATE TABLE IF NOT EXISTS `Copyrights` (
	`AlbumId`	TEXT,
	`Text`	TEXT NOT NULL,
	`Type`	TEXT NOT NULL,
	PRIMARY KEY(`AlbumId`),
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`)
);
DROP TABLE IF EXISTS `CategoryPlaylists`;
CREATE TABLE IF NOT EXISTS `CategoryPlaylists` (
	`CategoryId`	TEXT NOT NULL,
	`PlaylistId`	TEXT NOT NULL,
	FOREIGN KEY(`PlaylistId`) REFERENCES `Playlists`(`PlaylistId`) ON DELETE CASCADE,
	PRIMARY KEY(`CategoryId`,`PlaylistId`),
	FOREIGN KEY(`CategoryId`) REFERENCES `Categories`(`CategoryId`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `Categories`;
CREATE TABLE IF NOT EXISTS `Categories` (
	`CategoryId`	TEXT,
	`Name`	TEXT NOT NULL,
	`Href`	TEXT NOT NULL,
	PRIMARY KEY(`CategoryId`)
);
DROP TABLE IF EXISTS `AudioFeatures`;
CREATE TABLE IF NOT EXISTS `AudioFeatures` (
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
DROP TABLE IF EXISTS `AudioAnalyses`;
CREATE TABLE IF NOT EXISTS `AudioAnalyses` (
	`TrackId`	TEXT,
	`Json`	TEXT NOT NULL,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	PRIMARY KEY(`TrackId`)
);
DROP TABLE IF EXISTS `Artists`;
CREATE TABLE IF NOT EXISTS `Artists` (
	`ArtistId`	TEXT,
	`Genres`	TEXT NOT NULL,
	`Href`	TEXT NOT NULL,
	`Name`	TEXT NOT NULL,
	`Popularity`	INTEGER,
	`Uri`	TEXT NOT NULL,
	PRIMARY KEY(`ArtistId`)
);
DROP TABLE IF EXISTS `ArtistTrackMap`;
CREATE TABLE IF NOT EXISTS `ArtistTrackMap` (
	`ArtistId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`),
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`),
	PRIMARY KEY(`ArtistId`,`TrackId`)
);
DROP TABLE IF EXISTS `ArtistAlbumsMap`;
CREATE TABLE IF NOT EXISTS `ArtistAlbumsMap` (
	`AlbumId`	TEXT NOT NULL,
	`ArtistId`	TEXT NOT NULL,
	FOREIGN KEY(`ArtistId`) REFERENCES `Artists`(`ArtistId`),
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`),
	PRIMARY KEY(`AlbumId`,`ArtistId`)
);
DROP TABLE IF EXISTS `Albums`;
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
	`Popularity`	INTEGER,
	PRIMARY KEY(`AlbumId`)
);
DROP TABLE IF EXISTS `AlbumTrackMap`;
CREATE TABLE IF NOT EXISTS `AlbumTrackMap` (
	`AlbumId`	TEXT NOT NULL,
	`TrackId`	TEXT NOT NULL,
	FOREIGN KEY(`AlbumId`) REFERENCES `Albums`(`AlbumId`),
	PRIMARY KEY(`AlbumId`,`TrackId`),
	FOREIGN KEY(`TrackId`) REFERENCES `Tracks`(`TrackId`)
);
DROP INDEX IF EXISTS `TrackName`;
CREATE INDEX IF NOT EXISTS `TrackName` ON `Tracks` (
	`Name`
);
DROP INDEX IF EXISTS `PlaylistTrackIndex`;
CREATE INDEX IF NOT EXISTS `PlaylistTrackIndex` ON `PlaylistTracks` (
	`PlaylistId`,
	`TrackId`
);
DROP INDEX IF EXISTS `ArtistsName`;
CREATE INDEX IF NOT EXISTS `ArtistsName` ON `Artists` (
	`Name`	ASC
);
DROP INDEX IF EXISTS `AlbumName`;
CREATE INDEX IF NOT EXISTS `AlbumName` ON `Albums` (
	`Name`	ASC
);
COMMIT;
