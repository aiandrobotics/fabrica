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
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_ui_subsystem main/led.c main/buttons.c test/test_ui_subsystem.c && /tmp/test_ui_subsystem
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_pca9685 main/pca9685.c test/test_pca9685.c -lm && /tmp/test_pca9685
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_storage main/storage.c test/test_storage.c && /tmp/test_storage

