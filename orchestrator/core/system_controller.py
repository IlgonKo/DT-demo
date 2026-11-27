import asyncio
import math
from dataclasses import asdict

from orchestrator.devices.device_manager import AXES
from orchestrator.interfaces.motion_server.client import MotionRejected
from orchestrator.operations.manual_controller import Execution, ManualController

MOTION_ACTIONS = {'home', 'pp', 'jog', 'pv'}


class CommandRejected(Exception):
    pass


class SystemController:
    def __init__(self, devices, stop_timeout=2.0, hold_timeout=0.5, pv_speed=10.0):
        self.devices = devices
        self.stop_timeout = stop_timeout
        self.hold_timeout = hold_timeout
        self.manual = ManualController(devices, self.wait_feedback, hold_timeout, pv_speed)
        self.state = 'Init'
        self.source = 'HMI'
        self.pendant_mode = 'Single'
        self.pendant_axis = 'X1'
        self.fault = None
        self.notice = None
        self.execution = None
        self.task = None
        self.update = asyncio.Event()
        self.pendant_connected = False

    def receive_feedback(self, payload):
        self.devices.update(payload)
        event, self.update = self.update, asyncio.Event()
        event.set()
        axes = self.devices.axes
        faulted = [name for name, axis in axes.items() if axis.fault]
        fault = f'가상 축 Fault: {", ".join(faulted)}' if faulted else self.devices.server_fault
        executing = self.execution and self.execution.action in MOTION_ACTIONS
        if fault:
            self.fault = fault
            self.state = 'Fault'
            if executing:
                self.stop_after_fault()
        elif executing and not self.devices.authority:
            self.cancel()
            self.fault = '운전 중 Motion Server 제어권 상실'
            self.state = 'Fault'
        elif self.state == 'Init' and len(axes) == len(AXES) and all(not a.moving for a in axes.values()):
            self.state = 'Ready'

    def disconnected(self, reason):
        self.devices.disconnect()
        if self.state != 'Init':
            self.cancel()
            self.state = 'Fault'
            self.fault = reason

    async def wait_feedback(self, names, predicate, after=None):
        baseline = self.devices.version if after is None else after
        while True:
            axes = self.devices.axes
            if self.devices.version > baseline and all(name in axes for name in names):
                if predicate({name: axes[name] for name in names}):
                    return
            await self.update.wait()

    def cancel(self):
        if self.task and self.task is not asyncio.current_task():
            self.task.cancel()
        previous, self.execution = self.execution, None
        return previous

    def require_ready(self):
        if self.state != 'Ready' or self.execution:
            raise CommandRejected('Ready 상태에서 조작 설정을 변경할 수 있습니다.')

    def change_source(self, source):
        self.require_ready()
        self.source = source

    def change_pendant(self, mode=None, axis=None):
        self.require_ready()
        if mode is not None:
            self.pendant_mode = mode
        if axis is not None:
            self.pendant_axis = axis

    def dispatch(self, action, source='HMI', axes=None, **data):
        if action == 'pp':
            axes = tuple(data['positions'])
        if action in {'authority', 'stop', 'recover', 'pv'}:
            axes = AXES
        if axes is None:
            axes = ('X1',)
        axes = tuple(axes)
        if (not axes or len(set(axes)) != len(axes)
                or any(name not in self.devices.mapping for name in axes)
                or (action in {'home', 'jog'} and len(axes) != 1)):
            raise CommandRejected('유효한 축을 선택하세요.')
        if action in {'stop', 'disable'}:
            if action == 'disable' and source != self.source:
                raise CommandRejected('다른 조작 소스가 선택되어 있습니다.')
            self.stop(source, action, axes)
            return
        if not self.devices.motion.connected or any(name not in self.devices.axes for name in axes):
            raise CommandRejected('요청된 축 전체의 유효한 피드백이 필요합니다.')
        if self.execution:
            raise CommandRejected('다른 동작이 실행 중입니다.')
        if action == 'recover':
            if self.state != 'Fault':
                raise CommandRejected('Fault 상태에서 복구할 수 있습니다.')
            if any(self.devices.axes[name].fault for name in axes) and not self.devices.authority:
                raise CommandRejected('축 Fault 해제에 제어권이 필요합니다.')
        elif action == 'authority':
            if self.state not in {'Ready', 'Fault'}:
                raise CommandRejected('현재 상태에서 제어권을 변경할 수 없습니다.')
        elif self.state != 'Ready' or source != self.source or not self.devices.authority:
            raise CommandRejected('Ready 상태, 선택된 조작 소스 및 제어권을 확인하세요.')
        if action in MOTION_ACTIONS and any(not self.devices.axes[name].enabled for name in axes):
            raise CommandRejected('대상 축의 Servo를 모두 켜세요.')
        inputs = data.get('inputs', {})
        if action == 'pv' and (source != 'Pendant' or not valid_pv_inputs(inputs, axes)):
            raise CommandRejected('올바른 Pendant PV 입력이 필요합니다.')
        execution = Execution(action, source, hold=data.get('hold'), axes=axes,
                              jog_axis=axes[0] if action == 'jog' else None, inputs=inputs)
        if execution.hold:
            execution.expires_at = asyncio.get_running_loop().time() + self.hold_timeout
        if action in MOTION_ACTIONS:
            self.state = 'Running'
        self.start(execution, data)

    def stop(self, source, action='stop', axes=AXES):
        if not self.devices.motion.connected or not self.devices.authority:
            raise CommandRejected('정지 요청에 Motion Server 연결과 제어권이 필요합니다.')
        if self.execution and self.execution.action == action and set(axes) <= set(self.execution.axes):
            return
        old = self.cancel()
        if old and action == 'disable' and old.action in MOTION_ACTIONS:
            axes = tuple(dict.fromkeys((*axes, *old.axes)))
        if self.state != 'Fault':
            self.state = 'Running'
        jog_axis = old.jog_axis if old and old.jog_axis in axes else None
        self.start(Execution(action, source, axes=axes, jog_axis=jog_axis), {})

    def stop_after_fault(self):
        try:
            self.stop('System')
        except CommandRejected:
            self.cancel()

    def start(self, execution, data):
        self.notice = None
        self.execution = execution
        now = asyncio.get_running_loop().time()
        duration = {'stop': self.stop_timeout, 'disable': self.stop_timeout,
                    'home': 30.0, 'pp': 30.0, 'jog': None, 'pv': None}.get(execution.action, 5.0)
        self.task = asyncio.create_task(
            self.execute(execution, data, None if duration is None else now + duration)
        )

    async def execute(self, execution, data, deadline):
        action = execution.action
        try:
            async with asyncio.timeout_at(deadline):
                if action == 'stop':
                    await self.devices.stop(execution.axes, execution.jog_axis)
                    await self.wait_feedback(execution.axes, lambda states: all(
                        not axis.moving for axis in states.values()
                    ))
                else:
                    await self.manual.execute(execution, data)
        except asyncio.CancelledError:
            raise
        except MotionRejected as error:
            self.notice = str(error)
            if action in {'stop', 'disable'}:
                self.fault = f'정지 미확인: {error}'
                self.state = 'Fault'
            elif action in {'pp', 'pv'}:
                self.fault = str(error)
                self.state = 'Fault'
                self.stop_after_fault()
            elif self.state != 'Fault':
                self.state = 'Ready'
        except (ConnectionError, ValueError, RuntimeError, TimeoutError) as error:
            self.state = 'Fault'
            detail = str(error) or '피드백 또는 응답 시간 초과'
            self.fault = f'정지 미확인: {detail}' if action in {'stop', 'disable'} else detail
            if action in MOTION_ACTIONS:
                self.stop_after_fault()
        else:
            if action == 'recover':
                self.fault = None
            self.state = 'Fault' if self.fault else 'Ready'
        finally:
            if self.execution is execution:
                self.execution = None

    def hold(self, source, key, pressed, inputs=None):
        execution = self.execution
        if not execution or execution.hold != key or execution.source != source:
            return
        now = asyncio.get_running_loop().time()
        if pressed and now < execution.expires_at:
            if execution.action == 'pv':
                if not valid_pv_inputs(inputs, execution.axes):
                    self.input_lost(source)
                    return
                execution.inputs = inputs
            execution.expires_at = now + self.hold_timeout
        else:
            self.input_lost(source)

    def input_lost(self, source):
        if self.execution and self.execution.hold and self.execution.source == source:
            try:
                self.stop(source, axes=self.execution.axes)
            except CommandRejected as error:
                self.cancel()
                self.state = 'Fault'
                self.fault = f'정지 미확인: {error}'

    async def monitor_hold(self):
        while True:
            execution = self.execution
            if execution and execution.hold:
                if asyncio.get_running_loop().time() >= execution.expires_at:
                    self.input_lost(execution.source)
            await asyncio.sleep(0.05)

    def snapshot(self):
        return {
            'state': self.state, 'target_mode': 'DT', 'operation_mode': 'Manual',
            'source': self.source, 'connected': self.devices.motion.connected,
            'authority': self.devices.authority, 'fault': self.fault,
            'notice': self.notice, 'activity': self.execution.action if self.execution else None,
            'pendant_connected': self.pendant_connected,
            'virtual': {name: asdict(axis) | {'enabled': axis.enabled, 'moving': axis.moving}
                        if (axis := self.devices.axes.get(name)) else None for name in AXES},
            'pendant_mode': self.pendant_mode, 'pendant_axis': self.pendant_axis,
            'pv': self.manual.pv_status,
            'physical': {}, 'auto': None,
        }


def valid_pv_inputs(inputs, axes):
    return bool(inputs) and set(inputs) == set(axes) and all(
        math.isfinite(value) and -1 <= value <= 1 for value in inputs.values()
    )
