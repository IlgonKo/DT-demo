import asyncio
from dataclasses import dataclass

@dataclass
class Execution:
    action: str
    source: str
    hold: str | None = None
    expires_at: float = 0.0
    jogging: bool = False


class ManualController:
    def __init__(self, devices, wait_feedback, jog_ack_timeout):
        self.devices = devices
        self.wait_feedback = wait_feedback
        self.jog_ack_timeout = jog_ack_timeout

    async def execute(self, action, data):
        axis_command = self.devices.axis_command
        if action == 'authority':
            command = 'request' if data['enabled'] else 'release'
            await self.devices.motion.request(f'system/authority/{command}')
            await self.wait_feedback(lambda _: self.devices.authority == data['enabled'])
            return
        if action in {'enable', 'disable'}:
            await axis_command(action)
            await self.wait_feedback(
                lambda axis: axis.enabled == (action == 'enable') and not axis.moving
            )
            return
        if action == 'pp':
            position = data['position']
            await axis_command('move_abs', position=position, profile_velocity=5.0)
            await self.wait_feedback(
                lambda axis: not axis.moving and abs(axis.position - position) <= 0.02
            )
            return
        if action == 'home':
            await axis_command('home')
            while True:
                status = await axis_command('status')
                homing = status.get('homing', {})
                if homing.get('state') == 'complete':
                    await self.wait_feedback(lambda axis: not axis.moving)
                    return
                if homing.get('state') not in {'running', 'starting'} and not homing.get('active'):
                    raise RuntimeError(homing.get('message') or 'Homing 완료를 확인하지 못함')
                await asyncio.sleep(0.1)
        if action == 'jog':
            async with asyncio.timeout(self.jog_ack_timeout):
                await axis_command('jog_start', direction=data['direction'], speed='slow')
            await asyncio.Future()
        if action == 'recover':
            if self.devices.axis and self.devices.axis.fault:
                await axis_command('fault_reset')
            await self.wait_feedback(
                lambda axis: not axis.moving and not axis.fault and not self.devices.server_fault
            )
