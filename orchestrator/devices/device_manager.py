import math
from dataclasses import dataclass

from orchestrator.interfaces.motion_server.client import MotionRejected

AXES = ('X1', 'Y', 'Z')


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


@dataclass(frozen=True)
class AxisLimits:
    lower: float
    upper: float
    max_velocity: float
    deceleration: float


class DeviceManager:
    def __init__(self, mapping, pv_bounds=None):
        if set(mapping) != set(AXES) or len(set(mapping.values())) != len(AXES):
            raise ValueError('X1·Y·Z에는 서로 다른 축 인덱스가 필요합니다.')
        if any(type(index) is not int or index < 0 for index in mapping.values()):
            raise ValueError('축 인덱스는 0 이상의 정수여야 합니다.')
        self.mapping = dict(mapping)
        self.pv_bounds = pv_bounds or {}
        for name, bounds in self.pv_bounds.items():
            if (name not in AXES or len(bounds) != 2 or not all(map(math.isfinite, bounds))
                    or bounds[0] >= bounds[1]):
                raise ValueError('잘못된 PV 작업 범위')
        self.motion = None
        self.axes = {}
        self.version = 0
        self.authority = False
        self.server_fault = None

    def update(self, feedback):
        self.version += 1
        self.authority = feedback.get('command_authority', {}).get('owned_by_this_client', False)
        health = feedback.get('server_health', {})
        diagnostic = health.get('representative_diagnostic') or {}
        self.server_fault = (
            (diagnostic.get('title') or 'Motion Server Fault')
            if health.get('diagnostic_level') == 'fault' else None
        )
        self.axes = {}
        if not feedback.get('process_data_valid') or not health.get('initialized'):
            return
        arrays = [feedback.get(name, []) for name in
                  ('actual_positions', 'actual_velocities', 'statuswords')]
        for name, index in self.mapping.items():
            if all(index < len(values) for values in arrays):
                position, velocity, statusword = (values[index] for values in arrays)
                if math.isfinite(position) and math.isfinite(velocity) and type(statusword) is int:
                    self.axes[name] = AxisState(position, velocity, statusword)

    def disconnect(self):
        self.version += 1
        self.axes = {}
        self.authority = False
        self.server_fault = None

    async def stop(self, names, jog_axis=None):
        if jog_axis is None:
            await self.axis_group('stop', names)
            return
        try:
            await self.axis_command('jog_stop', jog_axis)
        except MotionRejected:
            await self.axis_group('stop', names)
            raise
        remaining = tuple(name for name in names if name != jog_axis)
        if remaining:
            await self.axis_group('stop', remaining)

    async def axis_command(self, command, name, **fields):
        return await self.motion.request(f'system/axis/{command}', axis=self.mapping[name], **fields)

    async def axis_group(self, command, names, **fields):
        return await self.motion.request(
            f'system/axes/{command}', axes=[self.mapping[name] for name in names], **fields
        )

    async def set_modes(self, names, mode):
        for name in names:
            await self.axis_command('mode', name, mode=mode)

    async def read_pv_limits(self, names):
        status = await self.motion.request('system/axes/status')
        limits = {}
        for name in names:
            index = self.mapping[name]
            try:
                metadata = status['axis_metadata'][index]
                lower, upper = status['software_position_limits'][index * 2:index * 2 + 2]
                max_velocity = status['motion_limits'][index * 4]
                deceleration = status['profile_settings'][index * 4 + 2]
                configured_lower, configured_upper = self.pv_bounds.get(name, (lower, upper))
                values = (lower, upper, max_velocity, deceleration)
                if (not metadata.get('pv_allowed') or metadata.get('velocity_unit') != 'mm/s'
                        or not all(map(math.isfinite, values)) or min(max_velocity, deceleration) <= 0):
                    raise ValueError
                lower, upper = max(lower, configured_lower), min(upper, configured_upper)
                if lower >= upper:
                    raise ValueError
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                raise RuntimeError(f'{name}의 유효한 PV 속도·위치 한계를 확인할 수 없습니다.') from exc
            limits[name] = AxisLimits(lower, upper, max_velocity, deceleration)
        return limits
