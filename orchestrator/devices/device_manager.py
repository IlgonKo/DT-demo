from dataclasses import dataclass

from orchestrator.interfaces.motion_server.client import MotionRejected


@dataclass(frozen=True)
class AxisState:
    position: float
    velocity: float
    statusword: int

    @property
    def moving(self):
        return bool(self.statusword & 0x0100)

    @property
    def enabled(self):
        return self.statusword & 0x006F == 0x0027

    @property
    def fault(self):
        return bool(self.statusword & 0x0008)


class DeviceManager:
    """The first integration slice maps logical X1 to one virtual server axis."""

    def __init__(self, axis_index):
        self.axis_index = axis_index
        self.motion = None
        self.axis = None
        self.version = 0
        self.authority = False
        self.server_fault = None

    def update(self, feedback):
        self.version += 1
        self.authority = feedback.get('command_authority', {}).get(
            'owned_by_this_client', False
        )
        health = feedback.get('server_health', {})
        diagnostic = health.get('representative_diagnostic') or {}
        self.server_fault = None
        if health.get('diagnostic_level') == 'fault':
            self.server_fault = diagnostic.get('title') or 'Motion Server Fault'
        self.axis = None
        index = self.axis_index
        if not feedback.get('process_data_valid') or not health.get('initialized'):
            return
        arrays = [feedback.get(name, []) for name in
                  ('actual_positions', 'actual_velocities', 'statuswords')]
        if all(index < len(values) for values in arrays):
            self.axis = AxisState(*(values[index] for values in arrays))

    def disconnect(self):
        self.version += 1
        self.axis = None
        self.authority = False
        self.server_fault = None

    async def stop_axis(self, jogging):
        if not jogging:
            await self.axis_command('stop')
            return
        try:
            await self.axis_command('jog_stop')
        except MotionRejected:
            await self.axis_command('stop')
            raise

    async def axis_command(self, command, **fields):
        return await self.motion.request(
            f'system/axis/{command}', axis=self.axis_index, **fields
        )
