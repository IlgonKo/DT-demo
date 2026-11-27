import asyncio
from typing import Literal

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, FiniteFloat

from orchestrator.core.system_controller import CommandRejected

router = APIRouter()


class Command(BaseModel):
    action: Literal['authority', 'enable', 'disable', 'home', 'pp', 'jog', 'stop', 'recover', 'source']
    enabled: bool | None = None
    direction: Literal['positive', 'negative'] | None = None
    position: FiniteFloat | None = None
    source: Literal['HMI', 'Pendant'] | None = None
    hold: str | None = Field(default=None, min_length=1, max_length=80)


class HoldInput(BaseModel):
    hold: str = Field(min_length=1, max_length=80)
    pressed: bool


@router.post('/api/command')
async def command(payload: Command, request: Request):
    controller = request.app.state.controller
    try:
        if payload.action == 'source':
            if payload.source is None:
                raise CommandRejected('조작 소스를 지정하세요.')
            controller.change_source(payload.source)
        else:
            fields = {
                'authority': ('enabled',), 'jog': ('direction', 'hold'), 'pp': ('position',),
            }.get(payload.action, ())
            data = {name: getattr(payload, name) for name in fields}
            if any(value is None for value in data.values()):
                raise CommandRejected('명령의 필수 입력값을 지정하세요.')
            controller.dispatch(payload.action, **data)
    except CommandRejected as error:
        return rejected(error)
    return {'accepted': True}


@router.post('/api/hold')
async def hold(payload: HoldInput, request: Request):
    try:
        request.app.state.controller.hold('HMI', payload.hold, payload.pressed)
    except CommandRejected as error:
        return rejected(error)
    return {'accepted': True}


def rejected(error):
    return JSONResponse({'accepted': False, 'reason': str(error)}, status_code=409)


@router.websocket('/api/state')
async def state(websocket: WebSocket):
    await websocket.accept()
    settings = websocket.app.state

    async def publish():
        while True:
            snapshot = settings.controller.snapshot()
            snapshot['period_ms'] = settings.period * 1000
            snapshot['missed_frames'] = settings.missed_frames
            await websocket.send_json(snapshot)
            await asyncio.sleep(settings.period)

    async def wait_disconnect():
        while True:
            if (await websocket.receive())['type'] == 'websocket.disconnect':
                return

    tasks = [asyncio.create_task(publish()), asyncio.create_task(wait_disconnect())]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (WebSocketDisconnect, RuntimeError, OSError):
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
