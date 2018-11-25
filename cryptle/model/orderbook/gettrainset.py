import pandas as pd
import numpy as np
import datetime
import json
import orderbook
import multiprocessing as mp



with open('orderdiff/eth.log') as f:
    ds = [json.loads(line) for line in f.readlines()]

diffs = pd.DataFrame(ds)
del ds


with open('orderbook/eth.json') as f:
    ob = [json.loads(line) for line in f.readlines()]


diffs['datetime']   = diffs['datetime'].map(int)
diffs['order_type'] = diffs['order_type'].map({0: 'bid', 1: 'ask'})
diffs.drop(['id'], axis=1, inplace=True)



depth = 10
period     = 60
df = pd.DataFrame()
list_of_lists = []

def event_count(diffs):
    return {
        'create_ask': len(diffs[(diffs['diff_type'] == 'create') & (diffs['order_type'] == 'ask')]),
        'take_ask':   len(diffs[(diffs['diff_type'] == 'change') & (diffs['order_type'] == 'ask')]),
        'delete_ask': len(diffs[(diffs['diff_type'] == 'delete') & (diffs['order_type'] == 'ask')]),
        'create_bid': len(diffs[(diffs['diff_type'] == 'create') & (diffs['order_type'] == 'bid')]),
        'take_bid':   len(diffs[(diffs['diff_type'] == 'change') & (diffs['order_type'] == 'bid')]),
        'delete_bid': len(diffs[(diffs['diff_type'] == 'delete') & (diffs['order_type'] == 'bid')]),
    }

def event_count_1(diffs):
    return len(diffs[(diffs['diff_type'] == 'create') & (diffs['order_type'] == 'ask')]), len(diffs[(diffs['diff_type'] == 'create') & (diffs['order_type'] == 'bid')]), len(diffs[(diffs['diff_type'] == 'change') & (diffs['order_type'] == 'ask')]), len(diffs[(diffs['diff_type'] == 'change') & (diffs['order_type'] == 'bid')]), len(diffs[(diffs['diff_type'] == 'delete') & (diffs['order_type'] == 'ask')]), len(diffs[(diffs['diff_type'] == 'delete') & (diffs['order_type'] == 'bid')])


def order_gradient(book, diffs):
    """Compute orderbook gradient after applying diffs.

    Todo: Improve performance with numpy arrays
    Todo: Make this functional
    """

    t = diffs.time
    bid_price_grad  = [0 for i in range(depth)]
    ask_price_grad  = [0 for i in range(depth)]
    bid_volume_grad = [0 for i in range(depth)]
    ask_volume_grad = [0 for i in range(depth)]


    for time in t.unique():
        # @Refactor: can just multiple by sum(t==time) in grad calculation
        tdiff = 1 / sum(t == time)


        for i, diff in diffs[t == time].iterrows():

            try:

                start_bid_price  = book.bids(depth)
                start_ask_price  = book.asks(depth)
                start_bid_volume = book.bid_volume(depth)
                start_ask_volume = book.ask_volume(depth)

                book.apply_diff(**{**diff, 'time': time+tdiff*i})

                end_bid_price    = book.bids(depth)
                end_ask_price    = book.asks(depth)
                end_bid_volume   = book.bid_volume(depth)
                end_ask_volume   = book.ask_volume(depth)

                for i in range(depth):
                    bid_price_grad[i]  += (end_bid_price[i] - start_bid_price[i]) / tdiff
                    ask_price_grad[i]  += (end_ask_price[i] - start_ask_price[i]) / tdiff
                    bid_volume_grad[i] += (end_bid_volume[i] - start_bid_volume[i]) / tdiff
                    ask_volume_grad[i] += (end_ask_volume[i] - start_ask_volume[i]) / tdiff

            except ValueError:
                pass

    return bid_price_grad, ask_price_grad, bid_volume_grad, ask_volume_grad



def get_snap_shot(j, labeling):
    """Returns a list of lists containing features using orderbook and orderdiff

    Note
    ----
    The function is not idempotent towards the orderbook object.

    Parameters
    ----------
    j
        Chooses the j instance in the orderbook snapshot.
    labeling
        Chooses the state we want to predict after such number of orderbook events.

    Returns
    -------
    A list of lists
        As the function runs, errors are thrown when there are inconsistency in data.
    """



    snap = ob[j]
    book = orderbook.Orderbook.fromstring(asks=snap['asks'], bids=snap['bids'])
    book.time = int(snap['timestamp'])

    start_time = int(datetime.datetime.strftime(book.time,'%s'))

    colume_names = {'datetime': 'time', 'type': 'diff_type'}

    # For gradient generation
    diffs_0 = diffs[(diffs.datetime >= start_time) & (diffs.datetime < start_time + period)]
#     diffs_0 = diffs_0.sort_values(by='datetime')
    diffs_0 = diffs_0.rename(columns=colume_names)
    diffs_0 = diffs_0.sort_index().sort_values(by='time', kind='mergesort')


    # For labeling, take next number of labeling events
    diffs_1 = diffs[diffs.datetime >= start_time + period]
    diffs_1 = diffs_1.rename(columns=colume_names)
    diffs_1 = diffs_1.sort_index().sort_values(by='time', kind='mergesort')

    diffs_1 = diffs_1.head(labeling) # here


    # k = 0
    # minis = list(diffs_1['time'])[-1] - start_time
    # while k <= minis:
    #     k += 1

    # for regime change detection
    diffs_2 = diffs[(diffs.datetime >= start_time - 2*period) & (diffs.datetime < start_time + period)]
#     diffs_2 = diffs_2.sort_values(by='datetime')
    diffs_2 = diffs_2.rename(columns = colume_names)
    diffs_2 = diffs_2.sort_index().sort_values(by='time', kind='mergesort')


    # for getting the next datapoint here every 20 mins
    # diffs_next = diffs[(diffs.datetime >= start_time + period) & (diffs.datetime < start_time + period*np.ceil(k/60))]
    # diffs_next = diffs_next.rename(columns = colume_names)
    # diffs_next = diffs_next.sort_index().sort_values(by='time', kind='mergesort')
    # diffs_next = diffs_next[labeling:]

    # print('how many min:', k/60)

    current_bid = book.bids(1)
    current_ask = book.asks(1)

    v_7 = event_count_1(diffs_0)
    v_7 = list(v_7)

    j_1 = [str(a) for a in book.asks(10)]
    j_2 = [str(a) for a in book.ask_volume(10)]
    j_4 = [str(a) for a in book.bids(10)]
    j_5 = [str(a) for a in book.bid_volume(10)]

    j_3 = zip(j_1, j_2, j_4, j_5)
    j_3 = list(j_3)

    v_1 = []
    for x in j_3:
        v_1 += x

    for x in range(len(v_1)):
        v_1[x] = float(v_1[x])

    v_2 = []
    for k in range(10):
        v_2.append(float(v_1[4*k]) - float(v_1[4*k+2]))
        v_2.append((float(v_1[4*k]) + float(v_1[4*k+2]))/2)

    v_31 = []
    v_31.append(v_1[-4] - v_1[0])
    v_31.append(v_1[2] - v_1[-2])

    v_32 = []
    for x in range(9):
        v_32.append(abs(v_1[4*(x+1)] - v_1[4*x]))
        v_32.append(abs(v_1[4*(x+1) + 2] - v_1[4*x +2]))

    v_4 = [sum(x for i, x in enumerate(v_1) if i % 4 == n)/10 for n in [0,2,1,3]]

    v_5 = []
    v_5.append((v_4[0]- v_4[1])*10)
    v_5.append((v_4[2]- v_4[3])*10)

    temp = []
    for x in event_count_1(diffs_2):
        temp.append(x/5)

    v_8 = [0 for i in range(len(temp)-2)]
    for i in range(len(temp)-2):
        if list(v_7)[i] > temp[i]:
            v_8[i] = 1
        else:
            v_8[i] = 0

    v_6 = order_gradient(book, diffs_0)

    test = []
    for x in (v_6):
        for y in x:
            test.append(y)
    v_6 = test


    for i, diff in diffs_1.iterrows():
        try:
            book.apply_diff(**diff)
        except ValueError:
            print('error in label %s' %j)
            pass

    future_bid = book.bids(1)
    future_ask = book.asks(1)

    # 2 be up, 1 be stationary, 0 be down

    if (current_ask[0] + current_bid[0])/2 > (future_bid[0] + future_ask[0])/2:
        mid_price = '0'
    elif (current_ask[0] + current_bid[0])/2 < (future_bid[0] + future_ask[0])/2:
        mid_price = '2'
    else:
        mid_price = '1'

    if future_bid[0] > current_ask[0]:
        price_spread = '2'
    elif future_ask[0] < current_bid[0]:
        price_spread = '1'
    else:
        price_spread = '0'

    if future_ask[0] <= current_ask[0]:
        buy_in = '1'
    else:
        buy_in = '0'

    if future_bid[0] >= current_bid[0]:
        sell_out = '1'
    else:
        sell_out = '0'

    v = v_1 + v_2 + v_31 + v_32 + v_4 + v_5 + v_6 + v_7 + v_8 + [mid_price] + [price_spread] + [buy_in] + [sell_out] + [j]

    return v

    # for i, diff in diffs_next.iterrows():
    #     try:
    #         book.apply_diff(**diff)
    #     except ValueError:
    #         pass



pool = mp.Pool(processes = 6)

# This means that we are getting 400 datapoints where we are predicting the coming labels
results = [pool.apply_async(get_snap_shot, args = (j,5*60*13)) for j in range(400)]
output = [p.get() for p in results]

col = [i for i in range(len(output[0]))]
df = pd.DataFrame(output, columns=col)
df.to_csv('training_set_400.csv', header=None, index=None)
