from algosdk import mnemonic
from algosdk.v2client.algod import AlgodClient
from operations.util import createFeeTokenAsset, getAlgodClient
from utils.account import Account
from operations.deploy import createAlgolockerApp
from operations.setup import setupAlgolockerApp
from constants import ALGOD_ADDRESS, ALGOD_TOKEN, USER_MNEMONIC

def getAlgodClient() -> AlgodClient:
    return AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    
def deploy():
    client = getAlgodClient()

    print("Preparing user...")
    privateKey = mnemonic.to_private_key(USER_MNEMONIC)
    myAccount = Account(privateKey)

    print("Creating fee token...")
    myFeeAsaId = createFeeTokenAsset(
        client,
        myAccount,
        f"MyToken",
        f"MyAwesomeToken",
        f"https://www.my-awesome-token.org"
    )
    print("myFeeAsaId: ", myFeeAsaId)

    print("Starting to deploy locker app")
    appId = createAlgolockerApp(
        client, 
        myAccount, 
        myFeeAsaId, 
        500*(10**6) # fees * decimals
        )    
    print("AppId: ", appId)

    print("Setting up locker app")
    setupAlgolockerApp(
        client, 
        appId, 
        myAccount, 
        myFeeAsaId
        )
    print("Setup complete")
    
    print("We did it!")

deploy()