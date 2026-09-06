"""
EXPERIMENT (throwaway): does an injected ES_Distance Cruise_Set / Cruise_Resume bit move EyeSight's ACC set speed?

Decides WHEN to simulate a press. The safety side (opendbc/safety/modes/subaru.h, SETSPEED_EXP flag) independently
enforces that such a frame only passes the camera's own throttle through and is only sent while engaged.

Cadence mirrors a real press as measured on the 2024 Crosstrek: the camera echoes a physical press for 2-3 of its
20 Hz frames (100-150 ms), so we hold the bit for press_frames control frames (100 Hz).
"""


class SetSpeedExperiment:
  def __init__(self, button: str, period_frames: int = 1000, press_frames: int = 15, settle_frames: int = 500,
               min_speed: float = 10.0, max_presses: int = 6):
    assert button in ("Cruise_Set", "Cruise_Resume")
    self.button = button
    self.period_frames = period_frames
    self.press_frames = press_frames
    self.settle_frames = settle_frames
    self.min_speed = min_speed
    self.max_presses = max_presses

    self.ready_since: int | None = None
    self.press_end: int | None = None
    self.last_press: int | None = None
    self.presses = 0

  def update(self, frame: int, enabled: bool, cruise_enabled: bool, cancel: bool, v_ego: float,
             brake: bool, gas: bool, camera_buttons_active: bool) -> str | None:
    ok = enabled and cruise_enabled and not cancel and v_ego >= self.min_speed and not brake and not gas \
         and not camera_buttons_active
    if not ok:
      # any interruption ends a press in progress and restarts the settle timer
      self.ready_since = None
      self.press_end = None
      return None

    if self.ready_since is None:
      self.ready_since = frame

    if self.press_end is not None:
      if frame < self.press_end:
        return self.button
      self.press_end = None

    if self.presses >= self.max_presses:
      return None
    if frame - self.ready_since < self.settle_frames:
      return None
    if self.last_press is not None and frame - self.last_press < self.period_frames:
      return None

    self.last_press = frame
    self.press_end = frame + self.press_frames
    self.presses += 1
    return self.button
