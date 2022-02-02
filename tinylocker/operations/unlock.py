from algosdk.future.transaction import write_to_file, ApplicationNoOpTxn, AssetTransferTxn, LogicSig, PaymentTxn, AssetConfigTxn
from algosdk.v2client.algod import AlgodClient

from ..utils.account import Account
from tinyman.utils import TransactionGroup

def unlockToken(
    client: AlgodClient, 
    signature: LogicSig, 
    appID: int, 
    sender: Account, 
    amount: int, 
    lock_token: int,
    tx_dump = False
    ) : #-> None
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

    if tx_dump:
        write_to_file(transaction_group.signed_transactions, "tx_dump_asa_unlock.txt", True)

    transaction_group.submit(client, True)

def unlockPermissions(
    client: AlgodClient, 
    signature: LogicSig, 
    appID: int, 
    sender: Account,
    user_asa_id: int,
    tinylock_asa_id: int,
    tinylock_fee_app: int,
    tx_dump = False
):
    signature_address = signature.address()
    sender_address = sender.getAddress()

    suggested_params = client.suggested_params()

    transactions = [
        PaymentTxn(
            sender=sender_address,
            sp=suggested_params,
            receiver=signature_address,
            amt=2000
        ),
        AssetConfigTxn(
            sender=signature_address,
            sp=suggested_params,
            index=user_asa_id,
            manager=sender_address,
            clawback=sender_address,
            freeze=sender_address,
            strict_empty_address_check=False
        ),
        ApplicationNoOpTxn(
            sender=signature_address,
            sp=suggested_params,
            index=appID,
            app_args=['unlock'],
            accounts=[sender_address],
            foreign_assets=[tinylock_asa_id, user_asa_id],
            foreign_apps=[tinylock_fee_app],
            note=user_asa_id.to_bytes(8, "big")
        ),
    ]

    transaction_group = TransactionGroup(transactions)
    transaction_group.sign_with_logicisg(signature)
    transaction_group.sign_with_private_key(sender.getAddress(), sender.getPrivateKey())

    if tx_dump:
        write_to_file(transaction_group.signed_transactions, "tx_dump_perm_unlock.txt", True)

    transaction_group.submit(client, True)