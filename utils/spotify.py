from dataclasses import asdict, dataclass
from typing import Any

import spotipy
from spotipy import util

from utils.config import Config
from utils.logger import get_logger


@dataclass
class SpotifyPlayback:
    timestamp: int
    item_id: str
    item_progress: int
    item_duration: int
    item_progress_percent: float
    device_name: str
    device_type: str

    @classmethod
    def from_spotify_response(cls, playback: dict[str, Any], timestamp: int):
        item = playback["item"]
        progress = playback["progress_ms"]
        duration = item["duration_ms"]
        device = playback["device"]

        return cls(
            timestamp=timestamp,
            item_id=item["id"],
            item_progress=progress,
            item_duration=duration,
            item_progress_percent=100 * progress / duration,
            device_name=device["name"],
            device_type=device["type"],
        )

    def update_from_spotify_response(self, playback: dict[str, Any], timestamp: int) -> None:
        self.timestamp = timestamp
        self.item_progress = playback["progress_ms"]
        self.item_progress_percent = 100 * self.item_progress / self.item_duration

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["item_durration"] = values.pop("item_duration")
        return values


@dataclass(frozen=True)
class SpotifyAudioFeatures:
    item_id: str
    danceability: float | None
    energy: float | None
    key: int | None
    loudness: float | None
    mode: int | None
    speechiness: float | None
    acousticness: float | None
    instrumentalness: float | None
    liveness: float | None
    valence: float | None
    tempo: float | None
    time_signature: int | None
    item_name: str | None
    item_artist: str | None
    item_track_number: int | None
    item_popularity: int | None
    item_url: str | None
    album_id: str | None
    album_name: str | None
    album_type: str | None
    album_url: str | None
    album_cover: str | None
    album_release_date: str | None
    album_total_tracks: int | None

    @classmethod
    def from_spotify_response(cls, track: dict[str, Any], audio_features: dict[str, Any]):
        item = track["item"]
        album = item["album"]
        images = album.get("images", [])

        return cls(
            item_id=item["id"],
            danceability=audio_features.get("danceability"),
            energy=audio_features.get("energy"),
            key=audio_features.get("key"),
            loudness=audio_features.get("loudness"),
            mode=audio_features.get("mode"),
            speechiness=audio_features.get("speechiness"),
            acousticness=audio_features.get("acousticness"),
            instrumentalness=audio_features.get("instrumentalness"),
            liveness=audio_features.get("liveness"),
            valence=audio_features.get("valence"),
            tempo=audio_features.get("tempo"),
            time_signature=audio_features.get("time_signature"),
            item_name=item.get("name"),
            item_artist=", ".join(artist.get("name", "") for artist in item.get("artists", [])),
            item_track_number=item.get("track_number"),
            item_popularity=item.get("popularity"),
            item_url=item.get("external_urls", {}).get("spotify"),
            album_id=album.get("id"),
            album_name=album.get("name"),
            album_type=album.get("album_type"),
            album_url=album.get("external_urls", {}).get("spotify"),
            album_cover=images[0].get("url") if images else None,
            album_release_date=album.get("release_date"),
            album_total_tracks=album.get("total_tracks"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpotifyClient:
    def __init__(self, config: Config):
        self._config = config
        self._logger = get_logger()
        self._client = self._create_client()

    def _create_client(self) -> spotipy.Spotify:
        token = util.prompt_for_user_token(
            self._config.spotify_username,
            self._config.spotify_scope,
            client_id=self._config.spotify_client_id,
            client_secret=self._config.spotify_client_secret,
            redirect_uri=self._config.spotify_redirect_uri,
        )
        client = spotipy.Spotify(auth=token)
        self._logger.info("Spotify client authorized")
        return client

    def reauthorize(self) -> None:
        self._logger.info("Reauthorizing Spotify client")
        self._client = self._create_client()

    def current_playback(self) -> dict[str, Any] | None:
        return self._client.current_playback()

    def get_audio_features(self, track: dict[str, Any]) -> SpotifyAudioFeatures | None:
        item_id = track["item"]["id"]
        audio_features = self._client.audio_features(item_id)
        if not audio_features or not audio_features[0]:
            return None

        return SpotifyAudioFeatures.from_spotify_response(track, audio_features[0])
