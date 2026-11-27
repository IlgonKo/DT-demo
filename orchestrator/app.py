import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from orchestrator.core.system_controller import SystemController
from orchestrator.devices.device_manager import DeviceManager
from orchestrator.interfaces.hmi.api import router
from orchestrator.interfaces.motion_server.client import MotionServerInterface
from orchestrator.interfaces.pendant.input import read_pendant


@asynccontextmanager
async def lifespan(app):
    devices = DeviceManager(int(os.environ.get('DT_X1_AXIS', '0')))
    if devices.axis_index < 0:
        raise ValueError('DT_X1_AXIS must be nonnegative')
    controller = SystemController(
        devices, stop_timeout=float(os.environ.get('DT_STOP_SECONDS', '2'))
    )
    devices.motion = MotionServerInterface(
        os.environ['DT_MOTION_HOST'],
        int(os.environ.get('DT_MOTION_PORT', '15000')),
        float(os.environ.get('DT_MOTION_HEARTBEAT_TIMEOUT', '0.5')),
        controller.receive_feedback,
        controller.disconnected,
    )
    app.state.controller = controller
    tasks = [asyncio.create_task(devices.motion.run()),
             asyncio.create_task(controller.monitor_hold())]
    if os.environ.get('DT_PENDANT') == '1':
        tasks.append(asyncio.create_task(read_pendant(controller)))
    try:
        yield
    finally:
        controller.cancel()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)
app.state.period = float(os.environ.get('DT_HMI_PERIOD_MS', '100')) / 1000
app.state.missed_frames = int(os.environ.get('DT_HMI_MISSED_FRAMES', '5'))
app.include_router(router)
app.mount('/', StaticFiles(directory=Path(__file__).resolve().parents[1] / 'hmi', html=True))
