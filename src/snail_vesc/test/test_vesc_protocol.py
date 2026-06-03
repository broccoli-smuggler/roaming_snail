"""Unit tests for snail_vesc.vesc_protocol."""

import struct

import pytest

from snail_vesc import vesc_protocol as vp


@pytest.mark.parametrize('packet_id, vesc_id', [
    (vp.VescPacketId.SET_RPM, 1),
    (vp.VescPacketId.SET_POS, 5),
    (vp.VescPacketId.SET_CURRENT_BRAKE, vp.BROADCAST_ID),
    (vp.VescPacketId.STATUS_1, 17),
])
def test_frame_id_round_trip(packet_id, vesc_id):
    frame_id = vp.make_frame_id(int(packet_id), vesc_id)
    parsed_packet, parsed_vesc = vp.parse_frame_id(frame_id)
    assert parsed_packet == int(packet_id)
    assert parsed_vesc == vesc_id


def test_frame_id_layout():
    assert vp.make_frame_id(3, 1) == 0x0301
    assert vp.parse_frame_id(0x0301) == (3, 1)


def test_frame_id_broadcast():
    assert vp.make_frame_id(vp.VescPacketId.SET_RPM, vp.BROADCAST_ID) == 0x03FF


@pytest.mark.parametrize('bad_packet, bad_vesc', [
    (-1, 0),
    (256, 0),
    (0, -1),
    (0, 256),
])
def test_frame_id_out_of_range(bad_packet, bad_vesc):
    with pytest.raises(ValueError):
        vp.make_frame_id(bad_packet, bad_vesc)


def test_encode_set_rpm_positive():
    assert vp.encode_set_rpm(1000) == struct.pack('>i', 1000)


def test_encode_set_rpm_negative():
    (decoded,) = struct.unpack('>i', vp.encode_set_rpm(-5000))
    assert decoded == -5000


def test_encode_set_pos_90_degrees():
    (decoded,) = struct.unpack('>i', vp.encode_set_pos(90.0))
    assert decoded == 90_000_000


def test_encode_set_pos_fractional():
    (decoded,) = struct.unpack('>i', vp.encode_set_pos(0.5))
    assert decoded == 500_000


def test_encode_set_current_brake():
    (decoded,) = struct.unpack('>i', vp.encode_set_current_brake(10.0))
    assert decoded == 10_000


def test_encode_set_duty_max():
    (decoded,) = struct.unpack('>i', vp.encode_set_duty(1.0))
    assert decoded == 100_000


def test_encode_set_current():
    (decoded,) = struct.unpack('>i', vp.encode_set_current(1.234))
    assert decoded == 1234


def test_status_1_round_trip():
    encoded = vp.encode_status_1(erpm=1500, current_motor=12.3, duty=0.456)
    status = vp.decode_status_1(encoded)
    assert status.erpm == 1500
    assert status.current_motor == pytest.approx(12.3, abs=0.1)
    assert status.duty == pytest.approx(0.456, abs=0.001)


def test_status_1_negative_values():
    encoded = vp.encode_status_1(erpm=-2000, current_motor=-5.0, duty=-0.5)
    status = vp.decode_status_1(encoded)
    assert status.erpm == -2000
    assert status.current_motor == pytest.approx(-5.0)
    assert status.duty == pytest.approx(-0.5)


def test_status_4_round_trip():
    encoded = vp.encode_status_4(temp_fet=45.6, temp_motor=33.3, current_in=2.5, pid_pos=120.0)
    status = vp.decode_status_4(encoded)
    assert status.temp_fet == pytest.approx(45.6, abs=0.1)
    assert status.temp_motor == pytest.approx(33.3, abs=0.1)
    assert status.current_in == pytest.approx(2.5, abs=0.1)
    assert status.pid_pos == pytest.approx(120.0, abs=0.02)


def test_status_5_round_trip():
    encoded = vp.encode_status_5(tacho_value=123456, v_in=48.2)
    status = vp.decode_status_5(encoded)
    assert status.tacho_value == 123456
    assert status.v_in == pytest.approx(48.2, abs=0.1)


def test_decode_too_short_raises():
    with pytest.raises(ValueError):
        vp.decode_status_1(b'\x00\x00')
    with pytest.raises(ValueError):
        vp.decode_status_4(b'')
    with pytest.raises(ValueError):
        vp.decode_status_5(b'\x00' * 7)
