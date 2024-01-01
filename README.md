# crypto_trading_using_ML

## Predict Bitcoin price using Machine learning models

This project utilizes multiple Keras training models to predict Bitcoin prices, providing estimates for the next ten minutes of price movements. The actual data used for model training is not included due to file size constraints. The models were trained using 2020 Bitcoin price data and tested with 2021 data.

After training the models, you can use `live_test_model.ipynb` to test with live data or apply the models to live data.

## Result

### Observed Price Moves for 10 Minutes
![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/expected.PNG?raw=true "Expected values")

### Model Predictions for the Next 10 Minutes
#### Model 1, 2, 3
![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/model%201%2C2%2C3.PNG?raw=true "Expected values")

#### Model 4, 5
![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/model%204%2C5.PNG?raw=true "Expected values")

### Different Time Predictions
1. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/1a972a15-3e29-4713-acdc-a0300f6ba35e)

2. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/63a917ac-2610-4fef-a7ba-0b1864f771cd)

3. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/8a717fdf-4590-4a86-845d-eca9a363a561)

### Trading Results Using Best Models (GRU and LSTM)
![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/4d9b9438-2341-41ab-9a20-c55e446e565d)
