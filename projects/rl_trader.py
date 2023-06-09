

import numpy as np
import pandas as pd

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam

from datetime import datetime

import itertools
import argparse
import re
import os
import pickle

from sklearn.preprocessing import StandardScaler

"""## Data"""

#!wget -nc https://raw.githubusercontent.com/lazyprogrammer/machine_learning_examples/master/tf2.0/aapl_msi_sbux.csv

# get_data() function returns T x 3 list of stock prices
def get_data():
    df = pd.read_csv('aapl_msi_sbux.csv')
    return df.values

print(get_data())

"""## Replay Buffer"""

class ReplayBuffer:
#### Constructor function ####
    def __init__(self, obs_dim, act_dim, size): # initialize array buffer and pointers
        # state buffer
        self.obs1_buf = np.zeros([size, obs_dim], dtype=np.float32) #stores state
        self.obs2_buf = np.zeros([size, obs_dim], dtype=np.float32) # stores next state
        # Action buffer
        self.acts_buf = np.zeros(size, dtype = np.uint8) # stores actions (0-26 inclusive), integer value hunxa
        # Reward buffer
        self.rews_buf = np.zeros(size, dtype = np.float32) #stores reward
        # Done buffer
        self.done_buf = np.zeros(size, dtype = np.uint8) #stores done flag (0 or 1)
        
        self.ptr, self.size, self.max_size = 0, 0, size # pointer starts from 0, current buffer size = 0, max_size of buffer = size



#### Store Function ####
    #stores state, action, reward, next_state, done in their respective buffer at the index "self.ptr"
    def store(self, obs, act, rew, next_obs, done):
        self.obs1_buf[self.ptr] = obs
        self.obs2_buf[self.ptr] = next_obs
        self.acts_buf[self.ptr] = act
        self.rews_buf[self.ptr] = rew
        self.done_buf[self.ptr] = done
        self.ptr = (self.ptr + 1) % self.max_size # next pointer in circular buffer
        self.size = min(self.size + 1 , self.max_size)




#### Sample_batch function ####
    def sample_batch(self, batch_size = 32):
        idxs = np.random.randint(0, self.size, size=batch_size) # chooses random indices of length 32(batch_size)
        return dict(s = self.obs1_buf[idxs],
                    s2 = self.obs2_buf[idxs],
                    a = self.acts_buf[idxs],
                    r = self.rews_buf[idxs],
                    d = self.done_buf[idxs])

def get_scaler(env):
    states = []
    for _ in range(env.n_step):
        action = np.random.choice(env.action_space)
        state, reward, done, info = env.step(action)
        states.append(state)
        if done:
          break
    scaler = StandardScaler()
    scaler.fit(states)
    return scaler

def maybe_make_dir(directory): #store trained model and rewards encountered
    if not os.path.exists(directory):
       os.makedirs(directory)

def mlp(input_dim, n_action, n_hidden_layers = 1, hidden_dim= 32):
    # multi layer perceptron

    # input layer
    i = Input(shape=(input_dim,))
    x = i

    # hidden layers
    for _ in range(n_hidden_layers):
        x = Dense(hidden_dim, activation ='relu')(x)
    
    # final layers
    x = Dense(n_action)(x)

    # model 
    model = Model(i,x)
    model.compile(loss='mse', optimizer='adam')
    print((model.summary()))
    return model

"""## Environment

```
3 stock traiding environment
state: vector of size 7 (n_stock * 2 +1)
       - shares of stock 1 owned
       - shares of stock 2 owned
       - shares of stock 3 owned
       - price of stock 1(using daily close price)
       - price of stock 2
       - price of stock 3
       - cash owned (can be used to purchase more stocks)
Action: categoricel variable with 27 possibilities
       - for each stock:
       - 0 = sell
       - 1 = hold 
       - 2 = buy
```
"""

class MultiStockEnv:
      def __init__(self,data, initial_investment = 20000):
          #data
          self.stock_price_history = data
          self.n_step, self.n_stock = self.stock_price_history.shape

          #instance attributes
          self.initial_investment = initial_investment
          self.cur_step = None #current step
          self.stock_owned = None
          self.stock_price = None
          self.cash_in_hand = None

          self.action_space = np.arange(3**self.n_stock) # numpy array from 0 to 26 inclusive
          
          #action permutations
          #returns a nested list with elements like:
          #[0,0,0]===> sell all your stock
          #[0,0,1]===> sell first two stock and hold last one
          #[0,0,2]===> sell first two stock and buy last one
          #etc. (where 0 = sell, 1 = hold, 2 = buy)

          #The map function applies the list constructor to 
          #each tuple generated by itertools.product, converting each tuple of actions into a list of actions.
          self.action_list = list(map(list, itertools.product([0,1,2], repeat=self.n_stock)))

          # calculate size of state
          self.state_dim = self.n_stock * 2 + 1

          self.reset()

      def reset(self):
        self.cur_step = 0 # points to first day of stock price in our dataset
        self.stock_owned = np.zeros(self.n_stock) # array of zeros, wich describes number of stock owned
        self.stock_price = self.stock_price_history[self.cur_step] #tells stock price on the current day
        self.cash_in_hand = self.initial_investment # since we have not bought any stock
        return self._get_obs() # returns state vector
      
      def step(self, action):
        assert action in self.action_space # checks action exists in action space

        # get current value before performing action
        prev_val = self._get_val()

        #update price, i.e, go to next day
        self.cur_step += 1 #next day banako
        self.stock_price = self.stock_price_history[self.cur_step] # price of next day

        #perform trade
        self._trade(action)

        # get new value after taking action
        cur_val = self._get_val()

        # reward is increase in portfolio value
        reward = cur_val - prev_val

        # done if we have run our of data
        done = self.cur_step == self.n_step - 1

        #store current value of the portfolio here
        info = {'cur_val': cur_val}

        # confrom to Gym API
        return self._get_obs(), reward, done, info

      
      def _get_obs(self):#returns state
          obs = np.empty(self.state_dim)
          obs[:self.n_stock] = self.stock_owned # first component is stock we own, (list of size 3)
          obs[self.n_stock:2*self.n_stock] = self.stock_price # second component is value of stock, (list of size 3)
          obs[-1] = self.cash_in_hand#last index
          return obs

      


      def _get_val(self):#returns current value of our portfolio
          return self.stock_owned.dot(self.stock_price) + self.cash_in_hand



      # [2,1,0] ==> buy first stock, hold second stock, and sell third stock
      def _trade(self, action):    
          action_vec = self.action_list[action]

          #determine which stocks to buy or sell
          sell_index = [] #store index of stocks we want to sell
          buy_index = [] #store index of stocks we want to buy
          for i, a in enumerate(action_vec):
            if a == 0:
              sell_index.append(i)#sell
            elif a == 2:
              buy_index.append(i)  # buy

          #sell any stocks we want to sell
          #then any stock we want to buy
          if sell_index:
             #Note: For simplicity we sell all the share of that stock
             for i in sell_index:
                 self.cash_in_hand += self.stock_price[i] * self.stock_owned[i] #sell gareko money + cash in hand
                 self.stock_owned[i]=0 # now we dont have any stock
          if buy_index:
            #Note: when buying, we will loop through each stock we want to buy,
            #      and buy one share at a time until we run out of cash
             can_buy = True
             while can_buy:
                  for i in buy_index:
                     if self.cash_in_hand > self.stock_price[i]: # check if we can buy a stock or not
                        self.stock_owned[i] += 1 # buy one share
                        self.cash_in_hand -= self.stock_price[i] # reduce the amount we bought from cash_in_hand
                     else:
                        can_buy = False

"""## Agent

```
Our Artificial Inteligence.
  => Take Past experience
  => Learn from them
  => Take action such that they will maximize future reward
```
"""

class DQNAgent(object):
     def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = ReplayBuffer(state_size, action_size, size=500)
        self.gamma = 0.95 #discount rate
        self.epsilon = 1.0 # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.model = mlp(state_size, action_size)

     def update_replay_memory(self, state, action, reward, next_state, done):
        self.memory.store(state, action, reward, next_state, done)

     def act(self, state):#it takes a state and use epsilion greedy to "choose action" based on that state
        #random action
        if np.random.rand() <= self.epsilon: # random number betn 0-1 and check if its less than 1
          return np.random.choice(self.action_size)# random action is done
        #greedy action
        act_values = self.model.predict(state)#otherwise we do greedy action by grabbing all Q value  for input state
                                              #then action to perform is action which leads max Q value
        return np.argmax(act_values[0]) #returns action which leads max Q value

     #most important function 
     def replay(self, batch_size=32): # here, batch_size means how many samples to grab from replay memory
        # first check if replay buffer contains enough data
        if self.memory.size < batch_size:
          return #just return otherwise continue

        # sample a batch of data from replay memory
        minibatch = self.memory.sample_batch(batch_size)#returns dict
        states = minibatch['s']
        actions = minibatch['a']
        rewards = minibatch['r']
        next_states = minibatch['s2']
        done = minibatch['d']

        # Calculate the tentative target for each state: Q(s',a)
        target = rewards + self.gamma * np.max(self.model.predict(next_states), axis=1)

        #The value of terminal states is zero
        # so set the target to be reward only
        target[done] = rewards[done] # where the data ends, in real life does data stops??

        #In Keras API, the target(usually) have the same
        #shape as the predictions.
        # However, we only need to update the network for the actions
        # which were actually taken
        #We can accomplish this by setting the target to be equal to
        # the prediction for all values
        #Then, only change the targets for the actions taken.
        #Q(s,a)
        target_full = self.model.predict(states) # input is 1D array of batch_size but model prediction is 2D array of batch_size x n_action
        target_full[np.arange(batch_size), actions] = target #double indexing gareko

        #Run one training step(gradient descent)
        self.model.train_on_batch(states, target_full)

        #update epsilon value to reduce exploration time
        if self.epsilon > self.epsilon_min:
          self.epsilon *= self.epsilon_decay

        #load model weights
        def load(self, name):
          self.model.load_weights(name)

        #save model weights
        def save(self, name):
          self.model.save_weights(name)

"""## Play one episode"""

def play_one_episode(agent, env, is_train):
   # note: after transforming states are already 1xD
   state = env.reset()
   state = scaler.transform([state])
   done = False

   while not done:
      action = agent.act(state) # agent le state liyera next action nikaleko
      next_state, reward, done, info = env.step(action) # env ma one step action gareko
      next_state = scaler.transform([next_state])
      if is_train == 'train':
        agent.update_replay_memory(state,action,reward,next_state,done)#update latest transition
        agent.replay(batch_size)#run one step of gradient descent
      state = next_state 
   return info['cur_val']

if __name__ == '__main__':
  #config
  models_folder = 'rl_trader_models'
  rewards_folder = 'rl_trader_rewards'
  num_episodes = 2000
  batch_size = 32
  initial_investment = 20000
  
  
  #to run the script with command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--mode', type = str, required=True,
                      help='either "train" or "test"')
  args = parser.parse_args()
  


  #create required directory
  maybe_make_dir(models_folder)
  maybe_make_dir(rewards_folder)
  


  #get our time series
  data = get_data()
  n_timesteps, n_stocks = data.shape
  
  #split data into train and test
  n_train = n_timesteps // 2  
  train_data = data[:n_train] #first half
  test_data = data[n_train:]



  #instance of env with training data
  env = MultiStockEnv(train_data, initial_investment)
  #get dimensionality of state and action space
  state_size = env.state_dim
  action_size = len(env.action_space)

  #instance of agent
  agent = DQNAgent(state_size, action_size)

  #instance of scaler 
  scaler = get_scaler(env)

  #store final value of portfolio (end of episode)
  portfolio_value = [] #populate it



  # this will overwrite the things we have created in the case of test mode
  if args.mode == 'test':
    #then load previous scaler(make sure we dont use different scaler)
    with open(f'{models_folder}/scaler.pkl','rb') as f:
      scaler = pickle.load(f)

    #remake env with test data
    env = MultiStockEnv(test_data,initial_investment)

    #make sure epsilon is not 1! (pure exploration)
    # no need to run multiple episodes if epsilon = 0, its deterministic
    agent.epsilon = 0.01

    #load trained weights
    agent.load(f'{models_folder}/dqn.h5')



  # play game num_episodes times
  for e in range(num_episodes):
     t0 = datetime.now()
     val = play_one_episode(agent, env, args.mode)
     dt = datetime.now() - t0
     print(f"episode: {e + 1}/{num_episodes}, episode end value: {val:.2f}, duration: {dt}")
     portfolio_value.append(val) # append episode end portfolio value

  # save the weights when we are done
  if args.mode =='train':
    #save DQN
    agent.save(f'{models_folder}/dqn.h5')

    #save scaler
    with open(f'{models_folder}/scaler.pkl', 'wb') as f:
      pickle.dump(scaler, f)


  #save portfolio value for each episode(both train and test)
  np.shape(f'{rewards_folder}/{args.mode}.npy', portfolio_value)