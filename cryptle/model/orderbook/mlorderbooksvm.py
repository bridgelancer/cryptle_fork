"""
    File name: ml_orderbook_svm.py
    Author: Nick
    Date created: 25/11/2018
    Python Version: 3.6
"""


import pandas as pd
import numpy as np
import orderbook
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from operator import itemgetter
from sklearn.metrics import classification_report, confusion_matrix


df = pd.read_csv('training_set_400.csv', header=None)

# the following is categorical variable for rate comparison
df[132] = df[132].astype('category')
df[133] = df[133].astype('category')
df[134] = df[134].astype('category')
df[135] = df[135].astype('category')

# 135 to 139 all labels
df[136] = df[136].astype('category')  # mid_price
df[137] = df[137].astype('category')  # price_spread
df[138] = df[138].astype('category')  # buy_in
df[139] = df[139].astype('category')  # sell_out

# df[140] is an index entry for debugging

# choose variables to be predicted
IG = mutual_info_classif(df[df.columns[1:136]], df[137])

# take the ones we want, there are better ways to do this
# argmax = list(IG.argsort()[-50:][::-1])
argmin = list(IG.argsort()[1:84][::1])

argmin.extend([136,137,138,139,140])

X = df.drop(df.columns[argmin], axis = 1) # keep top
X = df.drop(df.columns[[136,137,138,139,140]], axis =1)

# y = df[136] # predicting the drift of mid price
y = df[137] # predict drift

y_2 = [0 for i in range(len(y))]  # upward
y_1 = [0 for i in range(len(y))]  # stationary
y_0 = [0 for i in range(len(y))]  # downward

# do back to back ensemble
for i in range(len(y)):
    if y[i] == 2 or y[i] =='2':
        y_0[i] = -1
        y_1[i] = -1
        y_2[i] = 1
    elif y[i] == 1 or y[i] == '1':
        y_0[i] = -1
        y_1[i] = 1
        y_2[i] = -1
    elif y[i] == 0 or y[i] == '0':
        y_0[i] = 1
        y_1[i] = -1
        y_2[i] = -1
    else:
        raise Exception('Label Error')

# prefer scaling to 0,1 or -1,1
# X = preprocessing.scale(X)

X = np.array(X)
y = np.array(y)
y_0 = np.array(y_0)
y_1 = np.array(y_1)
y_2 = np.array(y_2)

X_train, X_test = X[:int(len(X)*0.8)], X[int(len(X)*0.8):]
y_train, y_test = y[:int(len(X)*0.8)], y[int(len(X)*0.8):]
y_train_0, y_test_0 = y_0[:int(len(X)*0.8)], y_0[int(len(X)*0.8):]
y_train_1, y_test_1 = y_1[:int(len(X)*0.8)], y_1[int(len(X)*0.8):]
y_train_2, y_test_2 = y_2[:int(len(X)*0.8)], y_2[int(len(X)*0.8):]

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, shuffle= False)

scale_obj = MinMaxScaler()

X_train = scale_obj.fit_transform(X_train)
X_test = scale_obj.transform(X_test)


# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, shuffle= False)
# X_train_0, X_test_0, y_train_0, y_test_0 = train_test_split(X, y_0, test_size= 0.2, shuffle= False)
# X_train_1, X_test_1, y_train_1, y_test_1 = train_test_split(X, y_1, test_size= 0.2, shuffle= False)
# X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(X, y_2, test_size= 0.2, shuffle= False)


# note that X_train_* has no difference

# one against all
svclassifier_0 = SVC(kernel = 'rbf', gamma='auto').fit(X_train_0, y_train_0)
svclassifier_1 = SVC(kernel = 'rbf', gamma='auto').fit(X_train_1, y_train_1)
# svclassifier_2 = SVC(kernel = 'rbf', gamma='auto').fit(X_train_2, y_train_2)

# %%timeit

# prediction step
set_0  = svclassifier_0.decision_function(X_test_0)
set_1  = svclassifier_1.decision_function(X_test_1)
# set_2  = svclassifier_2.decision_function(X_test_2)



z = [0 for i in range(len(X_test_1))]

for i in range(len(X_test_1)):

    # can remove the set in enumerate if we want to classify less class
    index, value = max(enumerate([set_0[i], set_1[i]]), key=itemgetter(1))

    # careful it's tricky here that we use the position in the above set to index
    z[i] = index

y_test = list(y_test)
for i in range(len(y_test)):
    y_test[i] = int(y_test[i])

print(confusion_matrix(y_test, z))
print(classification_report(y_test, z))


from pickle import dumps, loads

# pickle to string
s0 = pickle.dumps(svclassifier_0)
s1 = pickle.dumps(svclassifier_1)
s2 = pickle.dumps(svclassifier_2)

ss = pickle.dumps(scale_obj)

# loading and after loading
objects = pickle.loads(ss)
test = objects.transform(test)

obj2 = pickle.loads(s2)
obj1 = pickle.loads(s1)
obj0 = pickle.loads(s0)

pred = max(obj2.decision_funcion(test)[0], obj1.decision_funcion(test)[0], obj0.decision_funcion(test)[0])

from joblib import dump, load

# can only dump to disk but faster
dump(svclassifier_0, 'filename.joblib')
s0 = load('filename.joblib')
