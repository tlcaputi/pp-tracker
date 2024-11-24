# PP Tracker

This tracks the best two highest guaranteed-value matched bets on PP over time. 

`pp-selenium-loop.sh` runs forever. Every X minutes, it runs `pp-selenium.py`, which pulls the odds and plots the best two bets using `pp-plot.R`. The results are in `output-pp-selenium`. The whole repo is automatically updated after every Y pulls.

The relevant result is `current-multiplier.pdf`, which reflects the most recent date. This gives you the two best matched bets bets, and how they have changed over the course of the day. The idea here is that we look for two bets from different games with the highest value of `min(multiplier1, multiplier2)` because the lowest multiplier on two matched bets is the guaranteed return of the matched bet. You can bet on the over/over, over/under, under/over, under/under for these two bets and you'll get the highest possible guaranteed return. Among those, we look for the bets with the highest `product := multiplier1 * multiplier2`, which will give you the highest expected value. 

## Matched Bets

This is to help you place matched bets. You'll pick four varieties of two lines: over/over, over/under, under/over, and under/under. One of those is guaranteed to win, and the others are guaranteed to lose. If the minimum multiplier is 1.83, you'll expect to earn (1.83^2)/4 on your bet, which is a loss. However, if some of the initial deposit is a deposit match, you could end up ahead.

For example, say you deposit $100 and receive $100 in deposit match. You can place four $50 bets on over/over, over/under, under/over, and under/under, with a minimum multiplier across those two lines of 1.83. One of those will win (1.83^2)*(200/4) = $167. The others will lose. You will therefore make $167 risk free for $100 -- a 67% return.