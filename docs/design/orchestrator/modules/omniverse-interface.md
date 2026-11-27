# Omniverse Interface 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## ROS 2 연동 계약

Device Manager의 가상 장치 상태를 Omniverse에 제공하고, Omniverse의 충돌 결과를 System Controller에 전달한다. DT와 Sync 모두 Omniverse는 가상 상태를 추종한다. Soft ESC 모델이 축과 Loader 상태를 생성한다. 아래 값은 프로젝트의 내부 연동 기준이다. Omniverse 담당자와 구현 간 토픽·타입·단위 호환성, 실제 USD·I/O 매핑과 충돌 동작을 확인한다. 가상 축·I/O 상태는 Orchestrator의 단일 권한 Publisher 경로에서 발행한다.

| 토픽 | 메시지 타입 | 발행 → 수신 |
|---|---|---|
| /dt/virtual/joint_states | sensor_msgs/msg/JointState | Orchestrator → Digital Twin |
| /dt/virtual/io_states | control_msgs/msg/DynamicInterfaceGroupValues | Orchestrator → Digital Twin |
| /dt/validation/collision | diagnostic_msgs/msg/DiagnosticArray | Digital Twin → Orchestrator |

## 상태 발행

- JointState의 축 이름은 기준안에서 `x1_joint`, `y_joint`, `z_joint`다. 직선축 위치는 m로 발행한다. 속도·힘을 제공하지 않으면 해당 배열은 비워 둔다. USD 관절 매핑, 방향과 원점 오프셋은 설정으로 관리한다.
- I/O는 논리 그룹과 채널 이름을 사용하며, 디지털 값은 0.0(OFF)과 1.0(ON)을 사용한다. Loader 표시는 가상 DI와 연결하고 밸브 표시는 가상 DO와 연결한다. Omniverse 애니메이션은 제어용 DI와 공정 완료 판정에 사용하지 않는다.
- 동일 피드백에서 나온 축·I/O 값은 같은 상태 취득 시각을 사용한다. 원본 시각이 없으면 Orchestrator의 피드백 수신 시각을 사용한다. 실제 제어 시간은 Isaac Sim의 `/clock`에 의존하지 않는다.

## 충돌과 재연결

| 값 | Orchestrator 해석 |
|---|---|
| name=dt/collision, level=2(ERROR) | 충돌 검출. [System Controller의 Stop/Fault 처리](system-controller.md#fault와-복구) |
| 같은 name, level=0(OK) | 유효한 감시 결과의 충돌 해소. 자동 Fault 해제는 하지 않음 |
| WARN / STALE / 미수신 / Publisher 단절 | 충돌 검출 또는 해소로 해석하지 않음 |
| 다른 name의 ERROR | 충돌로 일괄 해석하지 않음 |

| 항목 | 상태 토픽 2종 | 충돌 토픽 |
|---|---|---|
| 발행 | 새 Motion Server Feedback 수신 시 최신 전체 상태 | 검출·해소 변경 시 즉시, 유효한 현재 결과도 주기 발행 |
| 초기 주기 | 약 100ms Feedback에 맞춤 | 약 100ms |
| History / Depth | Keep Last / 1 | Keep Last / 1 |
| Reliability | Reliable | Reliable |
| Durability | Volatile | Volatile |

Digital Twin이 연결되지 않았거나 단절돼도 그 자체로 데모 운전이 차단되거나 Stop/Fault가 발생하지 않는다. 재접속하면 최신 가상 상태부터 발행한다. 충돌 감지·해소 판단은 위 표의 유효 메시지 규칙을 적용한다. ROS 2 발행이나 콜백 지연이 Motion Server 명령과 Heartbeat를 막지 않도록 최신 상태를 사용한다.

복수 충돌 대상, 짧은 검출 유지 조건과 USD·I/O 매핑 실값은 확인이 필요하다. 판정 예시와 메시지 예시는 [시스템 사양 §11](../../../specifications/DT_Demo_System_Specification.md#11-digital-twin-ros-2-인터페이스)에 있다.
