"""VESC CAN protocol — encoder / decoder for the packets the Snail uses.

VESC firmware exposes a CAN protocol where each frame is identified by a 29-bit
extended ID composed of:

    bits  0..7 : target VESC ID (0..254), or 255 for broadcast
    bits  8..15: packet ID (the command / status code)

All multi-byte payload fields are big-endian (network byte order).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple


class VescPacketId(IntEnum):
    """Subset of CAN_PACKET_* identifiers used by the Snail."""

    SET_DUTY = 0
    SET_CURRENT = 1
    SET_CURRENT_BRAKE = 2
    SET_RPM = 3
    SET_POS = 4
    STATUS_1 = 9
    STATUS_4 = 16
    STATUS_5 = 27


BROADCAST_ID = 255


def make_frame_id(packet_id: int, vesc_id: int) -> int:
    if not 0 <= packet_id <= 0xFF:
        raise ValueError('packet_id out of range: {}'.format(packet_id))
    if not 0 <= vesc_id <= 0xFF:
        raise ValueError('vesc_id out of range: {}'.format(vesc_id))
    return (packet_id << 8) | vesc_id


def parse_frame_id(frame_id: int) -> Tuple[int, int]:
    """Returns (packet_id, vesc_id)."""
    return (frame_id >> 8) & 0xFF, frame_id & 0xFF


def encode_set_duty(duty: float) -> bytes:
    """duty must be in [-1.0, 1.0]."""
    return struct.pack('>i', int(round(duty * 100_000)))


def encode_set_current(current_amperes: float) -> bytes:
    return struct.pack('>i', int(round(current_amperes * 1000)))


def encode_set_current_brake(current_amperes: float) -> bytes:
    """current_amperes must be positive."""
    return struct.pack('>i', int(round(current_amperes * 1000)))


def encode_set_rpm(electrical_rpm: int) -> bytes:
    """Pass electrical RPM, not mechanical. Mechanical RPM = electrical_rpm / pole_pairs."""
    return struct.pack('>i', int(electrical_rpm))


def encode_set_pos(position_degrees: float) -> bytes:
    return struct.pack('>i', int(round(position_degrees * 1_000_000)))


@dataclass
class Status1:
    """STATUS_1: high-rate motor state."""

    erpm: int             # electrical RPM
    current_motor: float  # A
    duty: float           # -1.0..1.0


@dataclass
class Status4:
    """STATUS_4: temperatures, input current, PID position."""

    temp_fet: float    # °C
    temp_motor: float  # °C
    current_in: float  # A
    pid_pos: float     # degrees


@dataclass
class Status5:
    """STATUS_5: tachometer and input voltage."""

    tacho_value: int  # raw electrical tacho count
    v_in: float       # V


def decode_status_1(data: bytes) -> Status1:
    if len(data) < 8:
        raise ValueError('STATUS_1 payload too short: {} bytes'.format(len(data)))
    erpm, current_x10, duty_x1000 = struct.unpack('>ihh', data[:8])
    return Status1(
        erpm=erpm,
        current_motor=current_x10 / 10.0,
        duty=duty_x1000 / 1000.0,
    )


def decode_status_4(data: bytes) -> Status4:
    if len(data) < 8:
        raise ValueError('STATUS_4 payload too short: {} bytes'.format(len(data)))
    temp_fet_x10, temp_motor_x10, current_in_x10, pid_pos_x50 = struct.unpack(
        '>hhhh', data[:8]
    )
    return Status4(
        temp_fet=temp_fet_x10 / 10.0,
        temp_motor=temp_motor_x10 / 10.0,
        current_in=current_in_x10 / 10.0,
        pid_pos=pid_pos_x50 / 50.0,
    )


def decode_status_5(data: bytes) -> Status5:
    if len(data) < 8:
        raise ValueError('STATUS_5 payload too short: {} bytes'.format(len(data)))
    tacho, v_in_x10, _reserved = struct.unpack('>ihh', data[:8])
    return Status5(
        tacho_value=tacho,
        v_in=v_in_x10 / 10.0,
    )


def encode_status_1(erpm: int, current_motor: float, duty: float) -> bytes:
    return struct.pack(
        '>ihh',
        int(erpm),
        int(round(current_motor * 10)),
        int(round(duty * 1000)),
    )


def encode_status_4(temp_fet: float, temp_motor: float, current_in: float, pid_pos: float) -> bytes:
    return struct.pack(
        '>hhhh',
        int(round(temp_fet * 10)),
        int(round(temp_motor * 10)),
        int(round(current_in * 10)),
        int(round(pid_pos * 50)),
    )


def encode_status_5(tacho_value: int, v_in: float) -> bytes:
    return struct.pack(
        '>ihh',
        int(tacho_value),
        int(round(v_in * 10)),
        0,
    )
