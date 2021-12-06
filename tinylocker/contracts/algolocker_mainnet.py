from pyteal import *

def approval_program():

    @Subroutine(TealType.none)
    def optinToken(asa: Int):
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asa,
                    TxnField.asset_receiver: Global.current_application_address()
                }
            ),
            InnerTxnBuilder.Submit()
        )

    # Tokenfee TX object
    on_lock_asset_tx = Gtxn[1]
    # Tokenfee TX asset_amount
    on_lock_asset_tx_amount = on_lock_asset_tx.asset_amount()

    # Tokenfee TX safety checks
    on_lock_tx_check_asset = And(
        on_lock_asset_tx.type_enum() == TxnType.AssetTransfer,
        on_lock_asset_tx.asset_receiver() == Global.current_application_address(),
        on_lock_asset_tx_amount >= App.globalGet( Bytes("tinylock_fee") ),
        on_lock_asset_tx.xfer_asset() == Txn.assets[0], # asa asset transfer matches appcall external_asset 0 ( shouldnt be tinylock asa)
        Txn.assets[0] == App.globalGet( Bytes("tinylock_asa_id") ) # Fee token should have tinylock asa id
    )

    # Optin TX object
    on_lock_appcall_tx = Gtxn[2]
    # Optin TX time
    on_lock_appcall_tx_time = Btoi(Txn.application_args[1])

    # Optin TX safety checks
    on_lock_tx_check_appcall = And(
        on_lock_appcall_tx.type_enum() == TxnType.ApplicationCall,
        on_lock_appcall_tx_time <= Int(32503680000),
        on_lock_appcall_tx_time >= Global.latest_timestamp()
    )

    # Optin initialize local storage of sender
    on_lock_tx_init_storage = Seq(
        App.localPut(Txn.sender(), Bytes("time"), on_lock_appcall_tx_time),
    )

    # Lockgroup TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to CONTRACT
    # 2) SIG  -> OptIn to CONTRACT
    # 3) SIG  -> Asset OptIn
    # 4) User -> Asset TX to SIG

    on_lock = Seq(
        If( 
            And(
                # Make sure the user has no active lock
                App.localGet( Txn.sender(), Bytes("time") ) == Int(0),
                Global.group_size() == Int(5),
                on_lock_tx_check_asset,
                on_lock_tx_check_appcall
            )
        ).Then(
            Seq(
                on_lock_tx_init_storage,
                Approve()
            )
        ),
        Reject()
    )

    on_relock_asset_tx = Gtxn[1]
    on_relock_asset_tx_amount = on_relock_asset_tx.asset_amount()

    on_relock_tx_check_asset = And(
        on_relock_asset_tx.type_enum() == TxnType.AssetTransfer,
        on_relock_asset_tx.asset_receiver() == Global.current_application_address(),
        on_relock_asset_tx_amount >= App.globalGet( Bytes("tinylock_fee") ),
        on_relock_asset_tx.xfer_asset() == Txn.assets[0], # asa asset transfer matches appcall external_asset 0 ( shouldnt be tinylock asa)
        Txn.assets[0] == App.globalGet( Bytes("tinylock_asa_id") ) # Fee token should have tinylock asa id
    )

    on_relock_tx = Gtxn[3]
    on_relock_tx_check_appcall = And(
        on_relock_tx.type_enum() == TxnType.ApplicationCall,
        on_lock_appcall_tx_time <= Int(32503680000),
        on_lock_appcall_tx_time >= Global.latest_timestamp()
    )

    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to CONTRACT
    # 2) User -> Asset
    # 3) SIG  -> Relock to CONTRACT
    on_relock = Seq(
        If(
            And(
                on_lock_appcall_tx_time >= App.localGet( Txn.sender(), Bytes("time")), # equal greater last lock
                Global.group_size() == Int(4),
                on_relock_tx_check_asset,
                on_relock_tx_check_appcall
            )
        ).Then(
            Seq(
                on_lock_tx_init_storage,
                Approve()
            )
        ),
        Reject()
    )

     # Unlock TXN
    # 0) User -> TX Fee to SIG
    # 1) SIG  -> Unlock to CONTRACT
    # 2) SIG  -> Asset TX to OWNER

    on_unlock = Seq(
        # Time must be over the specified timelock
        If( 
            And(
                App.localGet( Txn.sender(), Bytes("time")) <= Global.latest_timestamp(),
                Global.group_size() == Int(3)
            )
        ).Then(
            Seq(
                App.localPut(Txn.sender(), Bytes("time"), Int(0)),
                Approve()
            )
        ),
        Reject()
    )

    on_init = Seq(
        optinToken(App.globalGet(Bytes("tinylock_asa_id"))),
        Approve()
    )

    on_update = Seq(
        If(
            Global.creator_address() == Txn.sender()
        ).Then(
            Seq(
                App.globalPut( Bytes("tinylock_fee"), Btoi(Txn.application_args[1])),
                Approve()
            )
        ),
        Reject()
    )

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("lock"), on_lock],
        [on_call_method == Bytes("unlock"), on_unlock],
        [on_call_method == Bytes("init"), on_init],
        [on_call_method == Bytes("update"), on_update],
        [on_call_method == Bytes("relock"), on_relock]
    )

    on_create = Seq(
        App.globalPut( Bytes("tinylock_asa_id"),  Btoi(Txn.application_args[0]) ), # Tinylock Token id
        App.globalPut( Bytes("tinylock_fee"), Btoi(Txn.application_args[1])),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.NoOp            
            ),
            on_call
        ],
        [
            Or(
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication,
                Txn.on_completion() == OnComplete.DeleteApplication
            ),
            Reject()
        ]
    )

    return program

def clear_state_program():
    return Approve()

if __name__ == "__main__":
    with open("algolocker_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("algolocker_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)