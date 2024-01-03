from migen import *

from litex.gen import *

from litex.soc.integration.soc_core import *
from litex.soc.interconnect import stream


class Send(LiteXModule):
    def __init__(self):
        self.sink   = stream.Endpoint([("data", 1)])
        self.source = stream.Endpoint([("data", 8)])

        self.en   = Signal()
        self.done = Signal()

        # # #

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            self.sink.ready.eq(self.en),
            If(self.en,
                If(self.sink.valid,
                    NextValue(self.source.data,
                        Mux(self.sink.data, ord('1'), ord('_'))
                    ),
                    NextState("DATA")
                ).Else(
                    NextValue(self.source.data, ord('\r')),
                    NextState("CR")
                )
            )
        )
        fsm.act("DATA",
            self.source.valid.eq(1),
            If(self.source.ready,
                NextState("IDLE")
            )
        )
        fsm.act("CR",
            self.source.valid.eq(1),
            If(self.source.ready,
                NextValue(self.source.data, ord('\n')),
                NextState("LF")
            )
        )
        fsm.act("LF",
            self.source.valid.eq(1),
            If(self.source.ready,
                self.done.eq(1),
                NextState("IDLE")
            )
        )
