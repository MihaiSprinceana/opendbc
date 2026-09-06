import unittest

from opendbc.car.subaru.fingerprints import FW_VERSIONS


class TestSubaruFingerprint(unittest.TestCase):
  def test_fw_version_format(self):
    for platform, fws_per_ecu in FW_VERSIONS.items():
      for (ecu, _, _), fws in fws_per_ecu.items():
        fw_size = len(fws[0])
        for fw in fws:
          assert len(fw) == fw_size, f"{platform} {ecu}: {len(fw)} {fw_size}"


class TestSubaruSetSpeedExpBuilder(unittest.TestCase):
  """EXPERIMENT (throwaway): create_es_distance can add a single button bit with throttle passed through."""

  def setUp(self):
    from opendbc.can import CANPacker
    from opendbc.car import Bus
    from opendbc.car.subaru.values import CAR, DBC
    self.packer = CANPacker(DBC[CAR.SUBARU_CROSSTREK_2025][Bus.pt])
    self.es = {s: 0 for s in ["CHECKSUM", "COUNTER", "Signal1", "Cruise_Fault", "Cruise_Throttle", "Signal2", "Car_Follow",
                              "Low_Speed_Follow", "Cruise_Soft_Disable", "Signal7", "Cruise_Brake_Active", "Distance_Swap",
                              "Cruise_EPB", "Signal4", "Close_Distance", "Signal5", "Cruise_Cancel", "Cruise_Set",
                              "Cruise_Resume", "Signal6"]}
    self.es["Cruise_Throttle"] = 7500
    self.es["Cruise_Resume"] = 1  # a stale camera bit that must not leak into our frame

  def test_set_button_passes_throttle_through(self):
    from opendbc.car.subaru import subarucan
    from opendbc.car.subaru.values import CanBus
    addr, dat, bus = subarucan.create_es_distance(self.packer, 3, self.es, CanBus.alt, False, button="Cruise_Set")
    assert addr == 0x221 and bus == CanBus.alt
    assert (int.from_bytes(dat[2:4], "little") & 0x1FFF) == 7500
    assert dat[7] & 0x7 == 0b010, f"expected only Cruise_Set, got bits {dat[7] & 0x7:03b}"

  def test_resume_button(self):
    from opendbc.car.subaru import subarucan
    from opendbc.car.subaru.values import CanBus
    _, dat, _ = subarucan.create_es_distance(self.packer, 3, self.es, CanBus.alt, False, button="Cruise_Resume")
    assert dat[7] & 0x7 == 0b100
