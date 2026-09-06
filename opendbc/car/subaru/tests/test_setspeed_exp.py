import unittest

from opendbc.car.subaru.setspeed_exp import SetSpeedExperiment

# frames are 100 Hz
PERIOD, PRESS, SETTLE, MAX = 1000, 15, 500, 3
OK = dict(enabled=True, cruise_enabled=True, cancel=False, v_ego=20.0, brake=False, gas=False, camera_buttons_active=False)


def run(exp, start, n, **overrides):
  out = []
  for f in range(start, start + n):
    out.append(exp.update(f, **{**OK, **overrides}))
  return out


class TestSetSpeedExperiment(unittest.TestCase):
  def setUp(self):
    self.exp = SetSpeedExperiment("Cruise_Set", period_frames=PERIOD, press_frames=PRESS, settle_frames=SETTLE,
                                  min_speed=10.0, max_presses=MAX)

  def test_no_press_before_settle(self):
    assert all(b is None for b in run(self.exp, 0, SETTLE))

  def test_press_lasts_exactly_press_frames(self):
    run(self.exp, 0, SETTLE)
    out = run(self.exp, SETTLE, PRESS + 5)
    assert out[:PRESS] == ["Cruise_Set"] * PRESS
    assert out[PRESS:] == [None] * 5

  def test_no_second_press_before_period(self):
    run(self.exp, 0, SETTLE + PRESS)
    out = run(self.exp, SETTLE + PRESS, PERIOD - PRESS)
    assert all(b is None for b in out)
    assert self.exp.update(SETTLE + PERIOD, **OK) == "Cruise_Set"

  def test_brake_aborts_press_and_requires_resettle(self):
    run(self.exp, 0, SETTLE + 3)
    assert self.exp.update(SETTLE + 3, **{**OK, "brake": True}) is None
    # conditions are back, but the settle timer restarted
    assert all(b is None for b in run(self.exp, SETTLE + 4, SETTLE - 1))

  def test_driver_button_echo_suppresses(self):
    run(self.exp, 0, SETTLE)
    assert self.exp.update(SETTLE, **{**OK, "camera_buttons_active": True}) is None

  def test_below_min_speed_never_presses(self):
    assert all(b is None for b in run(self.exp, 0, SETTLE + PERIOD, v_ego=9.0))

  def test_stops_after_max_presses(self):
    out = run(self.exp, 0, SETTLE + PERIOD * (MAX + 2))
    assert out.count("Cruise_Set") == MAX * PRESS

  def test_disengage_ends_press(self):
    run(self.exp, 0, SETTLE + 2)
    assert self.exp.update(SETTLE + 2, **{**OK, "enabled": False}) is None
    assert self.exp.update(SETTLE + 3, **{**OK, "cruise_enabled": False}) is None
    assert self.exp.update(SETTLE + 4, **{**OK, "cancel": True}) is None
