from algosdk.future.transaction import ApplicationNoOpTxn, AssetConfigTxn, AssetTransferTxn, LogicSig, PaymentTxn, write_to_file
from algosdk.logic import get_application_address
from algosdk.v2client.algod import AlgodClient
from ..utils.account import Account
from tinyman.utils import TransactionGroup


def relockToken(
    client: AlgodClient,
    signature: LogicSig,
    appID: int,
    sender: Account,
    amount: int,
    user_asa_id: int,
    tinylock_asa_id: int,
    time: int,
    fee: int,
    tx_dump=False
):  # -> None
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
            # In relock it's not really necessary since the WebApp searches for locks and filters balances. It doesn't care about the specific relock operation.
            note=user_asa_id.to_bytes(8, "big"),
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
    transaction_group.sign_with_private_key(
        sender.getAddress(), sender.getPrivateKey())

    if tx_dump:
        write_to_file(transaction_group.signed_transactions,
                      "tx_dump_asa_relock.txt", True)

    transaction_group.submit(client, True)


def relockPermissions(
    client: AlgodClient,
    signature: LogicSig,
    appID: int,
    sender: Account,
    user_asa_id: int,
    tinylock_asa_id: int,
    tinylock_fee_app: int,
    time: int,
    fee: int,
    extend=True,
    clawback=True,
    freeze=True,
    tx_dump=False
):  # -> None

    feeAddr = get_application_address(tinylock_fee_app)

    signature_address = signature.address()

    print("Relocking permissions")

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
            receiver=feeAddr,
            amt=fee,
            index=tinylock_asa_id
        ),
        ApplicationNoOpTxn(
            sender=signature_address,
            sp=suggested_params,
            index=appID,
            app_args=['relock', time.to_bytes(8, "big")],
            accounts=[sender.getAddress()],
            foreign_assets=[tinylock_asa_id, user_asa_id],
            foreign_apps=[tinylock_fee_app],
            note=user_asa_id.to_bytes(8, "big")
        )
    ]
    if not extend:
        transactions.append(
            AssetConfigTxn(
                sender=sender.getAddress(),
                sp=suggested_params,
                index=user_asa_id,
                manager=signature_address,
                clawback=signature_address if clawback else "",
                freeze=signature_address if freeze else "",
                strict_empty_address_check=False
            )
        )

    transaction_group = TransactionGroup(transactions)
    transaction_group.sign_with_logicisg(signature)
    transaction_group.sign_with_private_key(
        sender.getAddress(), sender.getPrivateKey())

    if tx_dump:
        write_to_file(transaction_group.signed_transactions,
                      "tx_dump_perm_relock.txt", True)

    transaction_group.submit(client, True)
