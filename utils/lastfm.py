import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

import requests

from utils.logger import get_logger


class LastFmClient:
    _endpoint = "https://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._logger = get_logger()

    def get_track_info(self, title: str, artist: str) -> Mapping[str, Any]:
        normalized_title = re.sub(r"\(.*\)", "", title).strip()
        query = urlencode(
            {
                "track": normalized_title,
                "artist": artist,
                "method": "track.getinfo",
                "api_key": self._api_key,
                "format": "json",
            }
        )

        try:
            response = requests.get(f"{self._endpoint}?{query}")
        except Exception as error:
            self._logger.error(
                "LastFM request failed",
                extra={"error": str(error), "title": normalized_title, "artist": artist},
            )
            return {}

        if response.status_code != 200:
            self._logger.error(
                "LastFM returned an error status",
                extra={
                    "status_code": response.status_code,
                    "title": normalized_title,
                    "artist": artist,
                },
            )
            return {}

        data = response.json()
        if data.get("error"):
            self._logger.error(
                "LastFM returned an API error",
                extra={
                    "error": data.get("message"),
                    "title": normalized_title,
                    "artist": artist,
                },
            )
            return {}

        return self._build_track_info(data["track"])

    @staticmethod
    def _build_track_info(results: dict[str, Any]) -> dict[str, Any]:
        track_info = {
            "lastfm_track_title": results.get("name"),
            "lastfm_track_url": results.get("url"),
            "lastfm_track_mbid": results.get("mbid"),
            "lastfm_track_listeners": int(results.get("listeners", 0)),
            "lastfm_track_playcount": int(results.get("playcount", 0)),
        }

        if results.get("artist"):
            track_info["lastfm_artist_mbid"] = results["artist"].get("mbid")

        if results.get("album"):
            track_info.update(
                {
                    "lastfm_album_title": results["album"].get("title"),
                    "lastfm_album_mbid": results["album"].get("mbid"),
                }
            )

        tags = results.get("toptags", {}).get("tag", [])
        if tags:
            track_info["lastfm_track_tags"] = "#" + " #".join(tag.get("name", "").replace(" ", "-").lower() for tag in tags)

        return track_info
