# -*- coding: utf-8 -*-
"""6050735TimeSeries.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MKk7ioGCzRtBJ-9qWPLjv6fdSayyhRZ9
"""

import pandas as pd
from datetime import datetime

df = pd.read_excel('Material.xlsx')

df.head()

df.CALMONTH = df.CALMONTH.astype(str)

df.CALMONTH = df.CALMONTH.apply(lambda x: datetime.strptime(x,'%Y%m'))

df.info()

df.head()

df = df.set_index("CALMONTH")

df.head()

df.index.freq = 'MS'

# Commented out IPython magic to ensure Python compatibility.
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
# %matplotlib inline

plt.figure(figsize=(18,9))
plt.plot(df.index, df.DELIVERY_QTY, linestyle="-")
plt.xlabel=('Dates')
plt.ylabel=('Delivery Qty')
plt.show();

from statsmodels.tsa.seasonal import seasonal_decompose

a = seasonal_decompose(df.DELIVERY_QTY, model = "add")
a.plot();

import matplotlib.pyplot as plt
plt.figure(figsize = (16,7))
a.seasonal.plot();

from pmdarima.arima import auto_arima

#pip install pmdarima

auto_arima(df.DELIVERY_QTY, seasonal=True, m=12,max_p=7, max_d=5,max_q=7, max_P=4, max_D=4,max_Q=4).summary()

train_data = df[:len(df)-12]
test_data = df[len(df)-12:]

from statsmodels.tsa.statespace.sarimax import SARIMAX

arima_model = SARIMAX(train_data.DELIVERY_QTY, order = (0,0,2), seasonal_order = (0,0,2,12))
arima_result = arima_model.fit()
arima_result.summary()

arima_pred = arima_result.predict(start = len(train_data), end = len(df)-1, typ="levels").rename("ARIMA Predictions")
arima_pred

test_data.DELIVERY_QTY.plot(figsize = (16,5), legend=True)
arima_pred.plot(legend = True);

from statsmodels.graphics.tsaplots import plot_acf,plot_pacf 
from sklearn.metrics import mean_squared_error
from statsmodels.tools.eval_measures import rmse

arima_rmse_error = rmse(test_data.DELIVERY_QTY, arima_pred)
arima_mse_error = arima_rmse_error**2
mean_value = df.DELIVERY_QTY.mean()

print(f'MSE Error: {arima_mse_error}\nRMSE Error: {arima_rmse_error}\nMean: {mean_value}')

test_data['ARIMA_Predictions'] = arima_pred

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

scaler.fit(train_data)
scaled_train_data = scaler.transform(train_data)
scaled_test_data = scaler.transform(test_data)

from keras.preprocessing.sequence import TimeseriesGenerator

n_input = 12
n_features= 1
generator = TimeseriesGenerator(scaled_train_data, scaled_train_data, length=n_input, batch_size=1)

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

lstm_model = Sequential()
lstm_model.add(LSTM(200, activation='relu', input_shape=(n_input, n_features)))
lstm_model.add(Dense(1))
lstm_model.compile(optimizer='adam', loss='mse')

lstm_model.summary()

lstm_model.fit_generator(generator,epochs=40)

import numpy as np

losses_lstm = lstm_model.history.history['loss']
plt.figure(figsize=(12,4))
plt.xticks(np.arange(0,21,1))
plt.plot(range(len(losses_lstm)),losses_lstm);

lstm_predictions_scaled = list()

batch = scaled_train_data[-n_input:]
current_batch = batch.reshape((1, n_input, n_features))

for i in range(len(test_data)):   
    lstm_pred = lstm_model.predict(current_batch)[0]
    lstm_predictions_scaled.append(lstm_pred) 
    current_batch = np.append(current_batch[:,1:,:],[[lstm_pred]],axis=1)

lstm_predictions_scaled

lstm_predictions = scaler.inverse_transform(lstm_predictions_scaled)

lstm_predictions

test_data['LSTM_Predictions'] = lstm_predictions

test_data

test_data.DELIVERY_QTY.plot(figsize = (16,5), legend=True)
test_data['LSTM_Predictions'].plot(legend = True);

lstm_rmse_error = rmse(test_data.DELIVERY_QTY, test_data["LSTM_Predictions"])
lstm_mse_error = lstm_rmse_error**2
mean_value = df.DELIVERY_QTY.mean()

print(f'MSE Error: {lstm_mse_error}\nRMSE Error: {lstm_rmse_error}\nMean: {mean_value}')

df_pr = df.copy()
df_pr = df.reset_index()

df_pr.columns = ['ds','y']

train_data_pr = df_pr.iloc[:len(df)-12]
test_data_pr = df_pr.iloc[len(df)-12:]

from fbprophet import Prophet

m = Prophet()
m.fit(train_data_pr)
future = m.make_future_dataframe(periods=12,freq='MS')
prophet_pred = m.predict(future)

prophet_pred.tail()

prophet_pred = pd.DataFrame({"Date" : prophet_pred[-12:]['ds'], "Pred" : prophet_pred[-12:]["yhat"]})

prophet_pred = prophet_pred.set_index("Date")

prophet_pred.index.freq = "MS"

prophet_pred

test_data["Prophet_Predictions"] = prophet_pred['Pred'].values

import seaborn as sns

plt.figure(figsize=(16,5))
ax = sns.lineplot(x= test_data.index, y=test_data.DELIVERY_QTY)
sns.lineplot(x=test_data.index, y = test_data["Prophet_Predictions"]);

prophet_rmse_error = rmse(test_data.DELIVERY_QTY, test_data["Prophet_Predictions"])
prophet_mse_error = prophet_rmse_error**2
mean_value = df.DELIVERY_QTY.mean()

print(f'MSE Error: {prophet_mse_error}\nRMSE Error: {prophet_rmse_error}\nMean: {mean_value}')

rmse_errors = [arima_rmse_error, lstm_rmse_error, prophet_rmse_error]
mse_errors = [arima_mse_error, lstm_mse_error, prophet_mse_error]
errors = pd.DataFrame({"Models" : ["ARIMA", "LSTM", "Prophet"],"RMSE Errors" : rmse_errors, "MSE Errors" : mse_errors})

plt.figure(figsize=(16,9))
plt.plot_date(test_data.index, test_data.DELIVERY_QTY, linestyle="-")
plt.plot_date(test_data.index, test_data["ARIMA_Predictions"], linestyle="-.")
plt.plot_date(test_data.index, test_data["LSTM_Predictions"], linestyle="--")
plt.plot_date(test_data.index, test_data["Prophet_Predictions"], linestyle=":")
plt.legend()
plt.show()

print(f"Mean: {test_data.DELIVERY_QTY.mean()}")
errors

test_data
