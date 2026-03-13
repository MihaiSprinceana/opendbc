import unittest
from types import SimpleNamespace

from opendbc.car.lateral import apply_steer_angle_limits_vm
from opendbc.car.subaru.carcontroller import CarController
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.values import CAR


class TestSubaruCarController(unittest.TestCase):
  def test_lkas_angle_engages_with_vm_limits(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_CROSSTREK_2025)
    controller = CarController({}, CP)

    controller.apply_angle_last = 18.85

    cs = SimpleNamespace(out=SimpleNamespace(
      vEgoRaw=9.5,
      steeringAngleDeg=20.56,
    ))
    cc = SimpleNamespace(
      latActive=True,
      actuators=SimpleNamespace(steeringAngleDeg=19.86),
    )

    controller.handle_angle_lateral(cc, cs)

    expected = apply_steer_angle_limits_vm(
      cc.actuators.steeringAngleDeg,
      18.85,
      cs.out.vEgoRaw,
      cs.out.steeringAngleDeg,
      cc.latActive,
      controller.p,
      controller.VM,
    )

    self.assertAlmostEqual(controller.apply_angle_last, expected)

  def test_lkas_angle_holds_request_until_gap_is_legal(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_CROSSTREK_2025)
    controller = CarController({}, CP)

    controller.apply_angle_last = 0.0

    cs = SimpleNamespace(out=SimpleNamespace(
      vEgoRaw=9.5,
      steeringAngleDeg=20.56,
    ))
    cc = SimpleNamespace(
      latActive=True,
      actuators=SimpleNamespace(steeringAngleDeg=19.86),
    )

    msg = controller.handle_angle_lateral(cc, cs)
    expected = subarucan.create_steering_control_angle(controller.packer, cs.out.steeringAngleDeg, False)

    self.assertEqual(msg[0], expected[0])
    self.assertEqual(msg[2], expected[2])
    self.assertEqual(msg[1][5:], expected[1][5:])
    self.assertEqual(msg[1][1] & 0x10, 0)
    self.assertAlmostEqual(controller.apply_angle_last, cs.out.steeringAngleDeg)


if __name__ == "__main__":
  unittest.main()
