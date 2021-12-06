from algosdk.future.transaction import ApplicationNoOpTxn, AssetTransferTxn, LogicSig, PaymentTxn
from algosdk.logic import get_application_address
from algosdk.v2client.algod import AlgodClient

from utils.account import Account
from tinyman.utils import TransactionGroup


def relockToken(client: AlgodClient, signature: LogicSig, appID: int, sender: Account, amount: int, user_asa_id: int, tinylock_asa_id:int, time: int, fee: int) : #-> None
    appAddr = get_application_address(appID)
    signature_address = signature.address()

    print("Relocking token")

    suggested_params = client.suggested_params()

    transactions = [
        PaymentTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=signature_address,
            amt=1000,
            note='txs fee'
        ),
        AssetTransferTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=appAddr,
            amt=fee,
            note=user_asa_id.to_bytes(8, "big"), # In relock it's not really necessary since the WebApp searches for locks and filters balances. It doesn't care about the specific relock operation.
            index=tinylock_asa_id
        ),
        AssetTransferTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=signature_address,
            amt=amount,
            index=user_asa_id
        ),
        ApplicationNoOpTxn(
            sender=signature_address,
            sp=suggested_params,
            index=appID,
            app_args=['relock', time.to_bytes(8, "big")],
            accounts=[sender.getAddress()],
            foreign_assets=[tinylock_asa_id]
        ),
    ]

    transaction_group = TransactionGroup(transactions)
    transaction_group.sign_with_logicisg(signature)
    transaction_group.sign_with_private_key(sender.getAddress(), sender.getPrivateKey())

    transaction_group.submit(client, True)