import asyncio
from dataclasses import asdict

from orchestrator.interfaces.motion_server.client import MotionRejected
from orchestrator.operations.manual_controller import Execution, ManualController


class CommandRejected(Exception):
    pass


class SystemController:
    def __init__(self, devices, stop_timeout=2.0, hold_timeout=0.5):
        self.devices = devices
        self.stop_timeout = stop_timeout
        self.hold_timeout = hold_timeout
        self.manual = ManualController(devices, self.wait_feedback, hold_timeout)
        self.state = 'Init'
        self.source = 'HMI'
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
        axis = self.devices.axis
        axis_fault = '가상 X1 축 Fault' if axis and axis.fault else None
        fault = axis_fault or self.devices.server_fault
        if fault:
            self.fault = fault
            self.state = 'Fault'
            if self.execution and self.execution.action in {'home', 'pp', 'jog'}:
                if self.devices.authority:
                    self.stop('System')
                else:
                    self.cancel()
        elif self.execution and self.execution.action in {'home', 'pp', 'jog'} and not self.devices.authority:
            self.cancel()
            self.fault = '운전 중 Motion Server 제어권 상실'
            self.state = 'Fault'
        elif self.state == 'Init' and axis and not axis.moving:
            self.state = 'Ready'

    def disconnected(self, reason):
        self.devices.disconnect()
        if self.state != 'Init':
            self.cancel()
            self.state = 'Fault'
            self.fault = reason

    async def wait_feedback(self, predicate):
        baseline = self.devices.version
        while True:
            axis = self.devices.axis
            if self.devices.version > baseline and axis is not None and predicate(axis):
                return
            await self.update.wait()

    def cancel(self):
        if self.task and self.task is not asyncio.current_task():
            self.task.cancel()
        previous, self.execution = self.execution, None
        return previous

    def change_source(self, source):
        if self.state != 'Ready' or self.execution:
            raise CommandRejected('Ready 상태에서 조작 소스를 변경할 수 있습니다.')
        self.source = source

    def dispatch(self, action, source='HMI', **data):
        if action in {'stop', 'disable'}:
            if action == 'disable' and source != self.source:
                raise CommandRejected('다른 조작 소스가 선택되어 있습니다.')
            self.stop(source, action)
            return
        if not self.devices.motion.connected or not self.devices.axis:
            raise CommandRejected('유효한 가상 X1 피드백이 없습니다.')
        if self.execution:
            raise CommandRejected('다른 동작이 실행 중입니다.')
        if action == 'recover':
            if self.state != 'Fault':
                raise CommandRejected('Fault 상태에서 복구할 수 있습니다.')
            if self.devices.axis.fault and not self.devices.authority:
                raise CommandRejected('축 Fault 해제에 제어권이 필요합니다.')
        elif action == 'authority':
            if self.state not in {'Ready', 'Fault'}:
                raise CommandRejected('현재 상태에서 제어권을 변경할 수 없습니다.')
        else:
            if self.state != 'Ready' or source != self.source:
                raise CommandRejected('Ready 상태와 선택된 조작 소스를 확인하세요.')
            if not self.devices.authority:
                raise CommandRejected('Motion Server 제어권이 필요합니다.')
        if action in {'home', 'pp', 'jog'} and not self.devices.axis.enabled:
            raise CommandRejected('가상 X1의 Servo를 먼저 켜세요.')
        execution = Execution(action, source, hold=data.get('hold'), jogging=action == 'jog')
        if execution.hold:
            execution.expires_at = asyncio.get_running_loop().time() + self.hold_timeout
        if action in {'home', 'pp', 'jog'}:
            self.state = 'Running'
        self.start(execution, data)

    def stop(self, source, action='stop'):
        if not self.devices.motion.connected or not self.devices.authority:
            raise CommandRejected('정지 요청에 Motion Server 연결과 제어권이 필요합니다.')
        if self.execution and self.execution.action == action:
            return
        old = self.cancel()
        if self.state != 'Fault':
            self.state = 'Running'
        self.start(Execution(action, source, jogging=bool(old and old.jogging)), {})

    def start(self, execution, data):
        self.notice = None
        self.execution = execution
        now = asyncio.get_running_loop().time()
        duration = {'stop': self.stop_timeout, 'disable': self.stop_timeout,
                    'home': 30.0, 'pp': 15.0, 'jog': None}.get(execution.action, 5.0)
        self.task = asyncio.create_task(
            self.execute(execution, data, None if duration is None else now + duration)
        )

    async def execute(self, execution, data, deadline):
        action = execution.action
        try:
            async with asyncio.timeout_at(deadline):
                if action == 'stop':
                    await self.devices.stop_axis(execution.jogging)
                    await self.wait_feedback(lambda axis: not axis.moving)
                else:
                    await self.manual.execute(action, data)
        except asyncio.CancelledError:
            raise
        except MotionRejected as error:
            self.notice = str(error)
            if action in {'stop', 'disable'}:
                self.fault = f'정지 미확인: {error}'
                self.state = 'Fault'
            elif self.state != 'Fault':
                self.state = 'Ready'
        except (ConnectionError, ValueError, RuntimeError, TimeoutError) as error:
            self.state = 'Fault'
            detail = str(error) or '피드백 또는 응답 시간 초과'
            self.fault = f'정지 미확인: {detail}' if action in {'stop', 'disable'} else detail
            if action in {'home', 'pp', 'jog'}:
                try:
                    self.stop('System')
                except CommandRejected:
                    pass
        else:
            if action == 'recover':
                self.fault = None
            self.state = 'Fault' if self.fault else 'Ready'
        finally:
            if self.execution is execution:
                self.execution = None

    def hold(self, source, key, pressed):
        execution = self.execution
        if not execution or execution.hold != key or execution.source != source:
            return
        now = asyncio.get_running_loop().time()
        if pressed and now < execution.expires_at:
            execution.expires_at = now + self.hold_timeout
        else:
            self.input_lost(source)

    def input_lost(self, source):
        if self.execution and self.execution.hold and self.execution.source == source:
            try:
                self.stop(source)
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
        axis = self.devices.axis
        return {
            'state': self.state, 'target_mode': 'DT', 'operation_mode': 'Manual',
            'source': self.source, 'connected': self.devices.motion.connected,
            'authority': self.devices.authority, 'fault': self.fault,
            'notice': self.notice, 'activity': self.execution.action if self.execution else None,
            'pendant_connected': self.pendant_connected,
            'virtual': {'X1': asdict(axis) | {'enabled': axis.enabled, 'moving': axis.moving}
                        if axis else None},
            'physical': {}, 'auto': None,
        }
