# Rocket League Analytics
Rocket League detailed stat dashboard with expected goals analysis.

See dashboard here: https://sertalpbilal.github.io/rocket_league_analytics

## Generating xG model and dashboard

The xG model file is under `src/xg_model`.
The model depends on having a valid key from [ballchasing.com]() API.

Steps:
1. **Setting up environment**  
   Add your BallChasing token to `.env.sample` file and rename it to `.env`
2. **Collecting random game data (optional)**  
   Navigate to `src/scripts` and run `python collect_model_games.py`  
   This step will download latest 1000 ranked double games under `data/model` directory.
3. **Generating xG model (optional)**  
   Run `python generate_xg.py` to populate xG model.  
   Note that you might need to run this inside a Docker container if you cannot install `carball` package.  
   This step will populate two files under `data/model`: `xg.model` (gradient boosting xG model) and `xg.scaler` (feature scaler)
4. **Download your games**  
   You can go to `scripts` folder and run `python download_my_games.py`  
   This step will download your games to `data/replay` and will populate `data/json` and `data/dataframe` directories for future use.
5. **Generate the dashboard**  
   Finally you can go to `src` and run `python boxcartest.py` to populate the dashboard.

## Screenshots:
### Considering all games 
#### Click [here](https://sertalpbilal.github.io/rocket_league_analytics/dashboard.html) to view in an alternative format
![full_canvas.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/data/charts/full_canvas.png)

### Considering the latest streak of games 
#### Click [here](https://sertalpbilal.github.io/rocket_league_analytics/dashboard-latest-streak.html) to view in an alternative format
![full_canvas.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/data/charts/latest_streak/full_canvas.png)


## Output:
Alongside all of the charts produced by the program, the program also outputs 11 tables. 

1. ![Game Records](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/game_records.tsv)
2. ![Per Game Data](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/per_game_data.tsv)
3. ![Player 1's Positional Tendencies](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/p1_positional_tendency_data.tsv)
4. ![Player 2's Positional Tendencies](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/p2_positional_tendency_data.tsv)
5. ![Player Comparison](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/player_comparison.tsv)
6. ![Player Records](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/player_records.tsv)
7. ![Results](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/results.tsv)
8. ![Scorelines](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/scorelines.tsv)
9. ![Streaks](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/streaks.tsv)
10. ![Team Comparison](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/team_comparison.tsv)
11. ![Team Records](https://github.com/sertalpbilal/rocket_league_analytics/blob/main/data/tables/team_records.tsv)

Tables for the latest streak of matches can be found [here](https://github.com/sertalpbilal/rocket_league_analytics/tree/main/data/tables/latest_streak).
