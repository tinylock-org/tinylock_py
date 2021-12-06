import sys
from typing import Dict
from algosdk import mnemonic

from algosdk.v2client.algod import AlgodClient
from tinyman.v1.pools import Pool
from tinyman.v1.client import TinymanClient
from tinyman.v1.constants import MAINNET_VALIDATOR_APP_ID, TESTNET_VALIDATOR_APP_ID
from constants import ALGOD_ADDRESS_MAINNET, ALGOD_ADDRESS_TESTNET, ALGOD_TOKEN, MAINNET, TESTNET, TINYLOCK_APP_MAINNET, TINYLOCK_APP_TESTNET, TINYLOCK_ASA_MAINNET, TINYLOCK_ASA_TESTNET, USER_MNEMONIC

from operations.lock import lockToken
from operations.relock import relockToken
from operations.unlock import unlockToken
from utils.account import Account, getBalances
from utils.contracts import getAppGlobalState, getTinylockerSignature

OP_METHOD = 1
CLIENT = AlgodClient
TINYMAN_CLIENT = TinymanClient
ENVIRONMENT = ""
ACCOUNT = Account
BALANCES = Dict[int, int]

def getAlgodClient() -> AlgodClient:
    return AlgodClient(
        ALGOD_TOKEN, 
        ALGOD_ADDRESS_TESTNET if ENVIRONMENT == TESTNET else ALGOD_ADDRESS_MAINNET,
        headers={'User-Agent': 'Client'}
        )

def main(argv):
    print("Args: ", argv)

    global ENVIRONMENT
    ENVIRONMENT = TESTNET if argv[0] == TESTNET else MAINNET
    print("Using environment: ", ENVIRONMENT)

    global CLIENT
    CLIENT = getAlgodClient()

    global ACCOUNT
    ACCOUNT = Account(mnemonic.to_private_key(USER_MNEMONIC))

    global BALANCES
    BALANCES = getBalances(CLIENT, ACCOUNT.getAddress())

    global TINYMAN_CLIENT
    TINYMAN_CLIENT = TinymanClient(
        CLIENT,
        MAINNET_VALIDATOR_APP_ID 
        if ENVIRONMENT == MAINNET else 
        TESTNET_VALIDATOR_APP_ID
        )

    if argv[OP_METHOD] == "lock":
        doLock(argv[2:])
    elif argv[OP_METHOD] == "unlock":
        doUnlock(argv[2:])

    print("Wrong operation: ", argv[OP_METHOD])
    sys.exit(1)

def getPoolFor(asa1: int, asa2: int) -> Pool:
    asset1 = TINYMAN_CLIENT.fetch_asset(asa1)
    asset2 = TINYMAN_CLIENT.fetch_asset(asa2)

    return TINYMAN_CLIENT.fetch_pool(asset1, asset2)

def getTinylockAppId() -> int:
    return TINYLOCK_APP_TESTNET if ENVIRONMENT == TESTNET else TINYLOCK_APP_MAINNET

def getTinylockAsaId() -> int:
    return TINYLOCK_ASA_TESTNET if ENVIRONMENT == TESTNET else TINYLOCK_ASA_MAINNET


def getFeeInfo() -> int:
    tinylock_state = getAppGlobalState(
        CLIENT,
        getTinylockAppId()
    )

    return tinylock_state[b"tinylock_asa_id"], tinylock_state[b"tinylock_fee"]

def doLock(argv):

    arg_length = len(argv)
    # amount, date, token1, token2
    if arg_length < 3 or arg_length > 4:
        print("Wrong number of arguments %u for operation %s" % (arg_length, sys.argv[OP_METHOD+1]) )
        sys.exit(1)


    lock_token_asa = int(argv[2])

    if arg_length == 4:
        pool = getPoolFor(lock_token_asa, int(argv[3]))
        lock_token_asa = pool.liquidity_asset.id

    lockAmount = int(argv[0])
    locktime = int(argv[1])

    print(
        CLIENT, 
        lock_token_asa, 
        getTinylockAppId(), 
        getTinylockAsaId(), 
        ACCOUNT.getAddress()
    )


    tinylock_signature = getTinylockerSignature(
        CLIENT,
        lock_token_asa,
        getTinylockAppId(),
        getTinylockAsaId(),
        ACCOUNT.getAddress()
    )

    lockAsa, lockFee = getFeeInfo()

    if BALANCES[lockAsa] < lockFee:
        print("You dont have enough TinyLock in your account. Required: ", lockFee, " found: ", BALANCES[lockAsa])
        sys.exit(1)

    signature_balances = getBalances(CLIENT, tinylock_signature.address())

    if lock_token_asa in signature_balances: 
        relockToken(
            CLIENT,
            tinylock_signature,
            getTinylockAppId(),
            ACCOUNT,
            lockAmount,
            lock_token_asa,
            getTinylockAsaId(),
            locktime,
            lockFee
        )
    else:
        lockToken(
            CLIENT,
            tinylock_signature,
            getTinylockAppId(),
            ACCOUNT,
            lockAmount,
            lock_token_asa,
            getTinylockAsaId(),
            locktime,
            lockFee
        )

    sys.exit(0)

def doUnlock(argv):
    arg_length = len(argv)
    # token, amount
    if arg_length != 2:
        print("Wrong number of arguments %u for operation %s" % (arg_length, sys.argv[OP_METHOD+1]) )
        sys.exit(1)

    
    lock_token_asa = int(argv[0])
    unlock_amount = int(argv[1])

    if unlock_amount == 0:
        print("Can not unlock the amount 0")
        sys.exit(1)

    tinylock_signature = getTinylockerSignature(
        CLIENT,
        lock_token_asa,
        getTinylockAppId(),
        getTinylockAsaId(),
        ACCOUNT.getAddress()
    )   

    signature_balances = getBalances(CLIENT, tinylock_signature.address())

    if unlock_amount >= signature_balances[lock_token_asa]:
        print("Your unlock amount %u is greater than the available balance of the contract: %u" % (unlock_amount, signature_balances[lock_token_asa]))
        sys.exit(1)

    unlockToken(
        CLIENT,
        tinylock_signature,
        getTinylockAppId(),
        ACCOUNT,
        unlock_amount,
        lock_token_asa,
        )

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])