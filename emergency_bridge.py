#!/usr/bin/env python3
"""
Emergency Bridge - Offline-only consent-state machine and command parser.

Hard boundaries (no exceptions):
- NO live Jitsi connections
- NO audio capture/recording/transcription
- NO networking (no sockets, no HTTP, no WebSockets)
- NO external process spawning (no subprocess, no os.system)
- NO file I/O beyond reading this source file for self-test

All actions are stubs that explicitly refuse the above.
"""

from __future__ import annotations
import sys
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable


class ConsentState(Enum):
    """Consent state machine states."""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class Command(Enum):
    """Supported commands."""
    CONSENT = "consent"
    TRANSCRIBE = "transcribe"
    SUMMARY = "summary"
    SPEAK = "speak"
    LEAVE = "leave"


@dataclass
class ConsentContext:
    """Holds consent state and metadata (offline only)."""
    state: ConsentState = ConsentState.PENDING
    user_id: Optional[str] = None
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedCommand:
    """Result of parsing a command line."""
    command: Command
    args: List[str]
    raw: str


# =============================================================================
# HARD REFUSAL STUBS - These explicitly refuse prohibited operations
# =============================================================================

def refuse_jitsi() -> str:
    """Refuse any live Jitsi connection attempt."""
    return "REFUSED: Live Jitsi connections are prohibited (offline-only mode)."


def refuse_audio_capture() -> str:
    """Refuse any audio capture/recording/transcription attempt."""
    return "REFUSED: Audio capture, recording, and transcription are prohibited (offline-only mode)."


def refuse_networking() -> str:
    """Refuse any networking attempt."""
    return "REFUSED: Networking (sockets, HTTP, WebSockets) is prohibited (offline-only mode)."


def refuse_external_process() -> str:
    """Refuse any external process spawning attempt."""
    return "REFUSED: External process spawning (subprocess, os.system) is prohibited (offline-only mode)."


def refuse_file_io(operation: str) -> str:
    """Refuse file I/O beyond reading this source for self-test."""
    return f"REFUSED: File I/O '{operation}' is prohibited (offline-only mode; only self-test source read allowed)."


# =============================================================================
# COMMAND HANDLERS - All stubs that call refusal functions
# =============================================================================

def handle_consent(ctx: ConsentContext, args: List[str]) -> str:
    """Handle /consent command - stub only."""
    if ctx.state == ConsentState.GRANTED:
        return "Consent already granted."
    if ctx.state == ConsentState.DENIED:
        return "Consent previously denied; use /consent grant to override."
    if not args:
        return "Usage: /consent [grant|deny|status]"
    action = args[0].lower()
    if action == "grant":
        ctx.state = ConsentState.GRANTED
        ctx.granted_at = "offline-timestamp"
        return "Consent GRANTED (offline stub)."
    elif action == "deny":
        ctx.state = ConsentState.DENIED
        return "Consent DENIED (offline stub)."
    elif action == "status":
        return f"Consent state: {ctx.state.value}"
    else:
        return f"Unknown consent action: {action}. Use grant, deny, or status."


def handle_transcribe(ctx: ConsentContext, args: List[str]) -> str:
    """Handle /transcribe command - stub that refuses audio operations."""
    if ctx.state != ConsentState.GRANTED:
        return "Consent required. Use /consent grant first."
    # Explicitly refuse audio capture/transcription
    return refuse_audio_capture()


def handle_summary(ctx: ConsentContext, args: List[str]) -> str:
    """Handle /summary command - stub that refuses networking/external process."""
    if ctx.state != ConsentState.GRANTED:
        return "Consent required. Use /consent grant first."
    # Explicitly refuse networking and external process for summary generation
    return refuse_networking() + " " + refuse_external_process()


def handle_speak(ctx: ConsentContext, args: List[str]) -> str:
    """Handle /speak command - stub that refuses Jitsi/audio/networking."""
    if ctx.state != ConsentState.GRANTED:
        return "Consent required. Use /consent grant first."
    # Explicitly refuse Jitsi, audio, and networking
    return refuse_jitsi() + " " + refuse_audio_capture() + " " + refuse_networking()


def handle_leave(ctx: ConsentContext, args: List[str]) -> str:
    """Handle /leave command - stub that revokes consent."""
    ctx.state = ConsentState.REVOKED
    ctx.revoked_at = "offline-timestamp"
    return "Left session. Consent REVOKED (offline stub)."


# Command handler registry
HANDLERS: Dict[Command, Callable[[ConsentContext, List[str]], str]] = {
    Command.CONSENT: handle_consent,
    Command.TRANSCRIBE: handle_transcribe,
    Command.SUMMARY: handle_summary,
    Command.SPEAK: handle_speak,
    Command.LEAVE: handle_leave,
}


# =============================================================================
# COMMAND PARSER
# =============================================================================

COMMAND_PATTERN = re.compile(r"^/(?P<cmd>\w+)(?:\s+(?P<args>.+))?$")


def parse_command(line: str) -> Optional[ParsedCommand]:
    """Parse a command line into a ParsedCommand."""
    line = line.strip()
    if not line:
        return None
    match = COMMAND_PATTERN.match(line)
    if not match:
        return None
    cmd_str = match.group("cmd").lower()
    args_str = match.group("args") or ""
    args = args_str.split() if args_str else []
    try:
        command = Command(cmd_str)
    except ValueError:
        return None
    return ParsedCommand(command=command, args=args, raw=line)


# =============================================================================
# MAIN INTERPRETER LOOP (offline, for self-test only)
# =============================================================================

def run_interpreter(commands: List[str]) -> List[str]:
    """Run a list of commands through the interpreter (offline, for testing)."""
    ctx = ConsentContext()
    results = []
    for line in commands:
        parsed = parse_command(line)
        if parsed is None:
            results.append(f"Parse error: {line}")
            continue
        handler = HANDLERS.get(parsed.command)
        if handler is None:
            results.append(f"Unknown command: {parsed.command.value}")
            continue
        try:
            result = handler(ctx, parsed.args)
        except Exception as e:
            result = f"Handler error: {e}"
        results.append(result)
    return results


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test() -> bool:
    """Run built-in self-test. Returns True if all tests pass."""
    test_cases = [
        # (input_commands, expected_outputs_contain)
        (
            ["/consent status", "/consent grant", "/consent status"],
            ["pending", "GRANTED", "granted"]
        ),
        (
            ["/transcribe"],
            ["Consent required"]
        ),
        (
            ["/consent grant", "/transcribe"],
            ["REFUSED: Audio capture"]
        ),
        (
            ["/consent grant", "/summary"],
            ["REFUSED: Networking", "REFUSED: External process"]
        ),
        (
            ["/consent grant", "/speak"],
            ["REFUSED: Live Jitsi", "REFUSED: Audio capture", "REFUSED: Networking"]
        ),
        (
            ["/consent grant", "/leave", "/consent status"],
            ["REVOKED", "revoked"]
        ),
        (
            ["/consent deny", "/transcribe"],
            ["Consent required"]
        ),
        (
            ["/unknown"],
            ["Parse error"]
        ),
        (
            [""],
            ["Parse error"]
        ),
    ]

    all_passed = True
    for i, (inputs, expected_substrings) in enumerate(test_cases):
        outputs = run_interpreter(inputs)
        # Check each expected substring appears in at least one output
        for substr in expected_substrings:
            found = any(substr.lower() in out.lower() for out in outputs)
            if not found:
                print(f"FAIL Test {i+1}: Expected substring '{substr}' not found in outputs: {outputs}")
                all_passed = False

    if all_passed:
        print("All self-tests PASSED.")
    else:
        print("Some self-tests FAILED.")
    return all_passed


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        success = self_test()
        sys.exit(0 if success else 1)
    else:
        print("Emergency Bridge - Offline-only consent-state machine")
        print("Usage: python emergency_bridge.py --self-test")
        print("Commands: /consent [grant|deny|status]  /transcribe  /summary  /speak  /leave")
        print("All operations are stubs that refuse: Jitsi, audio, networking, external processes.")