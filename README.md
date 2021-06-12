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
![preview6.png](https://raw.githubusercontent.com/sertalpbilal/rocket_league_analytics/main/preview5.png)

## Output:
```
STATS            Allan    Sertalp
-------------  -------  ---------
Goals              248        218
Misses             234        260
G/Shot            0.51       0.46
Assists            105        112
Saves              285        233
Demos              216        113
Demoed              85         86
Score            76526      68681
Passes             686        748
Clears             626        576
Touches           5183       5052
Goal Distance     2718       2654
Miss Distance     3764       3521
Shot Distance     3267       3155
Won Ball          1172       1131
Lost Ball         1245       1189
Dribbles          1079       1007
Aerials            956        426


STATS              Us    Them
-------------  ------  ------
Goals             466     455
Misses            494     729
G/Shot           0.49    0.38
Assists           217     214
Saves             518     394
Demos             329     171
Score          145207  141898
Passes           1434    1587
Clears           1202    1197
Touches         10235   11911
Goal Distance    2688    2586
Miss Distance    3636    3557
Shot Distance    3211    3214
Won Ball         2303    2434
Dribbles         2086    2813
Aerials          1382    1872


Win %    Results                              Games    Wins    Losses    Allan Goals/G    Sertalp Goals/G    Our Goals/G    Their Goals/G    Goal Diff./G
-------  ---------------------------------  -------  ------  --------  ---------------  -----------------  -------------  ---------------  --------------
47%      W W W L W L L W L L W L W W L L L       17       8         9              1.6                1.5            3.1                3             0.1
54%      W W W L W W W W L L L L L               13       7         6                2                1.3            3.3              3.5            -0.2
75%      W W W L                                  4       3         1              1.5                2.8            4.2              1.8             2.5
41%      L L W L W L W W W L L L L L L W W       17       7        10              1.5                1.6            3.2              3.1             0.1
33%      L L W                                    3       1         2              1.7                2.3              4              4.3            -0.3
58%      W W L L L W L W W W L W                 12       7         5              1.6                1.8            3.3              2.9             0.4
50%      L L L W W L W W                          8       4         4              2.5                2.1            4.6                4             0.6
47%      W W W W L W W L L L W L L L L           15       7         8              1.5                1.5            3.1              3.1            -0.1
0%       L L L                                    3       0         3                1                  1              2                4              -2
38%      L L W W L L L W W L L L L W L W         16       6        10              1.4                1.2            2.6              2.9            -0.3
20%      L L W L L                                5       1         4                2                  1              3              3.4            -0.4
44%      W L W W L L L W L                        9       4         5              1.6                1.7            3.2              3.2               0
70%      L W W L L W W W W W                     10       7         3              2.1                0.6            2.7              1.7               1
75%      W L W W                                  4       3         1              2.5                  1            3.5              2.2             1.2
38%      L W W L W W L W L L L L L               13       5         8              1.2                1.2            2.5              3.2            -0.8


STATS      Overall    Normaltime    Overtime
-------  ---------  ------------  ----------
Games          149           128          21
Win %        46.98         49.22       33.33
Loss %       53.02         50.78       66.67
Wins            70            63           7
Losses          79            65          14


Execution time in seconds:  2.95
```

NOTE: Execution time also includes the time taken to display the dashboard. However it may then take another second or so to populate the plots in the dashboard.
