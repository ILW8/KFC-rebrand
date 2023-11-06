# 2024 API

## Setup
- Clone repository
  - Include submodules by either passing `--recursive` flag to `git clone` or
  - Run `git submodule update --init --recursive` after the fact
- [Install Python 3.11](https://www.python.org/downloads/)
- [Optional] Create a virtual environment `python3 -m venv venv` and activate it
  - Windows: `venv\Scripts\activate.ps1`
  - *nix: `source venv/bin/activate`
- Install dependencies `python3 -m pip install -r requirements.txt`
- Acquire osu! and discord developer credentials (client ID and client secret)
  - [Discord developer portal](https://discord.com/developers/applications) -> Create new application -> OAuth2 -> Client ID & Client Secret
    - For development, add `http://127.0.0.1:8000/auth/discord/discord_code` to the list of allowed redirect URLs
  - [osu! account settings page](https://osu.ppy.sh/home/account/edit) -> Scroll down to OAuth -> New OAuth application
    - For development, add `http://127.0.0.1:8000/auth/osu/code` to list of allowed redirect URLs
- Database setup
  - For development purposes, a SQLite database should suffice. In `fivedigitworldcup/settings.py` in DATABASES dictionary:
    ```
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'db.sqlite3',
      }
      ```
  - Alternatively, create a database at [PlanetScale](https://app.planetscale.com)
    - Once the databse is created, create a password. Select "Connect with: Django" and follow the instructions.
    - Replace the database's `ENGINE` with `'ENGINE': 'django_psdb_engine'` for proper foreign key support.

## Running a development server
- Run database migrations if not already done: `python3 manage.py migrate`
- Run a development server using `python3 manage.py runserver 127.0.0.1:8000`
  - Discord and osu OAuth credentials are provided using environment variables:
    - DISCORD_CLIENT_ID
    - DISCORD_CLIENT_SECRET
    - OSU_CLIENT_ID
    - OSU_CLIENT_SECRET
  - Discord and osu OAuth require a redirect URL to be specified. This defaults to http://localhost:8000 which is fine for local development. This redirect URL can be given using an environment variable
    - OAUTH_REDIRECT_PREFIX
  - Either export them to your shell or provide them when running `runserver`:
```
OAUTH_REDIRECT_PREFIX="https://xxxxx.example.com:8000" \
DISCORD_CLIENT_ID="xxxxxxxxxx" \
DISCORD_CLIENT_SECRET="xxxxxxxxxx" \
OSU_CLIENT_ID="xxxxxxxxxx" \
OSU_CLIENT_SECRET="xxxxxxxxxxx" \
python3 manage.py runserver 127.0.0.1:8000
```

### macOS specific notes:
- Installing mysqlclient:
  - First install `mysql-client` and `pkg-config` using brew: 
    - ```brew install mysql-client pkg-config```
  - Export PKG_CONFIG_PATH and install `mysqlclient` by itself
    - ```PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig" python3 -m pip install mysqlclient~=2.2.0```
  - Install rest of dependencies: `python3 -m pip install -r requirements.txt`
