# Rocket League Analytics
Rocket League detailed stat dashboard with expected goals analysis

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
![full_canvas.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/full_canvas.png)

## Output:
```
STATS               Allan    Sertalp
----------------  -------  ---------
Goals                 333        289
Goals from Shots      292        254
xG                    250        233
GfS/Shot Ratio       0.46       0.42
GfS/xG Ratio         1.17       1.09
Shots                 629        609
Misses                337        355
Assists               138        146
Saves                 377        307
Demos                 297        149
Demoed                115        122
Score              103301      91989
Passes                909        994
Clears                883        787
Touches              7093       6770
Goal Distance        2608       2634
Miss Distance        3715       3478
Shot Distance        3201       3126
Won Ball             1599       1528
Lost Ball            1692       1582
Dribbles             1519       1382
Aerials              1268        562


STATS                 Us    Them
----------------  ------  ------
Goals                622     592
Goals from Shots     546     519
xG                   482     496
GfS/Shot Ratio      0.44    0.35
GfS/xG Ratio        1.13    1.05
Shots               1238    1474
Misses               692     955
Assists              284     286
Saves                684     546
Demos                446     237
Score             195290  189092
Passes              1903    2121
Clears              1670    1637
Touches            13863   15900
Goal Distance       2620    2610
Miss Distance       3594    3577
Shot Distance       3164    3237
Won Ball            3127    3274
Dribbles            2901    3752
Aerials             1830    2482


Win %    Results                               GP    W    L    Allan GS/G    Sertalp GS/G    GS/G    GC/G    GD/G    Allan xG/G    Sertalp xG/G    xG/G    xGC/G    xGD/G
-------  ----------------------------------  ----  ---  ---  ------------  --------------  ------  ------  ------  ------------  --------------  ------  -------  -------
47%      W W W L W L L W L L W L W W L L L     17    8    9           1.6             1.5     3.1       3     0.1           1.2             1.3     2.5      2.8     -0.3
54%      W W W L W W W W L L L L L             13    7    6             2             1.3     3.3     3.5    -0.2           1.3             0.9     2.2      2.7     -0.5
75%      W W W L                                4    3    1           1.5             2.8     4.2     1.8     2.5           1.3               2     3.3      2.1      1.2
41%      L L W L W L W W W L L L L L L W W     17    7   10           1.5             1.6     3.2     3.1     0.1             1             1.1     2.1      2.5     -0.4
33%      L L W                                  3    1    2           1.7             2.3       4     4.3    -0.3           1.8             2.1       4      3.4      0.6
58%      W W L L L W L W W W L W               12    7    5           1.6             1.8     3.3     2.9     0.4           1.3             1.5     2.8      2.1      0.7
50%      L L L W W L W W                        8    4    4           2.5             2.1     4.6       4     0.6           1.6             1.3     2.8      2.9     -0.1
47%      W W W W L W W L L L W L L L L         15    7    8           1.5             1.5     3.1     3.1    -0.1           1.2               1     2.3      2.7     -0.5
0%       L L L                                  3    0    3             1               1       2       4      -2             1             0.8     1.8      4.2     -2.4
38%      L L W W L L L W W L L L L W L W       16    6   10           1.4             1.2     2.6     2.9    -0.3           1.2             0.9     2.1      2.5     -0.4
20%      L L W L L                              5    1    4             2               1       3     3.4    -0.4           1.4             1.1     2.5      2.5     -0.1
44%      W L W W L L L W L                      9    4    5           1.6             1.7     3.2     3.2       0           0.9             1.4     2.3      2.3        0
70%      L W W L L W W W W W                   10    7    3           2.1             0.6     2.7     1.7       1           1.3             0.6       2      1.6      0.3
75%      W L W W                                4    3    1           2.5               1     3.5     2.2     1.2             1             1.4     2.4      1.9      0.5
38%      L W W L W W L W L L L L L             13    5    8           1.2             1.2     2.5     3.2    -0.8           0.8             1.1     1.9      3.1     -1.2
0%       L L L                                  3    0    3           1.3             0.3     1.7     5.3    -3.7           1.5             0.9     2.4      2.6     -0.2
67%      W L L W W W W L W                      9    6    3           2.2             1.3     3.6     2.2     1.3           1.8               1     2.8      2.1      0.8
75%      W L W W W W L W W L W W               12    9    3           1.8             2.1     3.8     2.4     1.4           1.4             1.5     2.9      1.5      1.4
43%      L W L L L W W L W W W L L L           14    6    8           1.7             1.1     2.9     2.6     0.2           1.5               1     2.5      2.4      0.1
43%      W L L L W W L W L L L W W L           14    6    8           1.1             1.2     2.4     2.5    -0.1           1.2             1.1     2.3      2.4     -0.2


STATS      Overall    Normaltime    Overtime
-------  ---------  ------------  ----------
Games          201           169          32
Win %        48.26         50.89       34.38
Loss %       51.74         49.11       65.62
Wins            97            86          11
Losses         104            83          21

Execution time in seconds:  9.92
```

NOTE: Execution time also includes the time taken to display the dashboard. However it may then take another second or so to populate the plots in the dashboard. In this case it also takes into account how long it took to crop each individual chart image.
