import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from orchestrator.core.system_controller import CommandRejected
from orchestrator.devices.device_manager import AXES


class PendantInput:
    def __init__(self):
        self.config = {
            key: int(os.environ.get(f'DT_PENDANT_{key}', default))
            for key, default in {'STICK': 0, 'Y': 1, 'Z': 3, 'TRIGGER': 4, 'HOME': 3, 'STOP': 1}.items()
        }
        self.joystick = None
        self.instance_id = None

    def open(self):
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        os.environ.setdefault('SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', '1')
        import pygame

        self.pygame = pygame
        pygame.display.init()
        pygame.joystick.init()

    def find_joystick(self):
        for index in range(self.pygame.joystick.get_count()):
            candidate = self.pygame.joystick.Joystick(index)
            if not any(name in candidate.get_name().lower()
                       for name in ('dualsense', 'wireless controller', 'ps5')):
                continue
            if (max(self.config[key] for key in ('STICK', 'Y', 'Z', 'TRIGGER')) < candidate.get_numaxes()
                    and max(self.config['HOME'], self.config['STOP']) < candidate.get_numbuttons()):
                self.joystick = candidate
                self.instance_id = candidate.get_instance_id()
                return

    def poll(self):
        pygame = self.pygame
        removed = False
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEREMOVED and event.instance_id == self.instance_id:
                self.joystick = None
                self.instance_id = None
                removed = True
        if removed:
            return None
        try:
            if self.joystick is None:
                self.find_joystick()
            if self.joystick is None:
                return None
            return (
                tuple(self.joystick.get_axis(self.config[key]) * sign
                      for key, sign in [('STICK', 1), ('Y', -1), ('Z', -1)]),
                self.joystick.get_axis(self.config['TRIGGER']) > 0.2,
                bool(self.joystick.get_button(self.config['HOME'])),
                bool(self.joystick.get_button(self.config['STOP'])),
            )
        except pygame.error:
            self.joystick = None
            self.instance_id = None
            return None

    def close(self):
        if hasattr(self, 'pygame'):
            self.pygame.quit()


async def read_pendant(controller):
    reader = PendantInput()
    loop = asyncio.get_running_loop()
    # SDL device discovery and hotplug can block. Keep it off the TCP/lease loop.
    worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='dt-pendant')
    active = armed = False
    previous = (False, False, False)
    hold = None
    selection = None

    def dispatch(action, **data):
        try:
            controller.dispatch(action, 'Pendant', **data)
            return True
        except CommandRejected:
            return False

    try:
        await loop.run_in_executor(worker, reader.open)
        while True:
            sample = await loop.run_in_executor(worker, reader.poll)
            controller.pendant_connected = sample is not None
            if sample is None:
                controller.input_lost('Pendant')
                active = armed = False
                hold = None
                previous = (False, False, False)
            else:
                sticks, trigger, home, stop = sample
                selected = controller.source == 'Pendant'
                current = (controller.pendant_mode, controller.pendant_axis)
                if current != selection:
                    armed = False
                    selection = current
                multi = current[0] == 'Multi'
                axes = AXES if multi else (current[1],)
                raw = sticks if multi else sticks[:1]
                neutral = all(abs(value) < 0.2 for value in raw)
                inputs = {name: scale_stick(value) for name, value in zip(axes, raw)}
                if stop and not previous[2]:
                    dispatch('stop')
                if not selected or not controller.devices.motion.connected or controller.state in {'Init', 'Fault'}:
                    if active or hold:
                        controller.input_lost('Pendant')
                    armed = False
                    hold = None
                elif not active or not armed:
                    armed = neutral and not trigger and not home and not stop
                else:
                    if trigger != previous[0]:
                        dispatch('enable' if trigger else 'disable', axes=axes)
                        if not trigger:
                            hold = None
                    if home and not previous[1] and not multi:
                        dispatch('home', axes=axes)
                    if neutral or not trigger or stop:
                        if hold:
                            controller.input_lost('Pendant')
                            hold = None
                    elif hold:
                        controller.hold('Pendant', hold, True, inputs=inputs if multi else None)
                    elif trigger and max(map(abs, raw)) > 0.35:
                        candidate = uuid4().hex
                        action = 'pv' if multi else 'jog'
                        data = {'inputs': inputs} if multi else {
                            'direction': 'positive' if raw[0] > 0 else 'negative'
                        }
                        if dispatch(action, axes=axes, hold=candidate, **data):
                            hold = candidate
                active = selected
                previous = (trigger, home, stop)
            await asyncio.sleep(0.02)
    finally:
        controller.input_lost('Pendant')
        controller.pendant_connected = False
        try:
            await loop.run_in_executor(worker, reader.close)
        finally:
            worker.shutdown(wait=False)


def scale_stick(value):
    magnitude = max(0.0, min(1.0, (abs(value) - 0.2) / 0.8))
    return magnitude if value >= 0 else -magnitude
