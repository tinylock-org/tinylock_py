from typing import Any, Dict, List
from algosdk import account, mnemonic
from algosdk.v2client.algod import AlgodClient


class Account:
    """Represents a private key and address for an Algorand account"""

    def __init__(self, privateKey: str) -> None:
        self.sk = privateKey
        self.addr = account.address_from_private_key(privateKey)

    def getAddress(self) -> str:
        return self.addr

    def getPrivateKey(self) -> str:
        return self.sk

    def getMnemonic(self) -> str:
        return mnemonic.from_private_key(self.sk)

    @classmethod
    def FromMnemonic(cls, m: str) -> "Account":
        return cls(mnemonic.to_private_key(m))


def getBalances(client: AlgodClient, account: str) -> Dict[int, int]:
    balances: Dict[int, int] = dict()

    accountInfo = client.account_info(account)

    # set key 0 to Algo balance
    balances[0] = accountInfo["amount"]

    assets: List[Dict[str, Any]] = accountInfo.get("assets", [])
    for assetHolding in assets:
        assetID = assetHolding["asset-id"]
        amount = assetHolding["amount"]
        balances[assetID] = amount

    return balances
