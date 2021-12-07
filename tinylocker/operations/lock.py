

from algosdk.future.transaction import ApplicationOptInTxn, AssetOptInTxn, AssetTransferTxn, LogicSig, PaymentTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.logic import get_application_address
from ..utils.account import Account
from tinyman.utils import TransactionGroup

def lockToken(client: AlgodClient, signature: LogicSig, appID: int, sender: Account, amount: int, user_asa_id: int, tinylock_asa_id:int, time: int, fee: int) : #-> None
    appAddr = get_application_address(appID)
    signature_address = signature.address()

    print("APP Address: ", appAddr, ", SIG Address: ", signature_address)

    suggested_params = client.suggested_params()

    transactions = [
        PaymentTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=signature_address,
            amt=330500,
            note='txs fee'
        ),
        AssetTransferTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=appAddr,
            amt=fee,
            note=user_asa_id.to_bytes(8, "big"), # Is not checked by the smart contract because it's just a shortcut for the webapp. Make sure to include it. Will be obsolete after MainNet Webapp 2.0
            index=tinylock_asa_id
        ),
        ApplicationOptInTxn(
            sender=signature_address,
            sp=suggested_params,
            index=appID,
            app_args=['lock', time.to_bytes(8, "big")],
            accounts=[sender.getAddress()],
            foreign_assets=[tinylock_asa_id]
        ),
        AssetOptInTxn(
            sender=signature_address,
            sp=suggested_params,
            index=user_asa_id
        ),
        AssetTransferTxn(
            sender=sender.getAddress(),
            sp=suggested_params,
            receiver=signature_address,
            amt=amount,
            index=user_asa_id
        )
    ]

    transaction_group = TransactionGroup(transactions)
    transaction_group.sign_with_logicisg(signature)
    transaction_group.sign_with_private_key(sender.getAddress(), sender.getPrivateKey())

    transaction_group.submit(client, True)