# Manual Controller 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 실행 책임

System Controller가 승인한 수동 동작을 실행하고, 논리 장치 대상으로 Device Manager에 지령을 전달한다. 일반 수동 지령은 Manual 운전 모드와 선택된 수동 조작 소스의 조건을 적용한다. HMI와 Pendant는 서로 다른 입력 방식을 공통 명령으로 전달한다.

| ID | 기능 | 입력·처리 | 완료·정지 |
|---|---|---|---|
| MAN-01 | Pendant Single Axis | 선택한 X1·Y·Z 중 한 축에 Jog 지령 | 중립 시 Jog 정지 |
| MAN-02 | Pendant Multi Axis | 스틱 입력으로 축별 PV 속도 벡터 생성 | 중립 시 정지 요청. Enable 해제는 직접 Servo Off |
| MAN-03 | HMI Jog | 축별 - / + 버튼과 Jog 속도 | 누르는 동안 이동, 놓으면 정지 요청 |
| MAN-04 | HMI Positioning | 축별 목표 위치 및 PP 조건. 축별 실행 또는 선택 축 함께 실행 | 대상 축의 도달·정지 확인. 보간·동시 도착 없음 |
| MAN-05 | Servo | HMI 축별·전체 On/Off. Pendant Trigger–Enable 직접 연결 | 실제 구동 상태 Feedback 확인 |
| MAN-06 | Homing | HMI 축별, Pendant 단축 선택 축 요청 | Homing 완료 또는 실패·타임아웃을 확인해 System Controller에 보고 |
| MAN-07 | Loader | Unload(초기 끝단) / Load 이동 요청 | 해당 대상의 끝단 센서 확인 |

## Pendant 속도 제어

Trigger 누름·해제는 Servo On/Off에 직접 연결한다. 다축 PV는 스틱을 축별 속도 벡터로 변환한 뒤 각 축의 현재 위치와 S/W Limit까지의 거리를 고려해 속도를 제한한다. 현재 가상축 구현은 서버의 위치·속도 한계와 PP 프로파일 감속 값을 읽고 축별 실제 위치와 속도를 반영한다. 기본 계산에는 반응 시간 여유 0.25초와 위치 여유 0.25 mm를 적용한다. `DT_PV_BOUNDS_MM`을 지정하면 서버 한계와 교집합을 사용한다. Sync의 실제·가상 위치 반영은 후속 검증 범위다.

## 완료·취소

PP는 모든 대상 축의 목표 도달과 정지를 확인한다. Homing은 Homing 상태, Loader 이동은 해당 끝단 센서, Servo는 Enable/Disable 피드백을 사용한다. 1차 가상 Loader는 목표 끝단과 선택된 밸브 출력을 확인하면 이동을 완료한다. 정상 완료 후 밸브 출력은 다음 Loader 이동 지령 또는 공통 Stop까지 유지한다. DT는 가상 대상, Sync는 실제·가상 대상 모두에서 동작별 결과를 확인한다. PP·Homing 타임아웃의 공통 Stop과 Fault 전이는 System Controller가 처리한다. Jog·PV는 조작 입력이 유지되는 동안만 실행한다. HMI 또는 Pendant의 조작 입력이 끊기면 해당 Jog/PV 동작의 후속 지령을 중단하고 대상 장치에 정지를 요청한다. 입력이 복구되면 새 조작부터 시작한다. Jog·PV에는 목표 도달 완료 타임아웃을 두지 않는다. PP 허용 오차와 동작별 타임아웃은 구성 및 시험을 통해 정한다.

수동 동작 한 건당 최종 결과를 한 번 System Controller에 보고한다. 대상 실행, 완료·실패·취소 여부와 실패·취소 사유를 포함한다. 취소를 받으면 해당 실행의 후속 지령을 중단한다. 공통 Stop 요청과 정지 확인 후 시스템 상태 전이는 [System Controller](system-controller.md)가 맡는다. 티칭을 위한 축 이동은 이 모듈이, 현재 좌표 등록은 [Recipe Manager](recipe-manager.md)가 맡는다.

[수동 운전 사양](../../../specifications/DT_Demo_System_Specification.md#6-manual-control)
