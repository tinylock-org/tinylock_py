from algosdk.v2client.algod import AlgodClient
from algosdk.future.transaction import StateSchema, ApplicationCreateTxn, OnComplete
from utils.contracts import getTinylockerContractTouple
from utils.transaction import waitForTransaction
from utils.account import Account

def createAlgolockerApp(
    client: AlgodClient,
    sender: Account,
    tinylock_asa_id: int,
    tinylock_fee_amount: int
) : 
    approval, clear = getTinylockerContractTouple(client)

    globalSchema = StateSchema(num_uints=2, num_byte_slices=0)
    localSchema = StateSchema(num_uints=1, num_byte_slices=0)

    app_args = [
        tinylock_asa_id.to_bytes(8, "big"),
        tinylock_fee_amount.to_bytes(8, "big")
    ]

    suggested_params = client.suggested_params()

    txn = ApplicationCreateTxn(
        sender=sender.getAddress(),
        on_complete=OnComplete.NoOpOC,
        approval_program=approval,
        clear_program=clear,
        global_schema=globalSchema,
        local_schema=localSchema,
        app_args=app_args,
        sp=suggested_params
    )

    signedTxn = txn.sign(sender.getPrivateKey())

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex