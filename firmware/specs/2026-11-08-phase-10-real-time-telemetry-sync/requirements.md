# Requirements: Phase 10 — Real-Time Telemetry & Button Configuration Sync

## Scope
Phase 10 implements the continuous, adaptive real-time telemetry streaming subsystem (`telemetry.c` / `telemetry.h`) and live progress tracking across the Core 0 motion engine, state machine, and Core 1 NimBLE GATT server. It provides mobile applications with smooth, high-fidelity visual representations of origami folding progress, live flap articulation angles, and button sequence synchronization.

## Decisions

### 1. Adaptive Streaming Rates & Power Management
- **High-Rate (10 Hz / 100ms)**: Active when the robot is in `STATE_RUNNING_MOTION` or `STATE_CALIBRATING`. Emits 31-byte telemetry notifications every 100ms to allow mobile apps to render smooth 10 Hz progress bars and 3D/2D flap animations.
- **Low-Rate (1 Hz / 1000ms)**: Active when the robot is in `STATE_IDLE_RUN`, `STATE_ESTOP`, or `STATE_ERROR`. Throttles telemetry to 1 notification per second to conserve connected phone battery and avoid iOS `CoreBluetooth` background notification rate-limiting.
- **Event-Driven Immediate Push**: State transitions (`STATE_IDLE_RUN` $\leftrightarrow$ `STATE_RUNNING_MOTION`, `STATE_ESTOP`), command status results, 100% routine completion, and button sequence updates bypass the periodic timer and immediately push an updated packet.

### 2. Streaming Control & CCCD Binding Policy
- **CCCD Gate**: Periodic telemetry streaming is strictly gated on the central having written `0x0001` to the `FAB2` Client Characteristic Configuration Descriptor (`0x2902`).
- **Auto-Stream on Connect**: Once CCCD is subscribed, periodic streaming is enabled by default (`stream_enabled = true`).
- **Opcode 0x11 Stream Control**: Centrals can pause streaming by sending `CMD_SET_TELEMETRY_STREAM` with `0x00` (`[0x11][0x00]`) or resume with `0x01` (`[0x11][0x01]`).
- **Disconnect Safety**: On central disconnection (`BLE_GAP_EVENT_DISCONNECT`), periodic streaming immediately pauses, preventing unnecessary FreeRTOS notification attempts.

### 3. Real-Time Mid-Sweep Progress & Angle Tracking
- **Elapsed Step Time**: `motion.c` tracks monotonic step start timestamps via `esp_timer_get_time()`, calculating `elapsed_step_time_ms` throughout the sweep and dwell periods.
- **Progress Calculation**: `step_progress_pct` is computed dynamically as $\min(100, \frac{\text{elapsed\_ms}}{\text{total\_step\_duration\_ms}} \times 100)$.
- **Live Servo Angles**: `channel_angles[16]` dynamically reflects the commanded angles from `pca9685_get_channel_angle()` for all 16 channels, updating in real time as servos are moved.

### 4. Telemetry Frame Wire Serialization
- Packed 31-byte binary struct (`telemetry_packet_t`, `__attribute__((packed))`, zero compiler padding):
  - `system_state` (`uint8_t`, offset 0)
  - `led_state` (`uint8_t`, offset 1)
  - `active_button_id` (`uint8_t`, offset 2)
  - `current_step_idx` (`uint8_t`, offset 3)
  - `total_steps` (`uint8_t`, offset 4)
  - `step_progress_pct` (`uint8_t`, offset 5)
  - `elapsed_step_time_ms` (`uint16_t`, Little-Endian, offsets 6-7)
  - `channel_angles[16]` (`uint8_t[16]`, offsets 8-23)
  - `last_cmd_status` (`uint8_t`, offset 24)
  - `free_heap_kb` (`uint16_t`, Little-Endian, offsets 25-26)
  - `ble_rssi_dbm` (`int8_t`, offset 27)
  - `error_code` (`uint8_t`, offset 28)
  - `sequence_counter` (`uint16_t`, Little-Endian, offsets 29-30)

## Constraints
1. **Core 1 Placement**: The telemetry task (`app_telem_task`) must run on Core 1 with Priority 3 and stack size $\le 3072$ bytes, ensuring zero preemption or timing jitter on Core 0 real-time servo trajectory execution.
2. **Deterministic Preemption Latency**: Querying motion progress must be non-blocking and lock-free (or acquire existing fast mutexes) so telemetry queries never stall Core 0 motion stepping or Core 1 BLE command ingestion.
3. **Strict Little-Endian Wire Encoding**: Multi-byte fields (`elapsed_step_time_ms`, `free_heap_kb`, `sequence_counter`) must be Little-Endian on the wire.

## Non-goals
- Audio output or speaker beeps.
- Battery gauge ADC voltage sensing (Fabrica is wall/bench-powered via 5V/10A external supply).
- Wi-Fi or MQTT telemetry streaming (local Bluetooth Low Energy only).
- Non-standard telemetry packet resizing (the 31-byte frame size is immutable).

## Context
Phase 8 established the NimBLE GATT server with `FAB1`, `FAB2`, and `FAB3` characteristics, and Phase 9 implemented command ingress, raw routine execution, latched E-Stop, and live servo calibration. Phase 10 provides the dedicated background periodic streaming engine that binds these subsystems into a continuous real-time telemetry stream.
