docker build -t rocket_league_current .
docker run -m 4GB --rm -it -v %cd%:/app --env-file %cd%\.env rocket_league_current bash