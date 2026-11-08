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
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_ui_subsystem main/led.c main/buttons.c main/state_machine.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/telemetry.c test/test_ui_subsystem.c -lm && /tmp/test_ui_subsystem
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_pca9685 main/pca9685.c test/test_pca9685.c -lm && /tmp/test_pca9685
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_storage main/storage.c test/test_storage.c && /tmp/test_storage
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_motion main/led.c main/pca9685.c main/storage.c main/motion.c test/test_motion.c -lm && /tmp/test_motion
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_state_machine main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_state_machine.c -lm && /tmp/test_state_machine
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_e2e_stress main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_e2e_stress.c -lm && /tmp/test_e2e_stress
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_ble_transport main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_ble_transport.c -lm && /tmp/test_ble_transport
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_remote_cmd main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_remote_cmd.c -lm && /tmp/test_remote_cmd
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_telemetry main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_telemetry.c -lm && /tmp/test_telemetry
	gcc -Wall -Wextra -Werror -I./main -o /tmp/test_ble_integration main/led.c main/buttons.c main/pca9685.c main/storage.c main/motion.c main/ble_transport.c main/remote_cmd.c main/state_machine.c main/telemetry.c test/test_ble_integration.c -lm && /tmp/test_ble_integration
