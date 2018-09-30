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
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger

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
dataframe = pd.read_csv('bch.candle.30mins.log', usecols=[1])

dataset = dataframe.values
dataset = dataset.astype('float32')

# normalize the dataset
scaler = MinMaxScaler(feature_range=(0, 1))   # this is look back bias

train_size = int(len(dataset) * 0.8)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]

train = scaler.fit_transform(train)
test = scaler.transform(test)

look_back = 1
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], 1))
testX = np.reshape(testX, (testX.shape[0], testX.shape[1], 1))


# create and fit the LSTM network
batch_size = 1

checkpointer = ModelCheckpoint(monitor='loss', filepath="weights.hdf5", verbose=1, save_best_only=True)

model = Sequential()
model.add(LSTM(30, batch_input_shape=(batch_size, look_back, 1), stateful=True, return_sequences=True))
# model.add(Dropout(0.3))
model.add(LSTM(30, batch_input_shape=(batch_size, look_back, 1), stateful=True))
model.add(Dense(1, activation="sigmoid"))
model.compile(loss='binary_crossentropy', optimizer='adam')
for i in range(50):
    model.fit(trainX, trainY, epochs=1, batch_size=batch_size, verbose=2, shuffle=False, callbacks=[checkpointer])
    model.reset_states()


model.load_weights("weights.hdf5")

# make predictions
trainPredict = model.predict(trainX, batch_size=batch_size)
model.reset_states()
print(testX)
testPredict = model.predict(testX, batch_size=batch_size)


tp = []
# tp is the predicted direction
for x in testPredict:
    if x >= 0.5:
        tp.append(1)
    else:
        tp.append(0)

print("TP:{}".format(tp))
print("testY:{}".format(testY))

print(sum((tp == testY) & (testY==0)) /  (len(tp) - sum(tp))) # len(tp) = total predict, sum(tp) = # predict true
print(sum((tp == testY) & testY) / sum(tp))
