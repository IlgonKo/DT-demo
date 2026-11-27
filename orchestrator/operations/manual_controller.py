import asyncio
import math
from dataclasses import dataclass, field


@dataclass
class Execution:
    action: str
    source: str
    hold: str | None = None
    expires_at: float = 0.0
    axes: tuple = ()
    jog_axis: str | None = None
    inputs: dict = field(default_factory=dict)
    stop_loader: bool = False


def pv_velocity(request, state, limits, speed, reaction=0.25, margin=0.25):
    if not request:
        return 0.0
    sign = math.copysign(1.0, request)
    edge = limits.upper if sign > 0 else limits.lower
    distance = max(0.0, (edge - state.position) * sign - margin)
    # v*t + v²/(2*a) <= available travel.
    deceleration = limits.deceleration
    safe_speed = 2 * distance / (
        math.sqrt(reaction**2 + 2 * distance / deceleration) + reaction
    )
    observed = max(0.0, sign * state.velocity)
    if observed * reaction + observed**2 / (2 * deceleration) > distance:
        return 0.0
    return sign * min(abs(request) * speed, limits.max_velocity, safe_speed)


class ManualController:
    def __init__(self, devices, wait_feedback, jog_ack_timeout, pv_speed=10.0):
        self.devices = devices
        self.wait_feedback = wait_feedback
        self.jog_ack_timeout = jog_ack_timeout
        self.pv_speed = pv_speed
        self.pv_status = {}

    async def execute(self, execution, data):
        action = execution.action
        axes = execution.axes
        axis_command = self.devices.axis_command
        wait = self.wait_feedback
        if action == 'authority':
            command = 'request' if data['enabled'] else 'release'
            await self.devices.motion.request(f'system/authority/{command}')
            await wait(axes, lambda _: self.devices.authority == data['enabled'])
        elif action in {'enable', 'disable'}:
            await self.devices.axis_group(action, axes)
            await wait(axes, lambda states: all(
                axis.enabled == (action == 'enable') and not axis.moving for axis in states.values()
            ))
        elif action == 'pp':
            positions = data['positions']
            await self.devices.set_modes(axes, 'pp')
            await self.devices.axis_group(
                'move_abs', axes, positions=[positions[name] for name in axes], profile_velocity=5.0
            )
            await wait(axes, lambda states: all(
                not axis.moving and abs(axis.position - positions[name]) <= 0.02
                for name, axis in states.items()
            ))
        elif action == 'loader':
            direction = data['direction']
            loader = self.devices.loader
            if loader and loader.at_commanded_endpoint(direction):
                return
            await self.devices.command_loader(direction)
            await wait((), lambda _: (loader := self.devices.loader) is not None
                       and loader.at_commanded_endpoint(direction))
        elif action == 'home':
            name = axes[0]
            await axis_command('home', name)
            while True:
                status = await axis_command('status', name)
                homing = status.get('homing', {})
                if homing.get('state') == 'complete':
                    break
                if homing.get('state') not in {'running', 'starting'} and not homing.get('active'):
                    raise RuntimeError(homing.get('message') or 'Homing 완료를 확인하지 못함')
                await asyncio.sleep(0.1)
            await wait(axes, lambda states: not states[name].moving)
        elif action == 'jog':
            async with asyncio.timeout(self.jog_ack_timeout):
                await axis_command('jog_start', axes[0], direction=data['direction'], speed='slow')
            await asyncio.Future()
        elif action == 'pv':
            await self.run_pv(execution)
        elif action == 'recover':
            faulted = tuple(name for name in axes if self.devices.axes[name].fault)
            if faulted:
                await self.devices.axis_group('fault_reset', faulted)
            await wait(axes, lambda states: not self.devices.server_fault and all(
                not axis.moving and not axis.fault for axis in states.values()
            ) and (not self.devices.loader_mapping or
                   (self.devices.loader and not self.devices.loader.conflicting)))

    async def run_pv(self, execution):
        names = execution.axes
        try:
            async with asyncio.timeout(2):
                limits = await self.devices.read_pv_limits(names)
                await self.devices.set_modes(names, 'pv')
            previous = None
            version = self.devices.version
            while True:
                async with asyncio.timeout(0.5):
                    await self.wait_feedback(names, lambda _: True, after=version)
                version = self.devices.version
                velocities = []
                for name in names:
                    request = execution.inputs[name]
                    limits_for_axis = limits[name]
                    speed = pv_velocity(request, self.devices.axes[name], limits_for_axis,
                                        self.pv_speed)
                    velocities.append(speed)
                    self.pv_status[name] = {
                        'lower': limits_for_axis.lower, 'upper': limits_for_axis.upper,
                        'requested': request * self.pv_speed, 'commanded': speed,
                    }
                if velocities != previous:
                    async with asyncio.timeout(0.5):
                        await self.devices.axis_group('move_vel', names, velocities=velocities)
                    previous = velocities
        finally:
            self.pv_status = {}
