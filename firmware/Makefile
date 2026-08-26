# Convenience Makefile for Fabrica ESP32 Firmware

.PHONY: all build flash monitor clean test

all: build

build:
	idf.py build

flash:
	idf.py flash

monitor:
	idf.py monitor

clean:
	idf.py fullclean

test:
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_headers test/test_headers.c && /tmp/test_headers
