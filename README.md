# crypto_trading_using_ML
# Predict Bitcoin price using Machine learning models
This project uses multiple keras training models to train bitcoin price to provide the next or the next ten minutes of price moves.
The actual data I used to train models are not included because of the file size issue.
Used 2020 bitcoin price data to train models and tested with 2021 data.

After training models, use live_test_model.ipynb to test with live data or use models with live data.

## Result
This graph shows the observed price moves for 10 minutes.
![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/expected.PNG?raw=true "Expected values")

Graphes below show how are the trained models are expecting the price to move for the next 10 minutes, without knowing the result.

![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/model%201%2C2%2C3.PNG?raw=true "Expected values")
![Y_Test](https://github.com/jpyoo/bitcoin-price-models/blob/main/model%204%2C5.PNG?raw=true "Expected values")

