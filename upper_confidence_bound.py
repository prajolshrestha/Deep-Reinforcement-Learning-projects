## Importing the libraries


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

## Importing the dataset"""

dataset = pd.read_csv('Ads_CTR_Optimisation.csv')

"""## Implementing UCB"""

import math

#initialize parameters
N = 10000 #no of user
d = 10    #no of ads
ads_selected = [] #list of ads selected
numbers_of_selections = [0] * d #list of 10 zeros #no of each ad selected
sums_of_rewards = [0] * d #sum of reward of ad i
total_reward = 0


#iterate through all round
for n in range(0,N):
    ad = 0
    max_upper_bound = 0

    #find max upper bound in among all 10 ads
    for i in range(0,d):   
        if numbers_of_selections[i] > 0: 
            
            average_reward = sums_of_rewards[i] / numbers_of_selections[i]
            delta_i = math.sqrt((3/2)*(math.log(n+1)/numbers_of_selections[i]))
            upper_bound =  average_reward + delta_i
        else:          #when ad is not clicked
            upper_bound = 1e400 #infinte value 
        if upper_bound > max_upper_bound :  #step 3
            max_upper_bound = upper_bound
            ad = i

    #update variables        
    ads_selected.append(ad)
    numbers_of_selections[ad] += 1
    reward = dataset.values[n,ad]
    sums_of_rewards[ad] =  sums_of_rewards[ad] + reward
    total_reward = total_reward + reward

#N
# d
#ads_selected
numbers_of_selections
# sums_of_rewards
# total_reward

"""## Visualising the results"""

plt.hist(ads_selected)
plt.title('Histogram of ads selections')
plt.xlabel('Ads')
plt.ylabel('Number of times each ad was selected')
plt.show()
