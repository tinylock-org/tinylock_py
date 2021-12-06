# Setup

This project depends mainly on AlgoSDK and TinymanSDK.
You can see the python dependencies in requirements.txt.

If you are not using this within the Algorand sandbox environment, I would recommend to create a virtual environment
```
python3 -m venv ./venv
source venv/bin/activate
```

TinymanSDK isn't available via PIP, so we need to install it manually.
```
pip install wheel
pip install git+https://github.com/tinymanorg/tinyman-py-sdk.git
```

Same for tinylock_py:
```
pip install git+https://github.com/tinylock-org/tinylock_py.git
```

# SDK

The SDK comes with all the operations possible on the smart contract. There are also some helper functions which come in handy if you deploy your own contract. Some of those helpers are from the Algorand Examples.

A deploy script is included, which could be a help for some.

# Client

The Client is a python console script which supports 3 operations:
1) Locking

The following operation locks 10 tinylock_testnet2 until the specified date in unix format.
Where 
10 = amount, 
1638288000 = unix date, 
47355102 = lock asa

```
python3 client.py testnet lock 10 1638288000 47355102
```
Note: Be aware that the amount includes the decimals for this coin. In this case it would be equal to 10 * 10^-6 since the tinylock token has decimals of 6.

If you want to lock a pool token but are not able to find it's asa you can also specify a 4th argument to let the client find it for you.
Where 
10 = amount, 
1638288000 = unix date, 
47355102 = lock asa, 
0 = lock asa2
```
python3 client.py testnet lock 10 1638288000 47355102 0
```

Note: 0 is Algo

2) Relocking

This function is automatically called if the smart signature (the locking contract) has locked the token once before. The only condition is that the date time must be higher than the first lock IF it still has a active lock going

```
python3 client.py testnet lock 10 1638288001 47355102
```

3) Unlocking

This function will only pass if the smart signature holds at least the specified amount and the current time is less or equal the lock date

Where 47355102 = your asa, 10 = amount

```
python3 client.py testnet unlock 47355102 10 
```


# Configuration
The client is mainly used to unlock your tokens in case of a operational failure of the website.
This means the focus wasn't to use this as a sdk tool. That doesn't mean you couldn't modify it though.

constants.py holds all the configurations available. In order for it to be functional, you need to provide your USER_MNEMONIC in the constants.py file.
Please make sure to never share this with anyone. Also please double check, when pushing to this repository in case you are contributing.

Thanks
