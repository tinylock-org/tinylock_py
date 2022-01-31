from algosdk import mnemonic
from algosdk.v2client.algod import AlgodClient
from tinylocker.operations.util import createFeeTokenAsset
from tinylocker.utils.account import Account
from tinylocker.operations.deploy import createAlgolockerApp
from tinylocker.operations.setup import setupAlgolockerApp
from constants import ALGOD_ADDRESS, ALGOD_TOKEN, USER_MNEMONIC, TINYLOCK_ASA, TINYLOCK_APP

def getAlgodClient() -> AlgodClient:
    return AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, headers={'User-Agent': 'Client'})
    
def deploy():
    client = getAlgodClient()

    print("Preparing user...")
    privateKey = mnemonic.to_private_key(USER_MNEMONIC)
    myAccount = Account(privateKey)

    print("Creating fee token...")
    myFeeAsaId = createFeeTokenAsset(
        client=client,
        account=myAccount,
        unit_name=f"MyCoin",
        asset_name=f"MC",
        url=f"https://www.mc.mc",
        decimals=6,
        amount=10**9,
        note="mc"
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

# deploy()

from tinylocker.operations.util import sendTokens
from algosdk.future.transaction import AssetCreateTxn, AssetOptInTxn, AssetTransferTxn
from tinylocker.utils.transaction import waitForTransaction

def sendTokens(
    client: AlgodClient,
    funder: Account,
    receiver: str,
    asa_id: int,
    amount: int
):

    suggested_params = client.suggested_params()

    transaction = AssetTransferTxn(
        sender=funder.getAddress(),
        sp=suggested_params,
        receiver=receiver,
        amt=amount,
        index=asa_id
    )
    signedTransaction = transaction.sign(funder.getPrivateKey())
    client.send_transactions([signedTransaction])
    waitForTransaction(client, signedTransaction.get_txid())

def do():
    client = getAlgodClient()

    print("Preparing user...")
    privateKey = mnemonic.to_private_key(USER_MNEMONIC)
    myAccount = Account(privateKey)

    sendTokens(
        client=client,
        funder=myAccount,
        receiver="MRCSZWNEI7FXH5VCYVCEVFUHIL6WXFMDUR4HRX4SAXCQCKUYMELAMOCDAQ",
        asa_id=TINYLOCK_ASA,
        amount=95000*10**6
    )
    
do()