from pyteal import *


def approval_program():

    on_lock_fee_amount = App.globalGetEx(
        App.globalGet(Bytes("tinylock_locker_id")),
        Bytes("tinylock_fee")
    )

    get_fee_amount = Seq(
        on_lock_fee_amount,
        If(on_lock_fee_amount.hasValue())
        .Then(
            on_lock_fee_amount.value()
        )
        .Else(
            Reject()
        )
    )

    on_lock_fee_asa = App.globalGetEx(
        App.globalGet(Bytes("tinylock_locker_id")),
        Bytes("tinylock_asa_id")
    )

    get_fee_asa = Seq(
        on_lock_fee_asa,
        If(on_lock_fee_asa.hasValue())
        .Then(
            on_lock_fee_asa.value()
        )
        .Else(
            Reject()
        )
    )

    # Tokenfee TX safety checks
    on_lock_tx_check_fee = And(
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].asset_receiver() == App.globalGet(
            Bytes("tinylock_locker_address")),
        Gtxn[1].asset_amount() >= get_fee_amount,
        # Fee token should be tinylock asa id
        Gtxn[1].xfer_asset() == get_fee_asa
    )

    # Optin TX time
    on_lock_appcall_tx_time = Btoi(Txn.application_args[1])
    on_lock_appcall_tx_manager = Gtxn[4].sender()

    # Optin TX safety checks
    on_lock_tx_check_appcall = And(
        Gtxn[2].type_enum() == TxnType.ApplicationCall,
        on_lock_appcall_tx_time <= Int(32503680000),
        on_lock_appcall_tx_time >= Global.latest_timestamp(),
        Txn.assets[0] == Gtxn[1].xfer_asset()
    )
    # Optin initialize local storage of sender
    on_lock_tx_init_storage = Seq(
        App.localPut(Txn.sender(), Bytes("time"), on_lock_appcall_tx_time),
        App.localPut(Txn.sender(), Bytes("locker"), on_lock_appcall_tx_manager)
    )

    @Subroutine(TealType.uint64)
    def get_config_tx(gtxn_index: Int):
        return And(
            Gtxn[gtxn_index].sender() != Gtxn[2].sender(),
            Gtxn[gtxn_index].sender() == Gtxn[1].sender(),
            Gtxn[gtxn_index].sender() == Gtxn[0].sender(),
            Gtxn[gtxn_index].type_enum() == TxnType.AssetConfig,
            Gtxn[gtxn_index].config_asset() == Txn.assets[1],
            # Signature must be the new asset manager
            Gtxn[gtxn_index].config_asset_manager() == Gtxn[2].sender(),
            # Signature must be the new clawback or 0
            Or(
                Gtxn[gtxn_index].config_asset_clawback() == Gtxn[2].sender(),
                Gtxn[gtxn_index].config_asset_clawback() == Global.zero_address()
            ),
            # Signature must be the freeze or 0
            Or(
                Gtxn[gtxn_index].config_asset_freeze() == Gtxn[2].sender(),
                Gtxn[gtxn_index].config_asset_freeze() == Global.zero_address()
            )
        )

    # Lockgroup TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to LOCKER CONTRACT
    # 2) SIG  -> OptIn to CONTRACT
    # 3) SIG  -> Asset OptIn
    # 4) User -> Asset Config to Signature

    on_lock = Seq(
        If(
            And(
                # Make sure the user has no active lock
                App.localGet(Txn.sender(), Bytes("time")) == Int(0),
                Global.group_size() == Int(5),
                on_lock_tx_check_fee,
                on_lock_tx_check_appcall,
                get_config_tx(Int(4))
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
    # 1) SIG  -> Asset Config to OWNER
    # 2) SIG  -> Unlock to USER

    on_unlock = Seq(
        # Time must be over the specified timelock
        If(
            And(
                App.localGet(Txn.sender(), Bytes("time")
                             ) <= Global.latest_timestamp(),
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

    # Relock TXN
    # 0) User -> TX Fee to SIG
    # 1) User -> TinyLock Token to LOCKER CONTRACT
    # 2) SIG  -> Relock to CONTRACT
    # 3) OPTIONAL: User -> Asset Config to Signature

    on_relock = Seq(
        If(
            And(
                Or(
                    Seq(
                        If(
                            Global.group_size() == Int(3)
                        ).Then(
                            And(
                                App.localGet(
                                    Txn.sender(), Bytes("time")) > Int(0),
                                on_lock_appcall_tx_time >= App.localGet(
                                    Txn.sender(), Bytes("time"))
                            )
                        ).Else(
                            Int(0)
                        )
                    ),
                    Seq(
                        If(
                            Global.group_size() == Int(4)
                        ).Then(
                            And(
                                App.localGet(
                                    Txn.sender(), Bytes("time")) == Int(0),
                                get_config_tx(Int(3))
                            )
                        ).Else(
                            Int(0)
                        )
                    )
                ),
                on_lock_tx_check_appcall,
                on_lock_tx_check_fee
            )
        ).Then(
            Seq(
                App.localPut(Txn.sender(), Bytes("time"),
                             on_lock_appcall_tx_time),
                Approve()
            )
        ),
        Reject()
    )

    on_create_app_tinylock_asa_value = App.globalGetEx(
        Txn.applications[1], Bytes("tinylock_asa_id"))
    on_create_app_tinylock_fee_value = App.globalGetEx(
        Txn.applications[1], Bytes("tinylock_fee"))

    @Subroutine(TealType.none)
    def reconfigure_locker_fee(args_index: int):
        return Seq(
            on_create_app_tinylock_asa_value,
            on_create_app_tinylock_fee_value,
            If(
                Not(
                    And(
                        on_create_app_tinylock_asa_value.hasValue(),
                        on_create_app_tinylock_fee_value.hasValue()
                    )
                )
            ).Then(
                Reject()  # Tinylock Contract hasn't set asa and fee
            ),
            App.globalPut(Bytes("tinylock_locker_id"),
                      Txn.applications[1]  # Locker app id,
                      ),
            App.globalPut(Bytes("tinylock_locker_address"),
                      Txn.application_args[args_index])
        )

    on_create = Seq(
        reconfigure_locker_fee(Int(0)),
        Approve()
    )

    on_reconfigure = Seq(
        Assert(Txn.sender() == Global.creator_address()),
        reconfigure_locker_fee(Int(1)),
        Approve()
    )

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("lock"), on_lock],
        [on_call_method == Bytes("unlock"), on_unlock],
        [on_call_method == Bytes("relock"), on_relock],
        [on_call_method == Bytes("reconfigure"), on_reconfigure]
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
    with open("permlocker_approval.teal", "w") as f:
        compiled=compileTeal(
            approval_program(), mode = Mode.Application, version = 5)
        f.write(compiled)

    with open("permlocker_clear_state.teal", "w") as f:
        compiled=compileTeal(clear_state_program(),
                               mode = Mode.Application, version = 5)
        f.write(compiled)
