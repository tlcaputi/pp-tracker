# PP Tracker

This tracks the best two EV bets on PP over time. 

`pp-selenium-loop.sh` runs forever. Every X minutes, it runs `pp-selenium.py`, which pulls the odds and plots the best two bets using `pp-plot.R`. The results are in `output-pp-selenium`. The whole repo is automatically updated after every Y pulls.

The relevant result is output-pp-selenium/output-pp-selenium-YYYYMMDD.pdf for the most recent date. This gives you the two best EV bets. The idea here is that we look for two bets with the highest value of `min(multiplier1, multiplier2)`, which reduces variance. You can bet on the over/over, over/under, under/over, under/under for these two bets and you'll get the highest possible guaranteed return. Among those, we look for the bets with the highest `product := multiplier1 * multiplier2`, which will give you the highest EV. 