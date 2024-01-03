#!/usr/bin/env python3

from migen import *

from litex.gen import *

from platforms import sipeed_tang_nano_1k

from litex.soc.cores.clock.gowin_gw1n import GW1NPLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex.soc.interconnect import stream
from litex.soc.cores import uart

from gateware.punch.flat import Punch


# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq):
        self.cd_sys = ClockDomain()
        clk = platform.request("clk27")

        # PLL.
        self.pll = pll = GW1NPLL(devicename=platform.devicename, device=platform.device)
        pll.register_clkin(clk, 27e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)


# SoC ----------------------------------------------------------------------------------------------

class SoC(SoCMini):
    def __init__(self, sys_clk_freq=66e6, **kwargs):
        platform = sipeed_tang_nano_1k.Platform()

        self.submodules.crg = _CRG(platform, sys_clk_freq)

        kwargs["cpu_type"] = "None"
        kwargs["integrated_sram_size"] = 0
        kwargs["with_uart"] = False
        kwargs["with_timer"] = False
        SoCMini.__init__(self, platform, sys_clk_freq, **kwargs)

        # UART
        serial = platform.request("serial")
        self.submodules.uart = uart.RS232PHY(serial, sys_clk_freq)

        # LED
        led = platform.request("user_led", 0)
        self.sync += If(self.uart.source.valid, led.eq(~led))

        # Punch
        cap_reset = platform.request("cap_reset")
        cap_pads = platform.request("cap")
        self.submodules.punch = Punch(cap_reset, cap_pads, sys_clk_freq)
        self.comb += self.uart.source.connect(self.punch.sink)
        self.comb += [
            self.uart.source.connect(self.punch.sink),
            self.punch.source.connect(self.uart.sink),
        ]


def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=sipeed_tang_nano_1k.Platform, description="LiteX SoC on Tang Nano 1k.")
    parser.add_target_argument("--flash", action="store_true", help="Flash Bitstream.")
    args = parser.parse_args()

    soc = SoC(
        **parser.soc_argdict
    )

    builder = Builder(soc, **parser.builder_argdict)

    builder.compile_gateware = True if args.build else False
    builder.build(**parser.toolchain_argdict)

    if args.flash:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
