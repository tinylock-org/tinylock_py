from algosdk.future.transaction import ApplicationNoOpTxn, AssetTransferTxn, LogicSig, PaymentTxn
from algosdk.v2client.algod import AlgodClient

from ..utils.account import Account
from tinyman.utils import TransactionGroup

def unlockToken(client: AlgodClient, signature: LogicSig, appID: int, sender: Account, amount: int, lock_token: int) : #-> None
    signature_address = signature.address()

    suggested_params = client.suggested_params()

    transactions = [
        PaymentTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=signature_address,
            amt=2000
        ),
        ApplicationNoOpTxn(
            sender=signature_address,
            sp=suggested_params,
            index=appID,
            app_args=['unlock']
        ),
        AssetTransferTxn(
            sender=signature_address,
            sp=suggested_params,
            receiver=sender.getAddress(),
            amt=amount,
            index=lock_token
        )
    ]

    transaction_group = TransactionGroup(transactions)
    transaction_group.sign_with_logicisg(signature)
    transaction_group.sign_with_private_key(sender.getAddress(), sender.getPrivateKey())

    transaction_group.submit(client, True)