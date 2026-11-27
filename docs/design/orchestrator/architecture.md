# DT Demo Overall 사양

기준일 2026-11-27 · 1차 데모 설계 기준

이 문서는 시연 범위, 상위 구성, 공통 운전 흐름과 통합 검증을 정의한다. 세부 동작은 아래 모듈 사양에서 확인한다.

## 시연 범위와 시스템 구성

PCB Loading → Gantry Path Execution → PCB Unloading 순서로 시연한다. 실제 재료 토출과 Underfill 품질 검증은 시연 범위 밖이다. X1·Y·Z는 구동축이며 X2는 수동 가이드다. Loader는 실린더, 밸브 출력과 양단 센서로 구성한다.

| 구성 | 역할과 배치 |
|---|---|
| Demo Control System | Edge #1의 Orchestrator가 운전 정책을 관리하고 Motion Server가 기존 TCP API와 EtherCAT Master를 제공한다. |
| 실제 장치 | 공통 EtherCAT 버스에 연결된 실제 드라이브와 I/O. |
| Soft ESC | Edge #2에서 가상 EtherCAT Slave와 축·Loader 동작 모델을 실행한다. |
| Omniverse | Workstation에서 가상 장치 상태를 추종하고 충돌을 ROS 2로 보고한다. |
| 조작 장치 | Tablet의 웹 HMI, Edge #1에 Bluetooth로 연결되는 DualSense Pendant. |

Motion Server 한 인스턴스가 실제·가상 Slave의 주기 통신을 유지한다. 각 Slave는 독립 ID를 가지며 모드에 따라 운전 지령 대상만 바뀐다. Sync에서 같은 논리 지령을 보내더라도 EtherCAT 주기와 실제·가상 상태는 각 장치에서 독립적으로 확인한다. 1차 데모의 갠트리 이동은 독립 PP로 구성한다. 실제 안전 기능은 장비의 안전 시스템이 담당한다. [시스템 구성·장치 사양](../../specifications/DT_Demo_System_Specification.md#2-시스템-구성과-책임)

## 모듈별 사양

| 모듈 | 책임 |
|---|---|
| [System Controller](modules/system-controller.md) | 명령 접수, 시스템 상태·모드, Stop·Fault·복구 |
| [Device Manager](modules/device-manager.md) | 논리 장치 매핑, DT/Sync 라우팅, 실제·가상 피드백, Parameter/PDO Pairing, State Alignment |
| [Manual Controller](modules/manual-controller.md) | Servo, Jog, PV, PP, Homing, Loader 수동 동작 |
| [Auto Controller](modules/auto-controller.md) | 자동 운전 준비·사이클 실행·반복·완료 횟수 |
| [Recipe Manager](modules/recipe-manager.md) | 티칭, Recipe 편집·저장·검증·실행 Snapshot |
| [HMI Interface](modules/hmi-interface.md) | HTTP 명령 응답, 웹 HMI의 WebSocket 상태 |
| [Pendant Interface](modules/pendant-interface.md) | DualSense 입력 변환, LED·햅틱 |
| [Motion Server Interface](modules/motion-server-interface.md) | 기존 TCP API, Heartbeat, 응답·피드백·재연결 |
| [Omniverse Interface](modules/omniverse-interface.md) | Omniverse 가상 상태 발행 및 충돌 수신 |

Sequencer는 Auto Controller의 하위 모듈이며 한 사이클을 수행한다. Parameter/PDO Pairing은 Device Manager가 실행한다. State Alignment는 System Controller가 승인하고, Device Manager가 실행과 완료 확인을 맡아 결과를 System Controller에 보고한다. 기능 요구사항은 [시스템 사양 §9](../../specifications/DT_Demo_System_Specification.md#9-parameter-pairing-및-state-alignment)을 따른다.

## 운전 모드와 데이터 흐름

| 구분 | 정책 |
|---|---|
| DT | 가상 장치가 운전 지령을 받는다. |
| Sync | 페어링된 실제·가상 장치가 같은 논리 지령을 받는다. |
| Manual | 선택된 HMI 또는 Pendant가 일반 수동 지령을 생성한다. |
| Auto | HMI 또는 Pendant가 Start를 요청하고 Auto Controller가 저장 Recipe로 운전을 실행한다. |

일반 경로는 HMI/Pendant → System Controller → 실행 모듈 → Device Manager → Motion Server Interface → Motion Server다. 실제·가상 피드백은 Device Manager가 각각 보관하고, HMI와 실행 모듈은 읽기 전용 상태 Snapshot을 사용한다. Omniverse에는 항상 가상 상태만 발행한다. 명시적으로 요청한 Pairing·Alignment는 개별 대상에 접근할 수 있다. DT의 State Alignment에서 실제 Loader 초기 복귀 중 공통 Stop을 접수하면 그 Loader도 정지 대상에 포함하고, 정렬 결과는 실패로 처리한다. [정지와 복구 기준](modules/system-controller.md#공통-stop)

같은 조작은 출처와 인자를 포함한 공통 명령으로 전달한다. 명령과 Recipe는 논리 장치 이름을 사용한다. System Controller가 명령을 접수하고 실행 모듈이 실행 결과를 판단한다. 웹 HMI는 같은 HTTP 요청의 접수·거절 응답과 WebSocket 상태를 사용한다. HMI·Pendant의 Jog/PV 입력이 끊기면 Orchestrator가 해당 동작을 정지시키고, 복구 후에는 새 조작만 받는다.

## 실행 구조와 구현 경계

Function Block 기반 Python 모듈의 Modular Monolith로 구성하며 단일 Orchestrator 프로세스·Container를 사용한다. 모듈 간 직접 호출, 비동기 이벤트 큐, 읽기 전용 상태 Snapshot을 사용한다. 상태마다 변경 책임을 가진 모듈을 하나 둔다. 장치 응답 대기나 블로킹 I/O와 별개로 제어 판단을 계속한다.

Python asyncio, FastAPI/WebSocket, ROS 2 Jazzy/rclpy, YAML 설정, JSON Recipe, Docker는 기술 후보로 기록한다. 내부 ID, 데이터 구조, 모듈 내부 API와 코드 재사용은 합의된 운전 동작을 만족하도록 구현 과정에서 결정한다. 외부 연동 호환성, 운전 동작 또는 검증 범위에 영향이 있는 결정은 별도로 합의한다.

시스템 상태와 모드 변경은 System Controller가, 장치 피드백과 매핑은 Device Manager가, 자동 운전 진행과 반복 집계는 Auto Controller가, Recipe 편집과 저장본은 Recipe Manager가 각각 관리한다.

Orchestrator와 HMI는 DT-demo에서 함께 관리한다. Motion Server와 Soft ESC는 독립 저장소를 유지하고 통합 시험에 사용한 버전을 기록한다. [저장소 구성](repository-strategy.md)

## 단계별 범위와 검증 환경

- **M1**은 수동 운전, HMI·Pendant, DT/Sync, Omniverse Follow 및 Collision/Stop/Fault 통합이다. 처음 제안한 브라우저→가상 X1→상태 표시→Stop→Ready 흐름의 범위는 구현 착수 전에 검토한다.
- **M2**는 티칭·Recipe, Auto와 반복 운전, Parameter/PDO Pairing 및 State Alignment 통합이다.
- **첫 통합 시험 환경**은 사용자가 준비한 Motion Server + Soft ESC 구성이다. 사용자가 설명한 구성에는 실제 축이 연결되어 있지 않다. 시험 실행과 결과 기록은 구현 착수 이후에 진행한다.
- **Phase 2**에서는 기존 CMMT-AS FMU의 Omniverse 물리 연동, Adapter 확장과 Time Gear를 검토한다. Festo AX는 후속 범위다.

## 통합에서 확인할 사항

- 준비된 시험 환경의 접속 정보, DT/Sync 장치 매핑과 운전 대상, Motion Server·Soft ESC 버전을 확인한다.
- 실제·가상 축 Statusword B8과 Loader 끝단 유지 동작, 공통 Stop 2초 기본값을 시험에서 검증한다. Loader의 Stop 출력 동작은 밸브·공압 회로와 가상 모델 구성에 맞춰 확정한다.
- HMI Quick Stop의 명령 경로, 대상 및 시스템 상태 처리를 확인한다. [Motion Server 연동 확인](modules/motion-server-interface.md#연동-확인)
- Omniverse 담당자와 ROS 2 토픽·메시지·단위, USD/채널 매핑, 충돌 발행과 해소 조건을 확인한다. [Omniverse Interface](modules/omniverse-interface.md)

첫 구현 범위는 DT Manual의 가상 X1이다. 시험 단계와 각 Milestone의 판정 기준은 [개발 계획](../../planning/orchestrator-implementation-plan.md)에 있다. 시스템 기능 기준과 결정 이력은 [시스템 사양서](../../specifications/DT_Demo_System_Specification.md)와 [합의 기록](../../agreements/DT_Demo_Working_Agreements.md)을 따른다.
