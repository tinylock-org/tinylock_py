
from algosdk.v2client.algod import AlgodClient
from algosdk.logic import get_application_address
from algosdk.future.transaction import PaymentTxn, ApplicationNoOpTxn
from utils.account import Account
from tinyman.utils import TransactionGroup


def setupAlgolockerApp(
    client: AlgodClient,
    appID: int,
    funder: Account,
    tinylock_asa_id: int
) : #-> None
    appAddr = get_application_address(appID)
    suggestedParams = client.suggested_params()

    fundingAmount = (
        # min account balance
        2 * 100_000
    )

    suggested_params_2 = client.suggested_params()
    suggested_params_2.fee = 2000 #Optin

    transactions = [
        PaymentTxn(
            sender=funder.getAddress(),
            sp=suggestedParams,
            receiver=appAddr,
            amt=fundingAmount
        ),
        ApplicationNoOpTxn(
            sender=funder.getAddress(),
            sp=suggested_params_2,
            index=appID,
            app_args=['init'],
            foreign_assets=[tinylock_asa_id]
        )
    ]

    transactionGroup = TransactionGroup(transactions)
    transactionGroup.sign_with_private_key(funder.getAddress(), funder.getPrivateKey())
    transactionGroup.submit(client, True)

