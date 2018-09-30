import keras
import numpy as np
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as sp
import operator

import math
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.layers import Dense, Dropout, Activation, Flatten
from pandas import DataFrame
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM


def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
        # the following is label
        if dataset[i+look_back] >= dataset[i+look_back-1]:
            dataY.append(1)
        else:
            dataY.append(0)
    return np.array(dataX), np.array(dataY)


# load the dataset
dataframe = pd.read_csv('bch.candle.15min.csv', usecols=[1])
dataframe = dataframe[3800:4500]

dataset = dataframe.values
dataset = dataset.astype('float32')

# normalize the dataset
scaler = MinMaxScaler(feature_range=(0, 1))   # this is look back bias

train_size = int(len(dataset) * 0.8)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]

look_back = 5
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)


# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], 1))
testX = np.reshape(testX, (testX.shape[0], testX.shape[1], 1))


# create and fit the LSTM network
batch_size = 1
model = Sequential()
model.add(LSTM(30, batch_input_shape=(batch_size, look_back, 1), stateful=True, return_sequences=True))
# model.add(Dropout(0.3))
model.add(LSTM(30, batch_input_shape=(batch_size, look_back, 1), stateful=True))
model.add(Dense(1, activation="sigmoid"))
model.compile(loss='binary_crossentropy', optimizer='adam')
for i in range(500):
    model.fit(trainX, trainY, epochs=1, batch_size=batch_size, verbose=2, shuffle=False)
    model.reset_states()


# make predictions
trainPredict = model.predict(trainX, batch_size=batch_size)
model.reset_states()
testPredict = model.predict(testX, batch_size=batch_size)


tp = []
for x in testPredict:
    if x >= 0.5:
        tp.append(1)
    else:
        tp.append(0)


sum((tp == testY) & (testY==0)) /  (len(tp) - sum(tp))

sum((tp == testY) & testY) / sum(tp)
