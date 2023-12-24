from migen import *

from litex.gen import *

from litex.soc.integration.soc_core import *
from litex.soc.interconnect import stream

from migen.genlib.misc import WaitTimer


class Punch(LiteXModule):
    def __init__(self, pads_reset, pads, depth=128):
        self.sink   = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])

        # # #

        start = Signal()
        reset = Signal(reset=1)
        wait = Signal()

        sel = Signal(max=len(pads))

        send = stream.Endpoint([("data", 8)])
        send_done = Signal()

        timer = WaitTimer(depth)
        self.submodules += timer

        self.sync += timer.wait.eq(wait)

        self.comb += start.eq(self.sink.valid & (self.sink.data == ord('1')))

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(start,
                NextState("WAIT")
            )
        )
        fsm.act("WAIT",
            reset.eq(0),
            wait.eq(1),
            If(timer.wait & timer.done,
                wait.eq(0),
                NextValue(sel, 0),
                NextValue(send_done, 0),
                NextState("SEND")
            )
        )
        fsm.act("SEND",
            send.ready.eq(1),
            If(send.valid,
                NextValue(self.source.data,
                    Mux(send.data, ord('1'), ord('_'))
                ),
                NextState("SEND-WAIT")
            ).Else(
                NextValue(self.source.data, ord('\r')),
                NextState("CR")
            )
        )
        fsm.act("SEND-WAIT",
            self.source.valid.eq(1),
            If(self.source.ready,
                NextState("SEND")
            )
        )
        fsm.act("CR",
            self.source.valid.eq(1),
            If(self.source.ready,
                self.source.valid.eq(1),
                NextValue(self.source.data, ord('\n')),
                NextState("LF")
            )
        )
        fsm.act("LF",
            self.source.valid.eq(1),
            If(self.source.ready,
                NextValue(sel, sel + 1),
                If(send_done,
                    NextState("IDLE")
                ).Elif((sel + 1) == len(pads),
                    NextValue(send_done, 1),
                    NextValue(self.source.data, ord('\r')),
                    NextState("CR")
                ).Else(
                    NextState("SEND")
                )
            )
        )

        self.comb += pads_reset.eq(~reset)

        pads_buf = Signal(len(pads))
        self.sync += pads_buf.eq(Cat(pads.flatten()))

        cases = {}
        for s in range(len(pads_buf)):
            fifo = stream.SyncFIFO([("data", 1)], depth)
            self.submodules += fifo

            self.comb += fifo.sink.valid.eq(timer.wait)
            self.comb += fifo.sink.data.eq(pads_buf[s])

            cases[s] = [
                fifo.source.connect(send),
            ]

        self.comb += Case(sel, cases)
