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
![preview7.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/preview7.png)

## Output:
```
STATS               Allan    Sertalp
----------------  -------  ---------
Goals                 272        231
Goals from Shots      233        203
xG                    178        175
GfS/Shot Ratio       0.47       0.42
GfS/xG Ratio         1.31       1.16
Misses                261        283
Assists               109        117
Saves                 306        249
Demos                 241        116
Demoed                 90         89
Score               83089      73335
Passes                735        806
Clears                687        622
Touches              5632       5418
Goal Distance        2634       2648
Miss Distance        3658       3500
Shot Distance        3175       3144
Won Ball             1267       1218
Lost Ball            1345       1278
Dribbles             1187       1080
Aerials              1016        448


STATS                 Us    Them
----------------  ------  ------
Goals                503     491
Goals from Shots     436     431
xG                   354     387
GfS/Shot Ratio      0.44    0.36
GfS/xG Ratio        1.23    1.11
Misses               544     780
Assists              226     232
Saves                555     430
Demos                357     179
Score             156424  153053
Passes              1541    1713
Clears              1309    1290
Touches            11050   12809
Goal Distance       2641    2615
Miss Distance       3576    3558
Shot Distance       3160    3222
Won Ball            2485    2623
Dribbles            2267    3034
Aerials             1464    2003


Win %    Results                              GP    W    L    Allan GS/G    Sertalp GS/G    GS/G    GC/G    GD/G    Allan xG/G    Sertalp xG/G    xG/G    xGC/G    xGD/G
-------  ---------------------------------  ----  ---  ---  ------------  --------------  ------  ------  ------  ------------  --------------  ------  -------  -------
47%      W W W L W L L W L L W L W W L L L    17    8    9           1.6             1.5     3.1       3    -0.4             1             1.3     2.3      2.7     -0.4
54%      W W W L W W W W L L L L L            13    7    6             2             1.3     3.3     3.5    -0.3           1.2             0.8     2.1      2.4     -0.3
75%      W W W L                               4    3    1           1.5             2.8     4.2     1.8     1.3           1.1             1.8     2.8      1.6      1.3
41%      L L W L W L W W W L L L L L L W W    17    7   10           1.5             1.6     3.2     3.1    -0.5             1               1       2      2.5     -0.5
33%      L L W                                 3    1    2           1.7             2.3       4     4.3     0.6           1.3             2.2     3.6        3      0.6
58%      W W L L L W L W W W L W              12    7    5           1.6             1.8     3.3     2.9     0.7           1.3             1.4     2.7      2.1      0.7
50%      L L L W W L W W                       8    4    4           2.5             2.1     4.6       4      -0           1.5             1.3     2.8      2.8       -0
47%      W W W W L W W L L L W L L L L        15    7    8           1.5             1.5     3.1     3.1    -0.4           1.1             0.9       2      2.4     -0.4
0%       L L L                                 3    0    3             1               1       2       4    -3.5           0.8             0.5     1.3      4.7     -3.5
38%      L L W W L L L W W L L L L W L W      16    6   10           1.4             1.2     2.6     2.9    -0.3           1.1             0.9     1.9      2.3     -0.3
20%      L L W L L                             5    1    4             2               1       3     3.4    -0.1           1.3             1.2     2.4      2.5     -0.1
44%      W L W W L L L W L                     9    4    5           1.6             1.7     3.2     3.2    -0.2           0.8             1.2       2      2.2     -0.2
70%      L W W L L W W W W W                  10    7    3           2.1             0.6     2.7     1.7     0.3           1.3             0.6     1.9      1.7      0.3
75%      W L W W                               4    3    1           2.5               1     3.5     2.2    -0.3           0.9             0.9     1.9      2.1     -0.3
38%      L W W L W W L W L L L L L            13    5    8           1.2             1.2     2.5     3.2      -1           0.7             1.1     1.8      2.8       -1
0%       L L L                                 3    0    3           1.3             0.3     1.7     5.3     0.4           1.5               1     2.5      2.1      0.4
67%      W L L W W W W L W                     9    6    3           2.2             1.3     3.6     2.2     0.5           1.6               1     2.5        2      0.5


STATS      Overall    Normaltime    Overtime
-------  ---------  ------------  ----------
Games          161           139          22
Win %         47.2         49.64       31.82
Loss %        52.8         50.36       68.18
Wins            76            69           7
Losses          85            70          15


Execution time in seconds:  4.13
```

NOTE: Execution time also includes the time taken to display the dashboard. However it may then take another second or so to populate the plots in the dashboard.
