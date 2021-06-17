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
Goals                 351        309
Goals from Shots      310        271
xG                    263        245
GfS/Shot Ratio       0.46       0.42
GfS/xG Ratio         1.18        1.1
Shots                 677        644
Misses                367        373
Assists               148        153
Saves                 400        326
Demos                 305        155
Demoed                119        129
Score              109651      97409
Passes                960       1048
Clears                932        820
Touches              7478       7146
Goal Distance        2674       2606
Miss Distance        3736       3522
Shot Distance        3250       3137
Won Ball             1687       1613
Lost Ball            1792       1666
Dribbles             1594       1462
Aerials              1334        589


STATS                 Us    Them
----------------  ------  ------
Goals                660     625
Goals from Shots     581     546
xG                   508     526
GfS/Shot Ratio      0.44    0.35
GfS/xG Ratio        1.14    1.04
Shots               1321    1559
Misses               740    1013
Assists              301     306
Saves                726     584
Demos                460     248
Score             207060  199862
Passes              2008    2236
Clears              1752    1718
Touches            14624   16778
Goal Distance       2643    2599
Miss Distance       3628    3570
Shot Distance       3195    3230
Won Ball            3300    3458
Dribbles            3056    3961
Aerials             1923    2657


Win %    Results                               GP    W    L    Allan GS/G    Sertalp GS/G    GS/G    GC/G    GD/G    Allan xG/G    Sertalp xG/G    xG/G    xGC/G    xGD/G
-------  ----------------------------------  ----  ---  ---  ------------  --------------  ------  ------  ------  ------------  --------------  ------  -------  -------
47%      W W W L W L L W L L W L W W L L L     17    8    9           1.6             1.5     3.1       3     0.1           1.2             1.4     2.5      2.8     -0.2
54%      W W W L W W W W L L L L L             13    7    6             2             1.3     3.3     3.5    -0.2           1.3             0.9     2.2      2.6     -0.4
75%      W W W L                                4    3    1           1.5             2.8     4.2     1.8     2.5           1.2             1.8     3.1      2.4      0.7
41%      L L W L W L W W W L L L L L L W W     17    7   10           1.5             1.6     3.2     3.1     0.1             1             1.1     2.1      2.5     -0.4
33%      L L W                                  3    1    2           1.7             2.3       4     4.3    -0.3           1.3             1.8       3        3      0.1
58%      W W L L L W L W W W L W               12    7    5           1.6             1.8     3.3     2.9     0.4           1.3             1.4     2.6      2.2      0.4
50%      L L L W W L W W                        8    4    4           2.5             2.1     4.6       4     0.6           1.6             1.4       3        3     -0.1
47%      W W W W L W W L L L W L L L L         15    7    8           1.5             1.5     3.1     3.1    -0.1           1.2               1     2.2      2.7     -0.5
0%       L L L                                  3    0    3             1               1       2       4      -2             1             0.8     1.8      4.2     -2.4
38%      L L W W L L L W W L L L L W L W       16    6   10           1.4             1.2     2.6     2.9    -0.3           1.2             0.9     2.2      2.4     -0.2
20%      L L W L L                              5    1    4             2               1       3     3.4    -0.4           1.4             1.1     2.5      2.5       -0
44%      W L W W L L L W L                      9    4    5           1.6             1.7     3.2     3.2       0           0.9             1.4     2.3      2.2      0.1
70%      L W W L L W W W W W                   10    7    3           2.1             0.6     2.7     1.7       1           1.4             0.8     2.2      1.7      0.4
75%      W L W W                                4    3    1           2.5               1     3.5     2.2     1.2           1.2             1.3     2.5      2.2      0.3
38%      L W W L W W L W L L L L L             13    5    8           1.2             1.2     2.5     3.2    -0.8           0.8               1     1.9      3.1     -1.3
0%       L L L                                  3    0    3           1.3             0.3     1.7     5.3    -3.7           1.5             0.9     2.4      2.5     -0.1
67%      W L L W W W W L W                      9    6    3           2.2             1.3     3.6     2.2     1.3           1.7             1.1     2.8        2      0.8
75%      W L W W W W L W W L W W               12    9    3           1.8             2.1     3.8     2.4     1.4           1.5             1.5       3      1.4      1.6
43%      L W L L L W W L W W W L L L           14    6    8           1.7             1.1     2.9     2.6     0.2           1.5               1     2.5      2.5      0.1
43%      W L L L W W L W L L L W W L           14    6    8           1.1             1.2     2.4     2.5    -0.1           1.1               1     2.1      2.5     -0.4
73%      W W W W L W L W L W W                 11    8    3           1.6             1.8     3.5       3     0.5           1.4             1.3     2.7      2.8     -0.1


STATS      Overall    Normaltime    Overtime
-------  ---------  ------------  ----------
Games          212           178          34
Win %        49.53         51.69       38.24
Loss %       50.47         48.31       61.76
Wins           105            92          13
Losses         107            86          21
```

