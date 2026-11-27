# DT-demo

Fieldbus 기반 Digital Twin 데모의 합의 내용, 시스템 사양 및 발표 자료를 관리한다.

## 문서

| 문서 | 용도 |
|---|---|
| [시스템 사양서 — Markdown](docs/specifications/DT_Demo_System_Specification.md) | 기능 요구사항, 실행 조건, 절차, 완료·실패 판정 및 인터페이스 |
| [시스템 사양서 — Word](docs/specifications/Festo_DT_Demo_System_Specification_v2.docx) | 편집 가능한 사양서, v1.1 |
| [시스템 사양서 — PDF](docs/specifications/Festo_DT_Demo_System_Specification_v2.pdf) | 공유·열람용 사양서, v1.1 |
| [합의 작업 문서](docs/agreements/DT_Demo_Working_Agreements.md) | 상세 합의·결정 기록 및 구현 시 확정 항목 |
| [Overview & Architecture — PowerPoint](presentations/Festo_DT_Demo_Overview_Architecture_v5.pptx) | 10장. Detail Specification 제외 |
| [관계도](docs/diagrams) | 시스템·네트워크·상태 관계도의 Mermaid 원본과 PNG |
| [DT Demo Overall 사양 및 모듈별 사양](docs/design/orchestrator/architecture.md) | 데모 범위, 상위 구조, 공통 운전 흐름과 모듈별 문서 |
| [Orchestrator Implementation Plan](docs/planning/orchestrator-implementation-plan.md) | 12월 Milestone, 역할 분담 및 Acceptance Criteria 초안 |
| [Repository 구성](docs/design/orchestrator/repository-strategy.md) | Repository 비교, 목표 구조 및 외부 버전 관리 방안 |

## 데모 범위

- 공정: PCB Loading → Gantry Path Execution → PCB Unloading. 실제 재료 토출은 제외한다.
- Demo Control System: Orchestrator + 기존 Motion Server.
- Soft ESC가 가상 장치 동작 모델과 I/O 응답을 계산한다.
- DT는 가상 장치, Sync는 실제·가상 장치에 같은 논리 지령을 전달한다.
- Omniverse는 모든 모드에서 가상 장치 상태를 추종한다. Digital Twin 연결에는 ROS 2를 사용한다.
- Festo AX, Omniverse 내 장치 모델 통합, CSP·축간 보간·블렌딩은 1차 범위에서 제외한다.

## 가상 X1·Y·Z 및 Loader 수동 운전

현재 구현 범위는 DT Manual 모드의 가상 X1·Y·Z 및 Loader다. Python 3.11 이상에서 실행한다. 연결할 Motion Server가 사용자가 준비한 가상축 전용 시험 구성인지 확인한 뒤, 프로젝트 루트에서 실행한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DT_MOTION_HOST = '<시험 Motion Server 주소>'
$env:DT_MOTION_PORT = '15000'
$env:DT_X1_AXIS = '0'
$env:DT_Y_AXIS = '1'
$env:DT_Z_AXIS = '2'
.\.venv\Scripts\python.exe -m uvicorn orchestrator.app:app --host 127.0.0.1
```

브라우저에서 로컬 포트 8000을 열고 HMI에서 제어권을 명시적으로 획득한다. X1·Y·Z의 서로 다른 Axis 인덱스를 시험 구성에서 확인해 지정한다. HMI에서 여러 축에 목표 위치를 입력하고 선택 축 PP를 실행할 수 있다. Pendant를 사용할 프로세스는 DualSense가 연결된 호스트에서 `DT_PENDANT=1`을 설정해 실행한다. 필요하면 SDL 인덱스를 `DT_PENDANT_STICK`, `DT_PENDANT_Y`, `DT_PENDANT_Z`, `DT_PENDANT_TRIGGER`, `DT_PENDANT_HOME`, `DT_PENDANT_STOP`으로 바꾼다. 다축 PV는 HMI에서 Pendant 모드를 선택한 뒤 L2를 누르고 왼쪽 스틱 좌우는 X1, 왼쪽 스틱 상하는 Y, 오른쪽 스틱 상하는 Z로 조작한다.

Jog/PV 유지 입력이 500 ms 동안 도착하지 않으면 해당 동작에 Stop을 요청한다. Motion Server Heartbeat challenge 수신 대기 기본값은 500 ms다. 이 값은 서버의 ACK 제한과 별개이며 `DT_MOTION_HEARTBEAT_TIMEOUT`(초)으로 설정한다. 이 초기 구현의 상태 발행 기본값은 100 ms, 갱신 중단 판단 배수는 5다. `DT_HMI_PERIOD_MS`, `DT_HMI_MISSED_FRAMES`, `DT_STOP_SECONDS`를 환경 변수로 조정할 수 있다. PV 기본 최대 요청 속도는 축당 10 mm/s이며 `DT_PV_SPEED_MM_S`로 설정한다. `DT_PV_BOUNDS_MM`으로 서버 위치 한계 안의 더 좁은 작업 범위를 적용할 수 있다. 공통 Stop은 가상 세 축과 구성된 가상 Loader에 적용한다. [가상 3축 검증 기록](docs/validation/2026-11-27-virtual-xyz-manual.md) · [가상 X1 검증 기록](docs/validation/2026-11-27-virtual-x1-manual.md)

Loader 시험 구성은 `DT_LOADER_CONFIG=config/virtual-loader-soft-esc.json`으로 활성화한다. Soft ESC에서 Loader 모델과 같은 I/O 채널 연결을 확인한다. HMI의 가상 Loader에서 초기·반대 끝단을 조작하고 센서·밸브 출력·정지 확인 상태를 볼 수 있다. DualSense는 스틱 중립, L2 해제 상태에서 L1으로 초기 끝단, R1으로 반대 끝단을 지령하고 ○(Circle)로 공통 Stop을 요청한다. 물리 SDL 입력은 `orchestrator/interfaces/pendant/device_profiles.json`, 동작 할당은 같은 폴더의 `config.json`을 사용한다. 필요하면 `DT_PENDANT_CONFIG`로 별도 동작 설정을 지정한다.

5/2 메모리 밸브 모델은 Stop으로 출력을 해제해도 기존 방향을 유지한다. Orchestrator는 새 피드백에서 검증된 끝단 하나만 ON이며 두 출력이 모두 OFF일 때 Loader 정지를 확인한다. [가상 Loader 검증 기록](docs/validation/2026-11-27-virtual-loader-manual.md)

## 기준 및 문서 관리

현재 시스템 사양 기준일은 2026-11-27이다. 시스템 사양서는 합의 내용을 구현 요구사항으로 재구성한 문서이며, 합의 작업 문서의 단순 변환본과 구분한다.

설계 논의 중에는 합의 기록과 Markdown 시스템 사양서를 갱신한다. 전체 변경이 확정되면 Word·PDF 배포본을 같은 내용으로 일괄 갱신한다. 구현 시 확정할 형번·수치·기구 조건은 사양서 15장의 TBD로 관리한다. PPT에는 Overview와 Architecture만 반영한다.

이 저장소의 최초 커밋에는 문서와 관계도만 포함한다. Motion Server 및 Soft ESC 구현 코드는 포함하지 않는다.
