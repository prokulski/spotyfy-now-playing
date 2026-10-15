# Now Playing

Worker zapisujący historię odtwarzania ze Spotify do PostgreSQL.

Program co kilka sekund sprawdza aktualnie odtwarzany utwór. Gdy wykryje zmianę utworu, zapisuje:

- postęp odtwarzania, czas trwania i urządzenie do tabeli `sp_plays`,
- informacje o utworze, albumie i cechach audio Spotify do tabeli `sp_features`,
- dodatkowe dane o utworze z Last.fm, jeśli API zwróci odpowiedź.

## Struktura

- `now_playing.py` - pętla główna aplikacji i koordynacja usług,
- `config.yaml` - niesekretne ustawienia aplikacji,
- `.env` - dane dostępowe i identyfikatory środowiskowe,
- `utils/config.py` - ładowanie i walidacja konfiguracji do niemutowalnych dataclass,
- `utils/spotify.py` - autoryzacja Spotify, aktualne odtwarzanie i cechy audio,
- `utils/lastfm.py` - klient API Last.fm,
- `utils/db.py` - SQLAlchemy, tworzenie tabel i zapis rekordów,
- `utils/logger.py` - konfiguracja logowania do konsoli i pliku.

## Wymagania

- Python 3.13 lub nowszy,
- konto Spotify z aplikacją w Spotify Developer Dashboard,
- klucz API Last.fm,
- PostgreSQL z bazą w kodowaniu UTF-8.

Zależności projektu są opisane w `pyproject.toml`, a ich zablokowane wersje w `uv.lock`.

## Konfiguracja

### `.env`

Utwórz plik `.env` na podstawie `.env.example`. Nie dodawaj go do repozytorium.

```env
SPOTIFY_USERNAME=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
LASTFM_API_KEY=
DB_HOST=
DB_PORT=5432
DB_NAME=spotify
DB_USER=
DB_PASSWORD=
```

Plik zawiera sekrety, hasło do bazy oraz identyfikatory konta i połączenia. Po ujawnieniu któregoś z kluczy należy go unieważnić i wygenerować ponownie.

### `config.yaml`

```yaml
spotify:
 scope: "user-read-currently-playing,user-read-playback-state"
 redirect_uri: "http://127.0.0.1:8080"

database:
 driver: "postgresql+psycopg2"

sleep_time: 5
```

`sleep_time` określa odstęp między kolejnymi odczytami Spotify w sekundach.

## Baza danych

Aplikacja używa SQLAlchemy i przy starcie tworzy brakujące tabele:

- `sp_plays` - historia odtworzeń,
- `sp_features` - cechy utworów oraz dane Last.fm.

Baza PostgreSQL powinna mieć kodowanie UTF-8:

```sql
SHOW server_encoding;
SHOW client_encoding;
```

Oczekiwane wartości to `UTF8` dla obu ustawień. Kodowanie jest właściwością całej bazy, nie pojedynczej tabeli.

## Uruchomienie

Przykład z `uv`:

```bash
uv sync
uv run python now_playing.py
```

Przy pierwszym uruchomieniu Spotipy może otworzyć proces autoryzacji Spotify. Token jest przechowywany w lokalnym pliku `.cache-*`, który jest ignorowany przez Git.

### Docker Compose

Skopiuj `.env.example` do `.env` i uzupełnij dane Spotify, Last.fm oraz PostgreSQL. Następnie zbuduj obraz i uruchom usługi:

```bash
./build-image.sh
docker compose up
```

Compose uruchamia worker oraz PostgreSQL. Przy pierwszym uruchomieniu autoryzuj Spotify w terminalu; token i logi są przechowywane w wolumenie `worker_state`, a dane bazy w `postgres_data`. Obraz nie zawiera pliku `.env`.

Aby zatrzymać usługi, użyj `docker compose down`. Dane pozostaną zachowane; `docker compose down -v` usuwa również wolumeny z tokenem i bazą.

## Uwagi

- Aktualny utwór jest zapisywany przy wykryciu następnego utworu. Zatrzymanie procesu przed zmianą utworu może więc nie zapisać ostatniego odtworzenia.
- Aplikacja jest procesem długotrwałym i wymaga działającego połączenia z PostgreSQL oraz dostępu do API Spotify i Last.fm.
