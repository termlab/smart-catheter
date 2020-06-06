import random

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d


def save_data(records, folder):
    for idx, record in enumerate(records):
        np.savetxt(f'data/preprocess/{folder}/{idx + 1}.csv', record, delimiter=',')


random.seed(1)
record_count = 54
ban_list = [11, 18, 19, 28, 32, 36, 37, 38, 40, 45, 48]
data_list = []
refs = [1539.7249357906976, 1539.7461374651164, 1539.5011418372094]

for i in range(1, record_count + 1):
    if i in ban_list:
        continue
    x_data = pd.read_csv(f'data/raw/input/{i}.csv', index_col=0, header=None,
                         names=['timestamp', 'sensor1', 'sensor2', 'sensor3'], parse_dates=['timestamp'])
    y_data = pd.read_csv(f'data/raw/output/{i}.csv', index_col=0, header=None, names=['timestamp', 'weight'],
                         parse_dates=['timestamp'], dtype={'weight': float})

    x_data, y_data = x_data.dropna().reset_index(drop=True), y_data.dropna().reset_index(drop=True)
    x_data = x_data[x_data['sensor3'] > 1538]
    for idx in range(3):
        x_data[f'sensor{idx + 1}'] -= refs[idx]

    raw_data = pd.merge_asof(y_data, x_data, on='timestamp', direction='nearest', tolerance=pd.Timedelta('5ms'))
    raw_data = raw_data.dropna().reset_index(drop=True)
    raw_data['timestamp'] = raw_data['timestamp'] - raw_data.at[0, 'timestamp']
    raw_data['timedelta'] = raw_data['timestamp'].dt.total_seconds()

    raw_data = raw_data.drop(['timestamp'], axis=1)
    data = raw_data.to_numpy()

    data = gaussian_filter1d(data, axis=0, sigma=1)
    cs = CubicSpline(data[:, 4], data[:, [0, 1, 2, 3]])
    xrange = np.arange(0, data[-1, 4], 0.01)
    data = cs(xrange)

    data_list.append(data)
    print(f'Record #{i} finished preprocess')

random.shuffle(data_list)
total_cnt = len(data_list)
train_cnt = int(total_cnt * 0.9)
validation_cnt = int(train_cnt * 0.2)

train_data = data_list[0:(train_cnt - validation_cnt)]
validation_data = data_list[(train_cnt - validation_cnt):train_cnt]
test_data = data_list[train_cnt:]

save_data(train_data, 'train')
save_data(validation_data, 'validation')
save_data(test_data, 'test')
