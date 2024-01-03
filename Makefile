gateware = ./build/sipeed_tang_nano_1k/gateware/sipeed_tang_nano_1k.v
firmware = $(patsubst %.v,%.fs,$(gateware))

deps = \
	main.py \
	gateware/punch/flat.py \
	gateware/punch/send.py \
	platforms/sipeed_tang_nano_1k.py

all: $(gateware)

build: $(firmware)

flash: .FORCE
	./main.py --build --flash

.FORCE:

$(firmware): %.fs: $(deps)
	./main.py --build

$(gateware): %.v: $(deps)
	./main.py

.PHONY: build
