# Deep-Reinforcement-Learning-projects
Some of the algorithms and models of Deep Reinforcement Learning

UCB Algorithm for Multi-Armed Bandit Problem
This code implements the UCB (Upper Confidence Bound) algorithm for solving the Multi-Armed Bandit problem. The algorithm aims to solve the problem of deciding which ad to show to a user in a repeated online advertising scenario, where there are multiple ads to choose from, and the objective is to maximize the total reward (clicks or purchases).

Dataset
The dataset used in this code is Ads_CTR_Optimisation.csv. It contains the click-through rates of 10 different ads shown to 10000 users.

Implementing UCB
The UCB algorithm is implemented in Python using Numpy, Matplotlib and Pandas libraries.


Algorithm
Initialize the variables.
For each round n from 1 to N, do the following:
Choose the ad i with the highest upper confidence bound.
Update the variables.
Repeat step 2 for all the rounds.
Visualize the results using a histogram.

Visualizing the Results
The results are visualized using a histogram that shows the number of times each ad was selected. The histogram is plotted using Matplotlib library.
