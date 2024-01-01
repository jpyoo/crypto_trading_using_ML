# crypto_trading_using_ML

## Predict Bitcoin price using Machine learning models

This project utilizes multiple Keras training models to predict Bitcoin prices, providing estimates for the next ten minutes of price movements. The actual data used for model training is not included due to file size constraints. The models were trained using 2020 Bitcoin price data and tested with 2021 data.

After training the models, you can use `live_test_model.ipynb` to test with live data or apply the models to live data.

## Result

### Observed Price Moves for 10 Minutes
![expected](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/e1ba59d9-673b-4233-8842-a0176a205759)

### Model Predictions for the Next 10 Minutes
#### Model 1, 2, 3
![model 1,2,3](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/3591dffc-fb9b-4595-973b-a242aa98bba3)

#### Model 4, 5
![model 4,5](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/63964cc8-3a07-4b47-9fa3-6bd76374a4ee)

### Different Time Predictions
1. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/1a972a15-3e29-4713-acdc-a0300f6ba35e)

2. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/63a917ac-2610-4fef-a7ba-0b1864f771cd)

3. ![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/8a717fdf-4590-4a86-845d-eca9a363a561)

### Trading Results Using Best Models (GRU and LSTM)
![image](https://github.com/jpyoo/crypto_trading_using_ML/assets/58375171/4d9b9438-2341-41ab-9a20-c55e446e565d)
