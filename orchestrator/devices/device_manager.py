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


@dataclass(frozen=True)
class LoaderMapping:
    io: str
    input_slot: int
    output_slot: int
    initial_sensor: int
    opposite_sensor: int
    initial_output: int
    opposite_output: int
    endpoint_hold_verified: bool = False

    def __post_init__(self):
        slots = (self.input_slot, self.output_slot)
        channels = (self.initial_sensor, self.opposite_sensor, self.initial_output, self.opposite_output)
        if (not isinstance(self.io, str) or not self.io.strip()
                or any(type(slot) is not int or slot < 1 for slot in slots)
                or self.input_slot == self.output_slot
                or any(type(channel) is not int or channel < 0 for channel in channels)
                or self.initial_sensor == self.opposite_sensor
                or self.initial_output == self.opposite_output
                or type(self.endpoint_hold_verified) is not bool):
            raise ValueError('잘못된 가상 Loader I/O 설정')


@dataclass(frozen=True)
class LoaderState:
    initial_sensor: bool
    opposite_sensor: bool
    initial_output: bool
    opposite_output: bool

    @property
    def endpoint(self):
        if self.initial_sensor == self.opposite_sensor:
            return None
        return 'initial' if self.initial_sensor else 'opposite'

    @property
    def outputs_off(self):
        return not (self.initial_output or self.opposite_output)

    @property
    def conflicting(self):
        return ((self.initial_sensor and self.opposite_sensor)
                or (self.initial_output and self.opposite_output))


class DeviceManager:
    def __init__(self, mapping, pv_bounds=None, loader_mapping=None):
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
        self.loader_mapping = loader_mapping
        self.loader = None
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
        self.loader = None
        if not feedback.get('process_data_valid') or not health.get('initialized'):
            return
        if self.loader_mapping:
            self.loader = self.read_loader(feedback)
        arrays = [feedback.get(name, []) for name in
                  ('actual_positions', 'actual_velocities', 'statuswords')]
        for name, index in self.mapping.items():
            if all(index < len(values) for values in arrays):
                position, velocity, statusword = (values[index] for values in arrays)
                if math.isfinite(position) and math.isfinite(velocity) and type(statusword) is int:
                    self.axes[name] = AxisState(position, velocity, statusword)

    def read_loader(self, feedback):
        mapping = self.loader_mapping
        station = next((device for device in feedback.get('io', {}).get('devices', [])
                        if device.get('id') == mapping.io), {})
        modules = {module.get('slot'): module for module in station.get('modules', [])}
        inputs = modules.get(mapping.input_slot, {}).get('inputs', {}).get('digital', [])
        outputs = modules.get(mapping.output_slot, {}).get('outputs', {}).get('digital', [])
        try:
            values = (inputs[mapping.initial_sensor], inputs[mapping.opposite_sensor],
                      outputs[mapping.initial_output], outputs[mapping.opposite_output])
        except (IndexError, KeyError, TypeError):
            return None
        if all(type(value) is bool for value in values):
            return LoaderState(*values)
        return None

    @property
    def loader_stopped(self):
        return bool(self.loader_mapping and self.loader_mapping.endpoint_hold_verified
                    and self.loader and self.loader.endpoint and self.loader.outputs_off)

    async def command_loader(self, direction=None):
        mapping = self.loader_mapping
        # Write the inactive coil first when handing off direction.
        outputs = [('initial', mapping.initial_output), ('opposite', mapping.opposite_output)]
        outputs.sort(key=lambda output: output[0] == direction)
        await self.motion.request('system/io/output_write', io=mapping.io, writes=[
            {'slot': mapping.output_slot, 'kind': 'digital', 'channel': channel,
             'value': name == direction}
            for name, channel in outputs
        ])

    def disconnect(self):
        self.version += 1
        self.axes = {}
        self.loader = None
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
