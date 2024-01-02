#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# Board diagram/pinout:
# https://dl.sipeed.com/fileList/TANG/Nano%201K/2_Schematic/Tang%20nano-6100_Schematic.pdf

from migen import *

from litex.build.generic_platform import *
from litex.build.gowin.platform import GowinPlatform
from litex.build.openfpgaloader import OpenFPGALoader

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk27",  0, Pins("47"), IOStandard("LVCMOS33")),

    # Leds
    ("user_led", 0, Pins("10"),  IOStandard("LVCMOS33")), # blue
    ("user_led", 1, Pins("9"),   IOStandard("LVCMOS33")), # red
    ("user_led", 2, Pins("11"),  IOStandard("LVCMOS33")), # green

    # Buttons.
    ("user_btn", 0, Pins("13"),  IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("44"),  IOStandard("LVCMOS33")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("41")),
        Subsignal("rx", Pins("40")),
        IOStandard("LVCMOS33")
    ),
]

# Connectors ---------------------------------------------------------------------------------------

_connectors = []

_cap = [
    ("cap_reset", 0, Pins("34"), IOStandard("LVCMOS33")),
    ("cap", 0,
        Subsignal("clk", Pins("20")),
        Subsignal("rdy", Pins("19")),
        Subsignal("in0", Pins("29")),
        IOStandard("LVCMOS33")
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(GowinPlatform):
    default_clk_name   = "clk27"
    default_clk_period = 1e9/27e6

    def __init__(self, toolchain="gowin"):
        GowinPlatform.__init__(self, "GW1NZ-LV1QN48C6/I5", _io, _connectors, toolchain=toolchain, devicename="GW1NZ-1")
        self.add_extension(_cap)

    def create_programmer(self):
        return OpenFPGALoader("tangnano")

    def do_finalize(self, fragment):
        GowinPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk27", loose=True), 1e9/27e6)
