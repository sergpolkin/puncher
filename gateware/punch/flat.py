from migen import *

from litex.gen import *

from litex.soc.integration.soc_core import *
from litex.soc.interconnect import stream

from migen.genlib.misc import WaitTimer

from .send import Send


class Punch(LiteXModule):
    def __init__(self, pads_reset, pads, depth=128):
        self.sink   = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])

        # # #

        start = Signal()
        reset = Signal(reset=1)
        wait = Signal()
        last = Signal()

        sel = Signal(max=len(pads))

        self.submodules.send = send = Send()
        self.comb += send.source.connect(self.source)

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
                NextValue(last, 0),
                NextState("SEND")
            )
        )
        fsm.act("SEND",
            send.en.eq(1),
            If(send.done,
                NextValue(sel, sel + 1),
                If(last,
                    NextState("IDLE")
                ).Elif((sel + 1) == len(pads),
                    NextValue(last, 1),
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
                fifo.source.connect(send.sink),
            ]

        self.comb += Case(sel, cases)
