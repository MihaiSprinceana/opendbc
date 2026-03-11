from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery

EXT_DIAG_REQUEST = b'\x10\x03'
EXT_DIAG_RESPONSE = b'\x50\x03'

COM_CONT_RESPONSE = b''


def disable_ecu(can_recv, can_send, bus=0, addr=0x7d0, sub_addr=None, com_cont_req=b'\x28\x83\x01',
                com_cont_reqs=None, com_cont_response=COM_CONT_RESPONSE, timeout=0.1, retry=10):
  """Silence an ECU by disabling sending and receiving messages using UDS 0x28.
  The ECU will stay silent as long as openpilot keeps sending Tester Present.

  This is used to disable the radar in some cars. Openpilot will emulate the radar.
  WARNING: THIS DISABLES AEB!"""
  carlog.warning(f"ecu disable {hex(addr), sub_addr} ...")

  if com_cont_reqs is None:
    com_cont_reqs = [com_cont_req]

  for i in range(retry):
    try:
      query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, sub_addr)], [EXT_DIAG_REQUEST], [EXT_DIAG_RESPONSE])

      for _, _ in query.get_data(timeout).items():
        for req in com_cont_reqs:
          carlog.warning(f"communication control request {req.hex()} ...")
          query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, sub_addr)], [req], [com_cont_response])
          response = query.get_data(timeout if len(com_cont_response) else 0)

          # Backward compatible mode for requests that intentionally suppress response.
          if len(com_cont_response) == 0:
            carlog.warning("ecu disabled")
            return True

          if len(response):
            carlog.warning("ecu disabled")
            return True

          carlog.error(f"communication control rejected/no response for {req.hex()}")

    except Exception:
      carlog.exception("ecu disable exception")

    carlog.error(f"ecu disable retry ({i + 1}) ...")
  carlog.error("ecu disable failed")
  return False
