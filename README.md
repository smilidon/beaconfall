# Emergency Bridge

Offline-only consent-state machine and command parser for `/consent`, `/transcribe`, `/summary`, `/speak`, `/leave`.

## Hard Boundaries (No Exceptions)

This code **explicitly refuses** and **cannot perform**:

| Prohibited Operation | Refusal Function | Triggered By |
|---------------------|------------------|--------------|
| Live Jitsi connections | `refuse_jitsi()` | `/speak` |
| Audio capture/recording/transcription | `refuse_audio_capture()` | `/transcribe`, `/speak` |
| Networking (sockets, HTTP, WebSockets) | `refuse_networking()` | `/summary`, `/speak` |
| External process spawning (subprocess, os.system) | `refuse_external_process()` | `/summary` |
| File I/O (beyond reading this source for self-test) | `refuse_file_io()` | Any attempt |

All command handlers are **stubs** that immediately return refusal messages. No live functionality exists.

## Files

- `emergency_bridge.py` — Single-file implementation (stdlib only)
- `README.md` — This file

## Requirements

- Python 3.8+ (stdlib only, no dependencies)

## Running the Self-Test

```bash
python -m py_compile emergency_bridge.py
python emergency_bridge.py --self-test
```

### Expected Output

```
All self-tests PASSED.
```

The self-test verifies:
1. Consent state machine: pending → granted → revoked
2. `/transcribe` refuses audio capture
3. `/summary` refuses networking and external processes
4. `/speak` refuses Jitsi, audio, and networking
5. `/leave` revokes consent
6. Unknown commands and empty input are handled

## Command Syntax

```
/consent [grant|deny|status]   # Manage consent state
/transcribe                    # Refused: audio capture
/summary                       # Refused: networking + external process
/speak                         # Refused: Jitsi + audio + networking
/leave                         # Revoke consent
```

## Design

- **ConsentContext** — Dataclass holding state (PENDING, GRANTED, DENIED, REVOKED)
- **ParsedCommand** — Result of parsing `/command args`
- **HANDLERS** — Registry mapping Command enum to handler functions
- **Refusal functions** — Explicit, auditable refusal messages for each prohibited operation
- **run_interpreter()** — Offline interpreter for self-test (no I/O, no networking)
- **self_test()** — Built-in test suite run via `--self-test` flag

## No Configuration, No Environment Variables, No External Dependencies

This is a single-file, zero-dependency, offline-only scaffold.
## Project direction

Beaconfall is planned as an emergency-coordination companion for the End of the World Bot. This initial scaffold intentionally contains no live conferencing, audio capture, recording, transcription, networking, or process execution.
