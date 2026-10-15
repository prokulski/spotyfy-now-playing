import time
from datetime import datetime

from utils.config import load_config
from utils.db import Database
from utils.lastfm import LastFmClient
from utils.logger import get_logger
from utils.spotify import SpotifyAudioFeatures, SpotifyClient, SpotifyPlayback

logger = get_logger(logger_name="now_playing")
config = load_config()

database = Database(config.database)
spotify_plays, spotify_features = database.build_tables()


def main():
    spotify = SpotifyClient(config)
    lastfm = LastFmClient(config.lastfm_api_key)

    last_item_id = "xxx"
    playback: SpotifyPlayback | None = None
    first_time = True
    item_features: SpotifyAudioFeatures | None = None
    lastfm_info = {}

    while True:
        try:
            currently_playing = spotify.current_playback()
        except Exception as err:
            logger.error("Spotify playback request failed", extra={"error": str(err)})
            spotify.reauthorize()
            continue

        if currently_playing and currently_playing.get("is_playing", False):
            if not currently_playing.get("item"):
                continue

            current_id = currently_playing.get("item", {}).get("id")

            if current_id != last_item_id:
                # zmieniła się piosenka - zapisujemy tą poprzednią
                if not first_time and item_features and playback:
                    logger.info(
                        f'Track "{item_features.item_name}" / {item_features.item_artist} playback completed at {playback.item_progress_percent:.1f}%',
                        extra={
                            "played_at": datetime.fromtimestamp(playback.timestamp).isoformat(),
                            "item_id": item_features.item_id,
                            "item_name": item_features.item_name,
                            "item_artist": item_features.item_artist,
                            "album_name": item_features.album_name,
                            "album_type": item_features.album_type,
                            "album_release_date": item_features.album_release_date,
                            "item_progress": playback.item_progress,
                            "item_duration": playback.item_duration,
                            "item_progress_percent": playback.item_progress_percent,
                            "device_name": playback.device_name,
                            "device_type": playback.device_type,
                        },
                    )
                    try:
                        database.save_record(spotify_plays, playback)
                        database.save_record(spotify_features, item_features, lastfm_info)
                    except Exception as err:
                        logger.error(
                            "Database save failed",
                            extra={"error": str(err), "item_id": item_features.item_id},
                        )

                # i budujemy obiekt dla nowej
                playback = SpotifyPlayback.from_spotify_response(currently_playing, int(time.time()))

                try:
                    item_features = spotify.get_audio_features(currently_playing)
                    if item_features is None:
                        logger.warning(
                            "Spotify returned no audio features",
                            extra={"item_id": current_id},
                        )
                        lastfm_info = {}
                    elif item_features.item_name is None or item_features.item_artist is None:
                        logger.warning(
                            "Spotify track has no title or artist",
                            extra={"item_id": current_id},
                        )
                        lastfm_info = {}
                    else:
                        lastfm_info = lastfm.get_track_info(item_features.item_name, item_features.item_artist)
                    first_time = False
                except Exception as e:
                    logger.error(
                        "Problem with getting/adding track features",
                        extra={"error": str(e), "item_id": current_id},
                    )

                last_item_id = current_id

            else:
                # piosenka ta sama - update postępu
                if playback is None:
                    continue

                playback.update_from_spotify_response(currently_playing, int(time.time()))

        time.sleep(config.sleep_time)


if __name__ == "__main__":
    main()
