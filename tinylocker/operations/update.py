

from algosdk.future.transaction import write_to_file, ApplicationNoOpTxn
from algosdk.v2client.algod import AlgodClient
from tinyman.utils import TransactionGroup
from ..utils.account import Account
from algosdk.encoding import decode_address
from algosdk.logic import get_application_address

def changeAlgolockerFee(
    client: AlgodClient,
    appID: int,
    funder: Account,
    fee: int,
    tx_dump = False
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

    if tx_dump:
        write_to_file(transactionGroup.signed_transactions, "tx_dump_asa_update.txt", True)

    transactionGroup.submit(client, True)


def reconfigurePermlockerFee(
    client: AlgodClient,
    appID: int,
    sender: Account,
    tinylock_app_id: int,
    tx_dump = False
):
    suggestedParams = client.suggested_params()

    tinylock_app_address = get_application_address(tinylock_app_id)

    app_args = [
        'reconfigure',
         decode_address(tinylock_app_address)
        ]
    foreign_apps = [tinylock_app_id]

    transactions = [
        ApplicationNoOpTxn(
            sender=sender.getAddress(),
            sp=suggestedParams,
            index=appID,
            app_args=app_args,
            foreign_apps=foreign_apps
        )
    ]

    transactionGroup = TransactionGroup(transactions)
    transactionGroup.sign_with_private_key(sender.getAddress(), sender.getPrivateKey())

    if tx_dump:
        write_to_file(transactionGroup.signed_transactions, "tx_dump_perm_reconfigure.txt", True)

    transactionGroup.submit(client, True)
