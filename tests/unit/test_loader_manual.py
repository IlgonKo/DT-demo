import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from orchestrator.core.system_controller import CommandRejected, SystemController
from orchestrator.devices.device_manager import AXES, DeviceManager, LoaderMapping


class LoaderManualTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.devices = DeviceManager(
            dict(zip(AXES, range(3))),
            loader_mapping=LoaderMapping('io0', 1, 2, 0, 1, 1, 0, True),
        )
        self.devices.motion = Mock(connected=True, request=AsyncMock())
        self.controller = SystemController(self.devices, stop_timeout=0.15)
        self.feed()

    async def asyncTearDown(self):
        task = self.controller.task
        self.controller.cancel()
        if task:
            await asyncio.gather(task, return_exceptions=True)

    def feed(self, sensors=(True, False), coils=(False, False), valid=True):
        self.controller.receive_feedback({
            'process_data_valid': valid,
            'server_health': {'initialized': True},
            'command_authority': {'owned_by_this_client': True},
            'actual_positions': [0.0, 0.0, 0.0],
            'actual_velocities': [0.0, 0.0, 0.0],
            'statuswords': [0x23, 0x23, 0x23],
            'io': {'devices': [{'id': 'io0', 'modules': [
                {'slot': 1, 'inputs': {'digital': sensors}},
                {'slot': 2, 'outputs': {'digital': coils}},
            ]}]},
        })

    async def await_requests(self, count):
        async with asyncio.timeout(0.1):
            while self.devices.motion.request.await_count < count:
                await asyncio.sleep(0)

    async def test_loader_uses_selected_endpoint_and_confirms_outputs_off(self):
        with self.assertRaises(CommandRejected):
            self.controller.dispatch('loader', 'Pendant', direction='opposite')
        self.controller.dispatch('loader', direction='opposite')
        await self.await_requests(1)
        request = self.devices.motion.request
        request.assert_awaited_once_with('system/io/output_write', io='io0', writes=[
            {'slot': 2, 'kind': 'digital', 'channel': 1, 'value': False},
            {'slot': 2, 'kind': 'digital', 'channel': 0, 'value': True},
        ])
        self.feed(sensors=(False, False), coils=(True, False))
        self.assertEqual(self.controller.state, 'Running')
        self.feed(sensors=(False, True), coils=(True, False))
        await self.await_requests(2)
        self.feed(sensors=(False, True))
        await asyncio.wait_for(self.controller.task, 0.1)
        self.assertEqual(self.controller.state, 'Ready')
        self.assertEqual(self.devices.loader.endpoint, 'opposite')

    async def test_common_stop_cancels_loader_and_waits_for_fresh_exclusive_endpoint(self):
        self.controller.dispatch('loader', direction='opposite')
        await self.await_requests(1)
        self.feed(sensors=(False, False), coils=(True, False))
        move = self.controller.task
        self.controller.dispatch('stop', 'Pendant')
        await self.await_requests(3)
        await asyncio.gather(move, return_exceptions=True)
        self.assertTrue(move.cancelled())
        self.devices.motion.request.assert_any_await('system/axes/stop', axes=[0, 1, 2])
        self.assertEqual(self.controller.loader_stop_confirmation, 'pending')
        self.feed(sensors=(False, False))
        await asyncio.sleep(0)
        self.assertEqual(self.controller.state, 'Running')
        self.feed(sensors=(False, True))
        await asyncio.wait_for(self.controller.task, 0.1)
        self.assertEqual(self.controller.state, 'Ready')
        self.assertEqual(self.controller.loader_stop_confirmation, 'confirmed')
        self.assertEqual(self.devices.motion.request.await_count, 3)

    async def test_stop_times_out_if_both_sensors_are_off(self):
        self.feed(sensors=(False, False))
        self.controller.dispatch('stop')
        await self.await_requests(2)
        self.feed(sensors=(False, False))
        await asyncio.wait_for(self.controller.task, 0.5)
        self.assertEqual(self.controller.state, 'Fault')
        self.assertEqual(self.controller.loader_stop_confirmation, 'unconfirmed')
        with self.assertRaises(CommandRejected):
            self.controller.dispatch('recover')
