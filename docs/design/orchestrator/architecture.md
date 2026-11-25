# Orchestrator — Software Architecture

**2026-11-25 | v0.1 | 설계 검토 초안**

## 1. 설계 기준

[DT Demo 시스템 사양서 v1.1](https://github.com/IlgonKo/DT-demo/blob/main/docs/specifications/DT_Demo_System_Specification.md). Motion Server는 기존 TCP API 및 EtherCAT 실시간 제어를 담당하고 Soft ESC는 가상 장치 모델을 담당한다. Orchestrator는 상위 운전 정책과 상태를 관리한다.

## 2. 합의된 실행 구조

Modular Monolith, Function Block 기반 독립 Python 모듈, 단일 프로세스 및 단일 Orchestrator Container. Event-driven/async 실행. 모듈 간 직접 함수 호출, 비동기 이벤트 큐, 읽기 전용 상태 Snapshot. 상태별 단일 소유자. 분산 실행을 위한 추가 통신 계층은 도입하지 않는다. Blocking IO는 별도 thread 등으로 격리하며 장시간 작업은 제어 판단을 차단하지 않는다.

## 3. 모듈 구성

| 모듈 | 책임 |
|---|---|
| Pendant Interface | DualSense 연결, 입력 매핑, LED/Haptic, 연결 상태 |
| HMI Interface | Web API, WebSocket, 요청 및 상태 전달 |
| ROS2 Interface | 가상 축/IO Publish, Collision Subscribe |
| Motion Server Interface | 기존 TCP 프로토콜, Heartbeat, 응답, 재연결 |
| System Controller | Init/Ready/Running/Fault, DT/Sync, Manual/Auto, Control Source, Authority, 실행 허가, Stop/Recovery |
| Device Manager | Registry, Pairing, Command Routing, Device State Store, 대상별 완료 판정 |
| Manual Controller | Servo, Jog, PV, PP, Homing, Loader, 거리 기반 PV 속도 제한 |
| Auto Controller | Start/Stop, Cycle Preparation, Repeat, Cycle Count |
| Sequencer | 한 사이클 Loading → P1~P6/Dwell → Unloading, Done/Aborted/Fault |
| Device Setup | Parameter/PDO Pairing 및 State Alignment |
| Recipe Manager | Teaching, 편집, 저장, 조회, 검증, 실행 Snapshot |

## 4. 책임 및 데이터 흐름

HMI/Pendant/ROS2 → System Controller → Operation 모듈 → Device Manager → Motion Server Interface → Motion Server. Feedback은 Device Manager가 실제·가상 상태를 독립 보관하고 HMI/ROS2/운전 모듈에 읽기 전용 Snapshot 제공. DT는 가상 장치만, Sync는 Pairing된 실제·가상 장치에 동일 논리 지령. 명시적 Alignment/Pairing은 개별 대상 접근 허용. Omniverse는 항상 가상 상태 추종. 충돌은 ROS2 → System Controller로 전달하며 Stop/Fault 우선 처리 및 신규 지령 차단, 실행 취소, 정지 확인을 수행한다. 실제 안전 기능을 대체하지 않는다.

## 5. 내부 Interface 원칙

Command는 typed method 및 결과, Event는 비동기 큐, State는 immutable/read-only snapshot. System Controller가 운전 판단을 직렬화하되 장치 응답 대기로 이벤트 처리를 차단하지 않는다. Stop/Fault 이후 대기 중 지령이 실행되지 않도록 취소 및 실행 권한을 검증한다. 모듈별 Protocol/dataclass/Enum 활용은 제안이며 세부 Contract는 후속 합의. Python asyncio, FastAPI/WebSocket, ROS2 Jazzy/rclpy, YAML config, JSON recipe, Docker는 기술 스택 제안.

## 6. ROS2 계약

`/dt/virtual/joint_states` — sensor_msgs/msg/JointState; `/dt/virtual/io_states` — control_msgs/msg/DynamicInterfaceGroupValues; `/dt/validation/collision` — diagnostic_msgs/msg/DiagnosticArray. Joint 이름/단위/IO 매핑 및 Collision 세부 의미는 별도 담당자와 조기 확인.

## 7. Repository 구성 제안 (미확정)

DT-demo에 Orchestrator와 HMI를 함께 유지하고 motion-server 및 ethercat-device-simulator는 기존 독립 Repository로 유지한다. 사양/구현/통합 테스트를 같은 변경 단위로 관리한다. 기존 docs/agreements, docs/specifications, presentations 유지. 추가: docs/design/orchestrator, docs/planning, docs/validation, orchestrator/{core,interfaces,devices,operations,setup,recipes}, hmi, config, recipes, tests/{unit,integration,system}, Dockerfile, compose.yaml. 외부 두 Repository의 검증 버전/commit을 기록한다. 범용 Core의 별도 제품화 요구가 생기면 분리를 재검토한다.

상세 비교표, 목표 디렉터리별 책임, 외부 의존성 버전 기록 및 향후 분리 기준은 [Repository 구성 제안](repository-strategy.md)에 정리한다. 이 구성은 최종 합의 전 검토 초안이다.

## 8. 후속 설계

Public Interface, 공통 Command/Event/State 모델, 동시성 및 취소 계약, 기존 Motion Server TCP 및 Gamepad 코드 재사용 범위를 확정한다.
