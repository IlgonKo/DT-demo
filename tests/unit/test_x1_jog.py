import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, call

from orchestrator.core.system_controller import SystemController
from orchestrator.devices.device_manager import DeviceManager
from orchestrator.interfaces.motion_server.client import MotionRejected
from orchestrator.operations.manual_controller import Execution


class JogStopTest(unittest.IsolatedAsyncioTestCase):
    async def test_jog_stop_preserves_mode_restoration_for_next_jog(self):
        devices = DeviceManager(0)
        devices.motion = Mock(request=AsyncMock())
        await devices.stop_axis(jogging=True)
        devices.motion.request.assert_awaited_once_with('system/axis/jog_stop', axis=0)

    async def test_rejected_jog_stop_falls_back_to_axis_stop(self):
        devices = DeviceManager(0)
        devices.motion = Mock(request=AsyncMock(side_effect=[MotionRejected('restore error'), {}]))
        with self.assertRaises(MotionRejected):
            await devices.stop_axis(jogging=True)
        self.assertEqual(devices.motion.request.await_args_list, [
            call('system/axis/jog_stop', axis=0),
            call('system/axis/stop', axis=0),
        ])

    async def test_expired_or_previous_input_cannot_renew_jog(self):
        controller = SystemController(DeviceManager(0))
        controller.input_lost = Mock()
        expired = asyncio.get_running_loop().time() - 1
        execution = Execution('jog', 'HMI', hold='current', expires_at=expired)
        controller.execution = execution
        controller.hold('HMI', 'old', True)
        controller.hold('Pendant', 'current', True)
        controller.input_lost.assert_not_called()
        controller.hold('HMI', 'current', True)
        controller.input_lost.assert_called_once_with('HMI')
        self.assertEqual(execution.expires_at, expired)
