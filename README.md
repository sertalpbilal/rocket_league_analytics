# Rocket League Analytics
Rocket League detailed stat dashboard with expected goals analysis

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
![preview8.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/preview8.png)

## Output:
```
STATS               Allan    Sertalp
----------------  -------  ---------
Goals                 317        272
Goals from Shots      277        239
xG                    224        221
GfS/Shot Ratio       0.47       0.42
GfS/xG Ratio         1.24       1.08
Shots                 586        572
Misses                309        333
Assists               128        136
Saves                 350        287
Demos                 273        135
Demoed                109        110
Score               95931      86093
Passes                837        920
Clears                819        726
Touches              6561       6295
Goal Distance        2598       2604
Miss Distance        3665       3496
Shot Distance        3161       3123
Won Ball             1479       1423
Lost Ball            1570       1483
Dribbles             1400       1278
Aerials              1173        521


STATS                 Us    Them
----------------  ------  ------
Goals                589     557
Goals from Shots     516     489
xG                   445     459
GfS/Shot Ratio      0.45    0.35
GfS/xG Ratio        1.16    1.07
Shots               1158    1379
Misses               642     890
Assists              264     265
Saves                637     508
Demos                408     219
Score             182024  176312
Passes              1757    1990
Clears              1545    1515
Touches            12856   14861
Goal Distance       2601    2643
Miss Distance       3577    3564
Shot Distance       3142    3237
Won Ball            2902    3053
Dribbles            2678    3521
Aerials             1694    2309


Win %    Results                               GP    W    L    Allan GS/G    Sertalp GS/G    GS/G    GC/G    GD/G    Allan xG/G    Sertalp xG/G    xG/G    xGC/G    xGD/G
-------  ----------------------------------  ----  ---  ---  ------------  --------------  ------  ------  ------  ------------  --------------  ------  -------  -------
47%      W W W L W L L W L L W L W W L L L     17    8    9           1.6             1.5     3.1       3     0.1           1.1             1.5     2.6      2.7     -0.1
54%      W W W L W W W W L L L L L             13    7    6             2             1.3     3.3     3.5    -0.2           1.3             0.9     2.2      2.6     -0.3
75%      W W W L                                4    3    1           1.5             2.8     4.2     1.8     2.5           1.1             2.1     3.1      1.9      1.2
41%      L L W L W L W W W L L L L L L W W     17    7   10           1.5             1.6     3.2     3.1     0.1             1             1.2     2.1      2.6     -0.4
33%      L L W                                  3    1    2           1.7             2.3       4     4.3    -0.3           1.2             2.2     3.4      3.2      0.2
58%      W W L L L W L W W W L W               12    7    5           1.6             1.8     3.3     2.9     0.4           1.3             1.5     2.9      2.2      0.7
50%      L L L W W L W W                        8    4    4           2.5             2.1     4.6       4     0.6           1.6             1.1     2.7      3.1     -0.4
47%      W W W W L W W L L L W L L L L         15    7    8           1.5             1.5     3.1     3.1    -0.1           1.1             1.1     2.2      2.7     -0.5
0%       L L L                                  3    0    3             1               1       2       4      -2             1             0.8     1.8      4.2     -2.3
38%      L L W W L L L W W L L L L W L W       16    6   10           1.4             1.2     2.6     2.9    -0.3           1.2             0.9     2.1      2.4     -0.3
20%      L L W L L                              5    1    4             2               1       3     3.4    -0.4           1.3             1.2     2.5      2.6     -0.1
44%      W L W W L L L W L                      9    4    5           1.6             1.7     3.2     3.2       0           0.8             1.3     2.1      2.4     -0.3
70%      L W W L L W W W W W                   10    7    3           2.1             0.6     2.7     1.7       1           1.3             0.7       2      1.6      0.4
75%      W L W W                                4    3    1           2.5               1     3.5     2.2     1.2           1.1             1.3     2.3      2.1      0.2
38%      L W W L W W L W L L L L L             13    5    8           1.2             1.2     2.5     3.2    -0.8           0.9               1     1.9      3.2     -1.3
0%       L L L                                  3    0    3           1.3             0.3     1.7     5.3    -3.7           1.2               1     2.2      2.4     -0.3
67%      W L L W W W W L W                      9    6    3           2.2             1.3     3.6     2.2     1.3           1.6             1.1     2.7      2.1      0.6
75%      W L W W W W L W W L W W               12    9    3           1.8             2.1     3.8     2.4     1.4           1.4             1.5       3      1.4      1.5
43%      L W L L L W W L W W W L L L           14    6    8           1.7             1.1     2.9     2.6     0.2           1.3               1     2.3      2.4     -0.1


STATS      Overall    Normaltime    Overtime
-------  ---------  ------------  ----------
Games          187           157          30
Win %        48.66         51.59       33.33
Loss %       51.34         48.41       66.67
Wins            91            81          10
Losses          96            76          20


Execution time in seconds:  4.20
```

NOTE: Execution time also includes the time taken to display the dashboard. However it may then take another second or so to populate the plots in the dashboard.
