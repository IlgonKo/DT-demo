import unittest
from unittest.mock import AsyncMock, Mock

from orchestrator.devices.device_manager import AxisLimits, AxisState, DeviceManager
from orchestrator.operations.manual_controller import Execution, ManualController, pv_velocity


class PvLimitTest(unittest.TestCase):
    limits = AxisLimits(-5.0, 5.0, 20.0, 1000.0)

    def test_slows_before_edge_and_allows_reversal(self):
        far = AxisState(0.0, 0.0, 0)
        near = AxisState(4.5, 0.0, 0)
        edge = AxisState(5.0, 0.0, 0)
        self.assertEqual(pv_velocity(1, far, self.limits, 10), 10)
        self.assertGreater(pv_velocity(1, near, self.limits, 10), 0)
        self.assertLess(pv_velocity(1, near, self.limits, 10), 10)
        self.assertEqual(pv_velocity(1, edge, self.limits, 10), 0)
        self.assertEqual(pv_velocity(-1, edge, self.limits, 10), -10)

    def test_commands_zero_when_observed_speed_exceeds_braking_room(self):
        near = AxisState(4.5, 10.0, 0x100)
        self.assertEqual(pv_velocity(1, near, self.limits, 10), 0)


class AxisGroupTest(unittest.IsolatedAsyncioTestCase):
    async def test_common_stop_includes_all_mapped_axes(self):
        devices = DeviceManager({'X1': 4, 'Y': 2, 'Z': 5})
        devices.motion = Mock(request=AsyncMock())
        await devices.stop(('X1', 'Y', 'Z'))
        devices.motion.request.assert_awaited_once_with('system/axes/stop', axes=[4, 2, 5])

    async def test_pp_waits_for_every_selected_axis(self):
        devices = Mock(set_modes=AsyncMock(), axis_group=AsyncMock())
        wait_for_feedback = AsyncMock()
        manual = ManualController(devices, wait_for_feedback, 0.5)
        await manual.execute(Execution('pp', 'HMI', axes=('X1', 'Z')),
                             {'positions': {'X1': 5, 'Z': 7}})
        devices.axis_group.assert_awaited_once_with(
            'move_abs', ('X1', 'Z'), positions=[5, 7], profile_velocity=5.0)
        names, complete = wait_for_feedback.await_args.args
        self.assertEqual(names, ('X1', 'Z'))
        self.assertFalse(complete({'X1': AxisState(5, 0, 0), 'Z': AxisState(7, 1, 0x100)}))
        self.assertTrue(complete({'X1': AxisState(5, 0, 0), 'Z': AxisState(7, 0, 0)}))
