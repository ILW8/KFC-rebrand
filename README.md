# 2024 API

## Setup
- Clone repository
- [Install Python 3.11](https://www.python.org/downloads/)
- [Optional] Create a virtual environment `python3 -m venv venv` and activate it
  - Windows: `venv\Scripts\activate.ps1`
  - *nix: `source venv/bin/activate`
- Install dependencies `python3 -m pip install -r requirements.txt`
- Aquire osu! and discord developer credentials (client ID and client secret)
  - [Discord developer portal](https://discord.com/developers/applications) -> Create new application -> OAuth2 -> Client ID & Client Secret
    - For development, add `http://127.0.0.1:8000/auth/discord/discord_code` to the list of allowed redirect URLs
  - [osu! account settings page](https://osu.ppy.sh/home/account/edit) -> Scroll down to OAuth -> New OAuth application
    - For development, add `http://127.0.0.1:8000/auth/osu/code` to list of allowed redirect URLs

## Running a development server
- Run a development server using `python3 manage.py runserver 127.0.0.1:8000`
  - Discord and osu OAuth credentials are provided using environment variables:
    - DISCORD_CLIENT_ID
    - DISCORD_CLIENT_SECRET
    - OSU_CLIENT_ID
    - OSU_CLIENT_SECRET
  - Either export them to your shell or provide them when running `runserver`:
```
DISCORD_CLIENT_ID="xxxxxxxxxx" DISCORD_CLIENT_SECRET="xxxxxxxxxx" OSU_CLIENT_ID="xxxxxxxxxx" OSU_CLIENT_SECRET="xxxxxxxxxxx" python3 manage.py runserver 127.0.0.1:8000
```
