from pyteal import *

# Signature Params:
# Int
# Int
# String
# String

def approval_program(
    TMPL_ASSET_ID,
    TMPL_CONTRACT_ID,
    TMPL_FEETOKEN_ID,
    TMPL_LOCKER_ADDRESS
):
    gtx_lock_algo_fee_to_sig = And(
        Gtxn[0].amount() >= Int(2000),
        Gtxn[0].receiver() == Txn.sender(),  # Signature should get fees
        Gtxn[0].sender() == Addr(TMPL_LOCKER_ADDRESS)  # Signature does not pay the fee
    )

    gtx_lock_tinylock_fee_to_contract = And(
        Gtxn[1].type_enum() == TxnType.AssetTransfer,  # Asset Transfer
        Gtxn[1].sender() == Addr(TMPL_LOCKER_ADDRESS),  # Signature is not the sender
        # Gtxn[1].asset_receiver() == Addr(TMPL_CONTRACT_ADDRESS), # receiver is checked in the contract
        Gtxn[1].asset_amount() > Int(0),  # Amount > 0
        Gtxn[1].xfer_asset() == TMPL_FEETOKEN_ID,  # Token must be the fee token
        Gtxn[1].asset_close_to() == Global.zero_address()
    )

    gtx_lock_optin_to_contract = And(
        # OptIn is a ApplicationCall
        Gtxn[2].application_args[0] == Bytes("lock"),
        Gtxn[2].type_enum() == TxnType.ApplicationCall,
        Gtxn[2].application_id() == TMPL_CONTRACT_ID,  # App must be Contract
        Gtxn[2].sender() == Txn.sender(),  # Signature is sender
        Gtxn[2].assets[0] == TMPL_FEETOKEN_ID,
        Gtxn[2].assets[1] == TMPL_ASSET_ID,
        Gtxn[2].rekey_to() == Global.zero_address() # No rekey of the signature
    )

    gtx_lock_optin_to_asset = And(
        # OptIn is Asset Transfer
        Gtxn[3].type_enum() == TxnType.AssetTransfer,
        Gtxn[3].sender() == Txn.sender(),  # Signature is sender
        Gtxn[3].asset_receiver() == Txn.sender(),  # Signature is receiver
        Gtxn[3].amount() == Int(0),  # OptIn amount should be 0
        # Must be the token that is being locked
        Gtxn[3].xfer_asset() == TMPL_ASSET_ID,
        Gtxn[3].rekey_to() == Global.zero_address() # No rekey of the signature
    )

    @Subroutine(TealType.uint64)
    def get_config_tx(gtxn_index: Int):
        return And(
        Gtxn[gtxn_index].type_enum() == TxnType.AssetConfig,  # Transfer
        Gtxn[gtxn_index].sender() != Txn.sender(),  # Signature is not the sender
        # Sender is Signature creator
        Gtxn[gtxn_index].sender() == Addr(TMPL_LOCKER_ADDRESS),
        # Must be the token that is being locked
        Gtxn[gtxn_index].config_asset() == TMPL_ASSET_ID,
        Gtxn[gtxn_index].rekey_to() == Global.zero_address(),
        # Signature must be the asset manager
        Gtxn[gtxn_index].config_asset_manager() == Txn.sender(),
        # Signature must be the new clawback or 0
        Or(
            Gtxn[gtxn_index].config_asset_clawback() == Txn.sender(),
            Gtxn[gtxn_index].config_asset_clawback() == Global.zero_address()
        ),
        # Signature must be the freeze or 0
        Or(
            Gtxn[gtxn_index].config_asset_freeze() == Txn.sender(),
            Gtxn[gtxn_index].config_asset_freeze() == Global.zero_address()
        )
    )

    # Lockgroup TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to LOCKER CONTRACT
    # 2) SIG  -> OptIn to CONTRACT
    # 3) SIG  -> Asset OptIn
    # 4) User -> Asset Config to Signature

    isLockGroup = And(
        Global.group_size() == Int(5),
        gtx_lock_optin_to_contract,
        gtx_lock_algo_fee_to_sig,
        gtx_lock_tinylock_fee_to_contract,
        gtx_lock_optin_to_asset,
        get_config_tx(Int(4))
    )

    gtx_unlock_algo_fee_to_sig = And(
        Gtxn[0].amount() > Int(0),
        Gtxn[0].receiver() == Txn.sender(),  # Signature should get fees
        Gtxn[0].sender() == Addr(TMPL_LOCKER_ADDRESS)  # Signature does not pay the fee
    )

    gtx_unlock_call_to_contract = And(
        # OptIn is a ApplicationCall
        Gtxn[2].application_args[0] == Bytes("unlock"),
        Gtxn[2].type_enum() == TxnType.ApplicationCall,
        Gtxn[2].application_id() == TMPL_CONTRACT_ID,  # App must be Contract
        Gtxn[2].sender() == Txn.sender(),  # Signature is sender
        Gtxn[2].rekey_to() == Global.zero_address(),
        Gtxn[2].assets[0] == TMPL_FEETOKEN_ID,
        Gtxn[2].assets[1] == TMPL_ASSET_ID
    )

    on_unlock_tx_config = And(
        # Signature must be the asset manager
        Gtxn[1].config_asset_manager() == Addr(TMPL_LOCKER_ADDRESS),
        # Signature must be the new clawback or 0
        Or(
            Gtxn[1].config_asset_clawback() == Addr(TMPL_LOCKER_ADDRESS),
            Gtxn[1].config_asset_clawback() == Global.zero_address()
        ),
        # Signature must be the freeze or 0
        Or(
            Gtxn[1].config_asset_freeze() == Addr(TMPL_LOCKER_ADDRESS),
            Gtxn[1].config_asset_freeze() == Global.zero_address()
        )
    )

    gtx_unlock_asset_to_locker = And(
        Gtxn[1].type_enum() == TxnType.AssetConfig,  # Transfer
        Gtxn[1].sender() == Txn.sender(),  # Signature is the sender
        # Must be the token that is being locked
        Gtxn[1].config_asset() == TMPL_ASSET_ID,
        Gtxn[1].rekey_to() == Global.zero_address(),
        on_unlock_tx_config
    )

    # Unlock TXN
    # 0) User -> TX Fee to SIG
    # 1) SIG  -> Unlock to CONTRACT
    # 2) SIG  -> Asset TX to OWNER

    isUnlockGroup = And(
        Global.group_size() == Int(3),
        gtx_unlock_call_to_contract,
        gtx_unlock_algo_fee_to_sig,
        gtx_unlock_asset_to_locker
    )

    gtx_relock_algo_fee_to_sig = And(
        Gtxn[0].amount() > Int(0),
        Gtxn[0].receiver() == Txn.sender(),  # Signature should get fees
        Gtxn[0].sender() == Addr(TMPL_LOCKER_ADDRESS)  # Signature does not pay the fee
    )

    gtx_relock_call_to_contract = And(
        # OptIn is a ApplicationCall
        Gtxn[2].type_enum() == TxnType.ApplicationCall,
        Gtxn[2].application_id() == TMPL_CONTRACT_ID,  # App must be Contract
        Gtxn[2].sender() == Txn.sender(),  # Signature is sender
        Gtxn[2].rekey_to() == Global.zero_address(),
    )

    # Relock TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to LOCKER CONTRACT
    # 2) SIG  -> Relock to CONTRACT
    # 3) OPTIONAL: User -> Asset Config to Signature

    isRelockGroup = And(
        Gtxn[2].application_args[0] == Bytes("relock"),
        Or(
            Global.group_size() == Int(3),
            Seq(
                If(Global.group_size() == Int(4), get_config_tx(Int(3)), Int(0))
            )  
        ),
        gtx_relock_call_to_contract,   
        gtx_relock_algo_fee_to_sig,
        gtx_lock_tinylock_fee_to_contract
    )

    return Seq(
        If(
            isUnlockGroup
        ).Then(
            Approve()
        ),
        If(
            isRelockGroup
        ).Then(
            Approve()
        ),
        If(
            isLockGroup
        ).Then(
            Approve()
        ),
        Reject()
    )


if __name__ == "__main__":
    with open("permlocker_sig.teal.tmpl", "w") as f:
        compiled = compileTeal(approval_program(Int(10000000000), Int(20000000000), Int(
            30000000000), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"), mode=Mode.Signature, version=5)
        # Replace values with TMPL VARIABLES
        compiled = compiled.replace("10000000000", "TMPL_ASSET_ID")
        compiled = compiled.replace("20000000000", "TMPL_CONTRACT_ID")
        compiled = compiled.replace("30000000000", "TMPL_FEETOKEN_ID")
        compiled = compiled.replace(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "TMPL_LOCKER_ADDRESS")

        f.write(compiled)
