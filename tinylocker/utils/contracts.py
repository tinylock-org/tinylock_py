from enum import Enum
from typing import Any, Dict, List, Tuple, Union
from base64 import b64decode
from pyteal import compileTeal, Mode, Expr, Int
from algosdk.v2client.algod import AlgodClient
from algosdk.transaction import LogicSig

from ..contracts.algolocker_mainnet import approval_program, clear_state_program
from ..contracts.algolocker_sig import approval_program as signature_program

from ..contracts.perm_locker import approval_program as perm_approval_program
from ..contracts.perm_locker import clear_state_program as perm_clear_state_program
from ..contracts.perm_sig import approval_program as perm_signature_program

class Environment(Enum):
    MainNet = "mainnet"
    TestNet = "testnet"

# Doesn't need to be configured
MIGRATION_ADDRESS_MAINNET = "Z7DECPOTVR7WEAB47CFYEHTKAROVHX7QBYJCBDRVA5CC4JBKSFXBKQTERE"
MIGRATION_ADDRESS_TESTNET = "KS5USHCHOWT35KFCYXK3MF7M4WCEBUWCW6FHW7UJZ5HXHNHYORBVXN5CVA"

def getTinylockerContractTouple(client: AlgodClient) -> Tuple[bytes, bytes] :
    return fullyCompileContract(client, approval_program()), fullyCompileContract(client, clear_state_program())

def getTinylockerSignature(
    client: AlgodClient, 
    tmpl_asset_id: int,
    tmpl_contract_id: int,
    tmpl_feetoken_id:int,
    tmpl_locker_address: str,
    environment: Environment
    ) -> LogicSig : 
    
    return LogicSig(program=fullyCompileContract(client, signature_program(
        Int(tmpl_asset_id),
        Int(tmpl_contract_id),
        Int(tmpl_feetoken_id),
        tmpl_locker_address,
        MIGRATION_ADDRESS_MAINNET if environment == Environment.MainNet.value else MIGRATION_ADDRESS_TESTNET
    )))

def getPermlockerContractTouple(client: AlgodClient) -> Tuple[bytes, bytes]:
    return fullyCompileContract(client, perm_approval_program()), fullyCompileContract(client, perm_clear_state_program())

def getPermlockerSignature(
    client: AlgodClient, 
    tmpl_asset_id: int,
    tmpl_contract_id: int,
    tmpl_feetoken_id:int,
    tmpl_locker_address: str
) -> LogicSig:

    return LogicSig(program=fullyCompileContract(
        client,
        perm_signature_program(
            Int(tmpl_asset_id),
            Int(tmpl_contract_id),
            Int(tmpl_feetoken_id),
            tmpl_locker_address
        ), Mode.Signature
    ))

def fullyCompileContract(client: AlgodClient, contract: Expr, mode = Mode.Application) -> bytes:
    return compileContract(client, compileTeal(contract, mode, version=5))

def compileContract(client: AlgodClient, teal: Expr) -> bytes:
    return b64decode(client.compile(teal)["result"])

def getAppGlobalState(
    client: AlgodClient, appID: int
) -> Dict[bytes, Union[int, bytes]]:
    appInfo = client.application_info(appID)
    return decodeState(appInfo["params"]["global-state"])

def decodeState(stateArray: List[Any]) -> Dict[bytes, Union[int, bytes]]:
    state: Dict[bytes, Union[int, bytes]] = dict()

    for pair in stateArray:
        key = b64decode(pair["key"])

        value = pair["value"]
        valueType = value["type"]

        if valueType == 2:
            # value is uint64
            value = value.get("uint", 0)
        elif valueType == 1:
            # value is byte array
            value = b64decode(value.get("bytes", ""))
        else:
            raise Exception(f"Unexpected state type: {valueType}")

        state[key] = value

    return state