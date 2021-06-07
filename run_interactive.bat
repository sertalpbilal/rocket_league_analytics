docker build -t rocket_league_current .
docker run --rm -it -v %cd%\data:/data -v %cd%\src:/src --env-file %cd%\.env rocket_league_current bash