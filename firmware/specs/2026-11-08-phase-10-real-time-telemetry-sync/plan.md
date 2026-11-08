# Plan: Phase 10 — Real-Time Telemetry & Button Configuration Sync

## Task Group 1: Motion Progress Hooks & Mid-Sweep Interpolation
1. **Extend Motion State Interface (`main/motion.h`, `main/motion.c`)**:
   - Expose thread-safe progress query APIs: `motion_get_progress(uint8_t *out_step_idx, uint8_t *out_total_steps, uint8_t *out_progress_pct, uint16_t *out_elapsed_ms)`.
   - Track step start timestamp (`int64_t step_start_time_us` via `esp_timer_get_time()`) and total calculated step duration (sweep time + dwell time) inside `motion_execute_step()`.
   - Implement real-time progress percentage calculation ($0\dots 100\%$) and elapsed time tracking in milliseconds throughout the active sweep and dwell loop.
   - Update `remote_cmd_get_progress_snapshot()` in `main/remote_cmd.c` to delegate directly to `motion_get_progress()` during active motion execution.

## Task Group 2: FreeRTOS Adaptive Streaming Task & Stream Control
1. **Define Telemetry Subsystem Header (`main/telemetry.h`)**:
   - Define subsystem lifecycle functions: `esp_err_t telemetry_init(void)`, `void telemetry_start(void)`, `void telemetry_stop(void)`.
   - Define streaming control APIs: `void telemetry_set_stream_enabled(bool enabled)`, `bool telemetry_is_stream_enabled(void)`.
   - Define rate query and tick helpers: `uint32_t telemetry_get_current_interval_ms(void)`.
2. **Implement Adaptive Streaming Engine (`main/telemetry.c`)**:
   - Spawn `app_telem_task` pinned to **Core 1** (Priority 3, 3072 bytes stack) in `telemetry_init()`.
   - Implement adaptive sleep loop:
     - Sleep interval = 100ms (10 Hz) when `state_machine_get_state()` is `STATE_RUNNING_MOTION` or `STATE_CALIBRATING`.
     - Sleep interval = 1000ms (1 Hz) when `state_machine_get_state()` is `STATE_IDLE_RUN`, `STATE_ESTOP`, or `STATE_ERROR`.
   - Enforce streaming gate policy:
     - Only emit `ble_transport_notify_telemetry()` if connected, `FAB2` CCCD is subscribed (`ble_transport_is_telemetry_subscribed()`), and periodic streaming is enabled (`telemetry_is_stream_enabled()`).
     - Default streaming enabled when CCCD is subscribed; mute immediately upon central disconnect.
3. **Integrate Stream Control Opcode 0x11 (`main/remote_cmd.c`, `main/ble_transport.c`)**:
   - Hook `CMD_SET_TELEMETRY_STREAM` (`0x11`) in `remote_cmd.c` to call `telemetry_set_stream_enabled(enable)`.
   - Update `ble_transport_build_telemetry()` to pull `elapsed_step_time_ms` from `motion_get_progress()`.
4. **Firmware Initialization & Build Integration (`main/main.c`, `main/CMakeLists.txt`)**:
   - Add `telemetry.c` to `main/CMakeLists.txt` SRCS.
   - Initialize `telemetry_init()` on Core 1 in `app_main()` following BLE transport setup.

## Task Group 3: Unit Test Suite & Build Verification
1. **Create Host Unit Test Suite (`test/test_telemetry.c`)**:
   - Implement mock FreeRTOS timer / clock stepping harness for unit tests without hardware delays.
   - Verify packed 31-byte struct memory alignment, offsets, and Little-Endian encoding of multi-byte fields (`elapsed_step_time_ms`, `free_heap_kb`, `sequence_counter`).
   - Verify adaptive interval calculation: 100ms in `STATE_RUNNING_MOTION` and `STATE_CALIBRATING` vs 1000ms in `STATE_IDLE_RUN`, `STATE_ESTOP`, and `STATE_ERROR`.
   - Verify sequence counter monotonically increments across successive telemetry packets.
   - Verify live 16-channel servo angle tracking mirrors `pca9685_get_channel_angle()`.
   - Verify streaming enable/disable gating with CCCD status and disconnect mute behavior.
2. **Build and Test Execution**:
   - Update `Makefile` to include `test/test_telemetry.c` in `make test`.
   - Verify all host tests pass cleanly (`make test`).
   - Verify target ESP-IDF compilation succeeds with zero errors and zero warnings (`idf.py build`).
