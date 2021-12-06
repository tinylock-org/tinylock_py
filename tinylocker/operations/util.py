from algosdk.future.transaction import AssetCreateTxn, AssetOptInTxn, AssetTransferTxn
from algosdk.v2client.algod import AlgodClient

from utils.account import Account
from utils.transaction import waitForTransaction

def optinToken(
    client: AlgodClient,
    sender: Account,
    asa_id: int
):

    suggested_params = client.suggested_params()

    transaction = AssetOptInTxn(
        sender=sender.getAddress(),
        sp=suggested_params,
        index=asa_id
    )

    signedTransaction = transaction.sign(sender.getPrivateKey())
    client.send_transactions([signedTransaction])
    waitForTransaction(client, signedTransaction.get_txid())

def sendTokens(
    client: AlgodClient,
    funder: Account,
    receiver: Account,
    asa_id: int,
    amount: int
):

    suggested_params = client.suggested_params()

    transaction = AssetTransferTxn(
        sender=funder.getAddress(),
        sp=suggested_params,
        receiver=receiver.getAddress(),
        amt=amount,
        index=asa_id
    )
    signedTransaction = transaction.sign(funder.getPrivateKey())
    client.send_transactions([signedTransaction])
    waitForTransaction(client, signedTransaction.get_txid())

def createFeeTokenAsset(
    client: AlgodClient, 
    account: Account = None,
    unit_name = f"MyToken",
    asset_name = f"MyTokenName",
    url = f"MyUrl"
    ) -> int:

    decimals = 6
    total =1*(10**9)*(10**decimals)

    txn = AssetCreateTxn(
        sender=account.getAddress(),
        total=total,
        decimals=decimals,
        default_frozen=False,
        manager=account.getAddress(),
        reserve="",
        freeze="",
        clawback="",
        unit_name=unit_name,
        asset_name=asset_name,
        url=url,
        sp=client.suggested_params(),
    )
    signedTxn = txn.sign(account.getPrivateKey())

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    assert response.assetIndex is not None and response.assetIndex > 0
    return response.assetIndex
