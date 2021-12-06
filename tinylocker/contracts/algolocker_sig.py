from pyteal import *

# Signature Params:
# Int
# Int
# Int
# String

def approval_program(
    TMPL_ASSET_ID,
    TMPL_CONTRACT_ID,
    TMPL_FEETOKEN_ID,
    TMPL_LOCKER_ADDRESS
    ):

    gtx_lock_algo_fee_to_sig = And(
        Gtxn[0].amount() >= Int(2000), # Todo: Verify correct fees
        Gtxn[0].receiver() == Txn.sender(), # Signature should get fees
        Gtxn[0].sender() != Txn.sender() # Signature does not pay the fee
    )

    gtx_lock_tinylock_fee_to_contract = And(
        Gtxn[1].type_enum() == TxnType.AssetTransfer, # Asset Transfer
        Gtxn[1].sender() != Txn.sender(), # Signature is not the sender
        # Gtxn[1].asset_receiver() == Addr(TMPL_CONTRACT_ADDRESS), # receiver is checked in the contract
        Gtxn[1].asset_amount() > Int(0), # Amount > 0
        Gtxn[1].xfer_asset() == TMPL_FEETOKEN_ID # Token must be the fee token
    )

    gtx_lock_optin_to_contract = And(
        Gtxn[2].type_enum() == TxnType.ApplicationCall, # OptIn is a ApplicationCall
        Gtxn[2].application_id() == TMPL_CONTRACT_ID, # App must be Contract
        Gtxn[2].sender() == Txn.sender(), # Signature is sender
        Gtxn[2].application_args[0] == Bytes("lock"),
        Gtxn[2].assets[0] == TMPL_FEETOKEN_ID,
    )

    gtx_lock_optin_to_asset = And(
        Gtxn[3].type_enum() == TxnType.AssetTransfer, # OptIn is Asset Transfer
        Gtxn[3].sender() == Txn.sender(), # Signature is sender
        Gtxn[3].asset_receiver() == Txn.sender(), # Signature is receiver
        Gtxn[3].amount() == Int(0), # OptIn amount should be 0
        Gtxn[3].xfer_asset() == TMPL_ASSET_ID # Must be the token that is being locked
    )

    gtx_lock_asset_to_sig = And(
        Gtxn[4].type_enum() == TxnType.AssetTransfer, # Transfer 
        Gtxn[4].sender() != Txn.sender(), # Signature is not the sender
        Gtxn[4].asset_receiver() == Txn.sender(), # Signature is receiver
        Gtxn[4].asset_amount() > Int(0), # Asset amount should be more than 0
        Gtxn[4].xfer_asset() == TMPL_ASSET_ID, # Must be the token that is being locked
    )

    # Lockgroup TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to CONTRACT
    # 2) SIG  -> OptIn to CONTRACT
    # 3) SIG  -> Asset OptIn
    # 4) User -> Asset TX to SIG

    isLockGroup = And(
        gtx_lock_algo_fee_to_sig,
        gtx_lock_tinylock_fee_to_contract,
        gtx_lock_optin_to_contract,
        gtx_lock_optin_to_asset,
        gtx_lock_asset_to_sig
    )

    gtx_unlock_algo_fee_to_sig = And(
        Gtxn[0].amount() > Int(0),
        Gtxn[0].receiver() == Txn.sender(), # Signature should get fees
        Gtxn[0].sender() != Txn.sender() # Signature does not pay the fee
    )

    gtx_unlock_call_to_contract = And(
        Gtxn[1].type_enum() == TxnType.ApplicationCall, # OptIn is a ApplicationCall
        Gtxn[1].application_id() == TMPL_CONTRACT_ID, # App must be Contract
        Gtxn[1].sender() == Txn.sender(), # Signature is sender
        Gtxn[1].application_args[0] == Bytes("unlock")
    )

    gtx_unlock_asset_to_locker = And(
        Gtxn[2].type_enum() == TxnType.AssetTransfer, # Transfer 
        Gtxn[2].sender() == Txn.sender(), # Signature is the sender
        Gtxn[2].asset_receiver() == Addr(TMPL_LOCKER_ADDRESS), # Locker is receiver
        Gtxn[2].xfer_asset() == TMPL_ASSET_ID # Must be the token that is being locked
    )

    # Unlock TXN
    # 0) User -> TX Fee to SIG
    # 1) SIG  -> Unlock to CONTRACT
    # 2) SIG  -> Asset TX to OWNER

    isUnlockGroup = And(
        gtx_unlock_algo_fee_to_sig,
        gtx_unlock_call_to_contract,
        gtx_unlock_asset_to_locker
    )

    gtx_relock_algo_fee_to_sig = And(
        Gtxn[0].amount() > Int(0),
        Gtxn[0].receiver() == Txn.sender(), # Signature should get fees
        Gtxn[0].sender() != Txn.sender() # Signature does not pay the fee
    )
    gtx_relock_asset_to_locker = And(
        Gtxn[2].type_enum() == TxnType.AssetTransfer, # Transfer 
        Gtxn[2].sender() != Txn.sender(), # Signature is not the sender
        Gtxn[2].asset_receiver() == Txn.sender(), # Signature is receiver
        Gtxn[2].asset_amount() > Int(0), # Asset amount should be more than 0
        Gtxn[2].xfer_asset() == TMPL_ASSET_ID, # Must be the token that is being locked
    )
    gtx_relock_call_to_contract = And(
        Gtxn[3].type_enum() == TxnType.ApplicationCall, # OptIn is a ApplicationCall
        Gtxn[3].application_id() == TMPL_CONTRACT_ID, # App must be Contract
        Gtxn[3].sender() == Txn.sender(), # Signature is sender
        Gtxn[3].application_args[0] == Bytes("relock")
    )


    # Relock TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to CONTRACT
    # 2) User -> Asset to SIG
    # 3) SIG  -> Relock to CONTRACT

    isRelockGroup = And(
        gtx_relock_algo_fee_to_sig,
        gtx_relock_call_to_contract,
        gtx_relock_asset_to_locker
    )

    return Seq(
        If(Global.group_size() == Int(5)).Then(
            Cond(
                [isLockGroup, Approve()]
            )
        ),
        If(Global.group_size() == Int(3)).Then(
            Cond(
                [isUnlockGroup, Approve()]
            )
        ),
        If(Global.group_size() == Int(4)).Then(
            Cond(
                [isRelockGroup, Approve()]
            )
        ),
        Reject()
    )


if __name__ == "__main__":
    with open("algolocker_sig.teal.tmpl", "w") as f:
        compiled = compileTeal(approval_program(Int(10000000000), Int(20000000000), Int(30000000000), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"), mode=Mode.Signature, version=5)
        # Replace values with TMPL VARIABLES
        compiled = compiled.replace("10000000000", "TMPL_ASSET_ID")
        compiled = compiled.replace("20000000000", "TMPL_CONTRACT_ID")
        compiled = compiled.replace("30000000000", "TMPL_FEETOKEN_ID")
        compiled = compiled.replace("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "TMPL_LOCKER_ADDRESS")

        f.write(compiled)