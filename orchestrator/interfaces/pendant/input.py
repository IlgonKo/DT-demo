import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from orchestrator.core.system_controller import CommandRejected
from orchestrator.devices.device_manager import AXES


class PendantInput:
    def __init__(self):
        default_config = Path(__file__).with_name('config.json')
        config = json.loads(Path(os.environ.get('DT_PENDANT_CONFIG', default_config))
                            .read_text(encoding='utf-8'))
        profiles = json.loads(default_config.with_name('device_profiles.json').read_text(encoding='utf-8'))
        mapping = profiles['profiles'][config['device']['profile']]['mapping']
        actions = config['actions']
        enable = actions['enable']
        self.axes = tuple(
            (int(os.environ.get(f'DT_PENDANT_{env_key}', mapping['axes'][config['axes'][name]])),
             -1 if config['invert'].get(name) else 1)
            for name, env_key in (('x', 'STICK'), ('y', 'Y'), ('z', 'Z'))
        )
        self.trigger = int(os.environ.get('DT_PENDANT_TRIGGER', mapping['triggers'][enable['control']]))
        self.trigger_threshold = enable['threshold']
        self.buttons = {
            name: int(os.environ.get(f'DT_PENDANT_{env_key}', mapping['buttons'][actions[name]]))
            for name, env_key in (('homing', 'HOME'), ('stop', 'STOP'),
                                  ('loader_initial', 'LOADER_INITIAL'),
                                  ('loader_opposite', 'LOADER_OPPOSITE'))
        }
        axes = [index for index, _ in self.axes] + [self.trigger]
        if (min(*axes, *self.buttons.values()) < 0 or len(set(axes)) != len(axes)
                or len(set(self.buttons.values())) != len(self.buttons)):
            raise ValueError('Pendant 축과 버튼에 서로 다른 유효한 SDL 인덱스가 필요합니다.')
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
        max_axis = max(self.trigger, *(index for index, _ in self.axes))
        max_button = max(self.buttons.values())
        for index in range(self.pygame.joystick.get_count()):
            candidate = self.pygame.joystick.Joystick(index)
            if not any(name in candidate.get_name().lower()
                       for name in ('dualsense', 'wireless controller', 'ps5')):
                continue
            if max_axis < candidate.get_numaxes() and max_button < candidate.get_numbuttons():
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
                tuple(self.joystick.get_axis(index) * sign for index, sign in self.axes),
                self.joystick.get_axis(self.trigger) > self.trigger_threshold,
                {action for action, index in self.buttons.items() if self.joystick.get_button(index)},
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
    active = armed = previous_trigger = False
    previous_buttons = set()
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
                active = armed = previous_trigger = False
                hold = None
                previous_buttons = set()
            else:
                sticks, trigger, buttons = sample
                pressed = buttons - previous_buttons
                stop = 'stop' in buttons
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
                if 'stop' in pressed:
                    dispatch('stop')
                if not selected or not controller.devices.motion.connected or controller.state in {'Init', 'Fault'}:
                    if active or hold:
                        controller.input_lost('Pendant')
                    armed = False
                    hold = None
                elif not active or not armed:
                    armed = neutral and not trigger and not buttons
                else:
                    if trigger != previous_trigger and not stop:
                        dispatch('enable' if trigger else 'disable', axes=axes)
                        if not trigger:
                            hold = None
                    if not stop:
                        if 'homing' in pressed and not multi:
                            dispatch('home', axes=axes)
                        loader_buttons = buttons & {'loader_initial', 'loader_opposite'}
                        if neutral and not trigger and len(loader_buttons) == 1:
                            button = next(iter(loader_buttons))
                            if button in pressed:
                                dispatch('loader', direction=button.removeprefix('loader_'))
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
                previous_trigger = trigger
                previous_buttons = buttons
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
