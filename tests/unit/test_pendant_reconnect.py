import asyncio
import unittest
from queue import Empty, Queue
from types import SimpleNamespace
from unittest.mock import Mock, patch

from orchestrator.interfaces.pendant.input import read_pendant


class PendantReconnectTest(unittest.IsolatedAsyncioTestCase):
    async def test_held_input_is_ignored_until_neutral_after_reconnect(self):
        samples = Queue()
        reader = Mock()

        def poll():
            try:
                return samples.get(timeout=0.1)
            except Empty:
                return None

        reader.poll.side_effect = poll
        controller = SimpleNamespace(
            source='Pendant', state='Ready', pendant_connected=False,
            pendant_mode='Single', pendant_axis='X1',
            devices=SimpleNamespace(motion=SimpleNamespace(connected=True)),
            dispatch=Mock(), hold=Mock(), input_lost=Mock(),
        )

        async def wait_for(condition):
            async with asyncio.timeout(2):
                while not condition():
                    await asyncio.sleep(0.005)

        def jogs():
            return [call for call in controller.dispatch.call_args_list
                    if call.args[0] == 'jog']

        neutral = ((0.0, 0.0, 0.0), False, False, False)
        trigger = ((0.0, 0.0, 0.0), True, False, False)
        stick_held = ((0.8, 0.0, 0.0), True, False, False)

        with patch('orchestrator.interfaces.pendant.input.PendantInput', return_value=reader):
            task = asyncio.create_task(read_pendant(controller))
            try:
                for sample in (neutral, trigger, stick_held):
                    samples.put(sample)
                await wait_for(lambda: len(jogs()) == 1)
                samples.put(None)
                await wait_for(lambda: not controller.pendant_connected)
                controller.input_lost.assert_any_call('Pendant')

                samples.put(stick_held)
                await wait_for(lambda: controller.pendant_connected)
                self.assertEqual(len(jogs()), 1)

                for sample in (neutral, trigger, stick_held):
                    samples.put(sample)
                await wait_for(lambda: len(jogs()) == 2)
                self.assertNotEqual(jogs()[0].kwargs['hold'], jogs()[1].kwargs['hold'])
            finally:
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
