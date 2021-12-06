

from algosdk.future.transaction import ApplicationNoOpTxn
from algosdk.v2client.algod import AlgodClient
from tinyman.utils import TransactionGroup
from utils.account import Account


def changeAlgolockerFee(
    client: AlgodClient,
    appID: int,
    funder: Account,
    fee: int
) : #-> None
    suggestedParams = client.suggested_params()

    transactions = [
        ApplicationNoOpTxn(
            sender=funder.getAddress(),
            sp=suggestedParams,
            index=appID,
            app_args=['update', fee.to_bytes(8, 'big')]
        )
    ]

    transactionGroup = TransactionGroup(transactions)
    transactionGroup.sign_with_private_key(funder.getAddress(), funder.getPrivateKey())
    transactionGroup.submit(client, True)