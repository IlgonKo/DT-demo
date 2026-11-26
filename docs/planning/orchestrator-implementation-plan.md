# DT Demo — Orchestrator Implementation Plan

**2026-11-26 | v0.2 | 기반 패키지 선행 개발 반영 · 목표 일정 초안**
관련 문서: [Orchestrator Architecture](https://chatgpt.com/space/page_a5dfae25ee6c81918c25942b651db7f3), [Soft ESC Gap Analysis](https://chatgpt.com/space/page_03103215e4088191bbc5aaf06940a026).

## 1. Milestones

- M1: 2026-12-11 Manual Control + Omniverse Integration. DT/Sync, HMI/Pendant, 가상축 및 Loader Follow, Collision/Stop/Fault.

- M2: 2026-12-25경 Full Operation Integration. Auto, P1~P6 Recipe, Repeat, Parameter/PDO Pairing, State Alignment, 회귀 검증. 공휴일을 고려해 12/24 사전 검증 목표.

## 2. 역할 및 가용성

Omniverse만 별도 담당자. 사용자와 ChatGPT/Codex가 Orchestrator, HMI, Soft ESC 및 Motion Server 연동을 공동 진행한다. 사용자는 설계 결정 및 실제 장비 시험, AI는 접근 가능한 개발 환경에서 코드 분석/구현/자동화 시험/문서 지원, 디버깅은 공동 수행. AI의 독립 백그라운드 개발이나 별도 인력 투입을 가정하지 않는다. 가용 공수 미확정으로 일정은 목표이며 일부 주말 포함.

## 3. 진행 현황 및 통합 개발 일정

### 3.1 진행 현황 (2026-11-26 기준)

Soft ESC와 Motion Server는 DT Demo의 기반 패키지이므로 Application 통합 개발에 앞서 우선 진행했다. Architecture/API 및 ROS2 계약 확정은 아직 완료한 항목이 아니며 11/27 착수 예정이다. 기반 패키지의 개별 개발·검증과 DT Demo 통합 검증은 별도로 관리한다.

| 항목 | 현재 상태 | 근거 및 다음 작업 |
|---|---|---|
| Soft ESC 기반 패키지 | 선행 개발 진행 | 사용자 진행 보고. 저장소에 DT Demo Gap Analysis, 독립 패키지 범위, 공압 FMU 검증 기록 및 Remote I/O 모델 계획, 소스·검증 도구 재정리 반영. RF-015/RF-013 및 Edge #2 검증의 잔여 범위는 계약 검토에서 확인 |
| Motion Server 기반 패키지 | 내부 1.0 기준선 커밋 반영 | 내부 1.0 기준선 및 기능·범위 문서 반영, TD-043~046 후속 작업 등록. DT Demo에 필요한 API와 제약은 11/27부터 확인 |
| Architecture/API 및 ROS2 계약 확정 | 착수 예정 · 11/27 | 공통 Command/Event/State, 장치 매핑, API 및 ROS2 계약 확정 |
| Orchestrator/HMI 구현 | 통합 개발 착수 전 | 계약 확정 후 Core부터 순차 구현 |
| M1/M2 통합 검증 | 미실시 | 기반 패키지 개발 결과를 통합 완료로 처리하지 않음 |

현황 확인에 사용한 로컬 저장소 Commit: Soft ESC `e8ad0b9`, Motion Server `eff4d12`. 이는 진행 기록의 참조이며 통합 검증을 마친 배포 조합은 아니다. 기반 패키지의 전체 완료율이나 RF별 완료 여부는 이 문서에서 추정하지 않는다.

### 3.2 조정 일정

| 기간 (2026년) | 작업 | 완료 목표 | 상태 |
|---|---|---|---|
| 11/25~26 선행 진행, 11/27~30 잔여 범위 확인 | Soft ESC / Motion Server 기반 패키지 | 현재 기능·검증 결과와 RF-015/RF-013/RF-012 잔여 범위 확인, 통합에 사용할 기준 버전 후보 기록 | 선행 개발 진행, 통합 준비 확인 예정 |
| 11/27~30 | 1. Architecture/API 및 ROS2 계약 확정 | 공통 Command/Event/State, 장치 매핑, Motion Server API 및 ROS2 Topic·메시지·단위·Collision 의미 확정 | 11/27 착수 예정 |
| 12/1~4 | Orchestrator Core | Motion Server IF, Device Manager, System Controller | 예정 |
| 12/3~7 | Manual/Pendant | Servo, Jog, PV, PP, Homing, Loader, Stop | 예정 |
| 12/5~9 | HMI/ROS2 | 기본 화면, 가상 상태 Publish, Collision Subscribe | 예정 |
| 12/9~10 | M1 사전 통합 | DT/Sync, 실제/가상 장치, 장애 복구 | 예정 |
| 12/11 | M1 시험 | Manual + Omniverse | 목표 유지 |
| 12/14~17 | Recipe/Auto | Teaching, 저장, Start/Stop/Repeat | 예정 |
| 12/16~20 | Sequencer | Cycle Preparation, Loading, P1~P6/Dwell, Unloading | 예정 |
| 12/18~22 | Device Setup/HMI | Parameter/PDO Pairing, State Alignment, Auto/Setup 화면 | 예정 |
| 12/22~24 | M2 사전 통합 | 전체 운전 및 회귀 검증 | 예정 |
| 12/25경 | M2 시험 | Full Demo | 목표 유지 |

Architecture/API 및 ROS2 계약 확정은 기존 11/25~27에서 11/27~30으로 조정한다. Soft ESC 개발을 일정상 신규 착수로 표시하던 항목은 기반 패키지 선행 진행 및 잔여 검증 확인으로 변경한다. 11/30 계약·통합 준비 검토에서 잔여 작업을 확인하고 12/1 Core 착수 가능 여부를 판단한다.

겹치는 날짜는 별도 개발 인력을 의미하지 않으며 사용자와 ChatGPT/Codex의 작업 전환·검증을 포함한 목표 구간이다. 기반 패키지 잔여 구현은 확인 결과에 따라 다시 배치한다. 11/30까지 필요한 API나 기반 기능이 준비되지 않으면 영향받는 작업과 M1 범위를 재산정하고 미완료 항목을 명시한다.

### 3.3 1번 아이템의 완료 조건

- 공통 Command/Event/State 모델과 상태 소유자, 비동기 실행·취소·Stop/Fault 처리 계약을 문서화한다.
- 실제·가상 장치 식별자, 축/IO 매핑, DT/Sync Routing 및 Pairing 관계를 정리한다.
- 현재 Motion Server API의 연결, Heartbeat, Feedback, 제어권, 명령·응답·오류와 재연결 동작을 확인한다.
- Omniverse 담당자와 ROS2 Topic, 메시지 타입, Joint/IO 이름, 단위 및 Collision 발생·해제 의미를 확인한다.
- 기반 패키지에서 지원하는 기능과 잔여 Gap을 구분하고, Core 구현에 사용할 인터페이스 기준을 기록한다.

## 4. M1 Acceptance Criteria

- [ ] 기존 TCP API 연결/Heartbeat/Feedback 및 제어권 획득·반납

- [ ] Init/Ready/Running/Fault, Stop, 명시적 복구

- [ ] Servo, 단축 Jog, 다축 PV 및 거리 기반 속도 제한, HMI PP, Homing

- [ ] HMI/Pendant 선택 및 입력 처리

- [ ] DT/Sync Routing, 실제/가상 상태 독립 관리

- [ ] 가상 3축 Follow, Valve/Loader IO Follow 및 Manual Loader

- [ ] Collision Feedback, Stop 및 통신 장애 시 자동 재개 금지

M1에는 Parameter Pairing/State Alignment 자동화가 없으므로 초기 위치 및 파라미터를 수동으로 맞춘다. RF-013 지연 시 축 Manual 시험 우선, Loader는 별도 미완료로 기록한다.

## 5. M2 Acceptance Criteria

- [ ] P1~P6 Teaching, 편집, 저장/불러오기, PP 조건 및 Dwell

- [ ] Cycle Preparation, PCB Loading, 경유점 이동, PCB Unloading

- [ ] DT/Sync Auto, Repeat, Cycle Count, 모든 대상 도달/정지 및 센서 확인

- [ ] PP 속도/가감속/SW Limit 양방향 Parameter Pairing 및 readback

- [ ] PDO Mapping/Assignment 양방향 적용 및 프로세스 이미지 검증

- [ ] 실제 위치 기준 가상축 PP 및 Loader State Alignment

- [ ] Stop/Collision/Fault 복구, 자동 재개 금지, Manual 전체 회귀

## 6. 시험 전략

L1: Orchestrator 내부 Mock Interface 및 단위 테스트. L2: 기존 Motion Server Mock Backend로 실제 TCP/API 통합. L3: Motion Server + Soft ESC + 실제 장치 + Omniverse. Mock은 실제 장치 동작의 증명이 아니며 물리 시험은 별도 안전 조치 하에 수행. Omniverse 충돌 검출은 안전 인증 기능이 아니다.

## 7. 외부 의존성 및 Risk

Omniverse 담당자와 11/27부터 ROS2 Topic, Joint/IO 이름, 단위, Collision 의미를 협의하고 11/30까지 확정을 목표로 한다. 담당자 확인 전에는 계약 확정으로 처리하지 않는다. Soft ESC RF-013 Virtual IO가 Loader 시험 선행 조건. RF-015 직선축 동작 검증, RF-012 Edge #2 배포 검증도 포함. 기존 Motion Server API 및 PDO 재구성 제약을 조기 확인한다. 일반 SDO Pairing과 PDO Pairing은 분리한다. HMI 디자인, 상세 Diagnostic, LED/Haptic 세부 완성도는 일정에 따라 후순위. 핵심 제어/Stop/Fault 기능은 축소하지 않는다.

## 8. Repository 및 관리

DT-demo와 Orchestrator/HMI를 동일 Repository에 두는 방향을 제안한다(사용자 최종 확인 전). Motion Server와 Soft ESC는 독립 Repository 유지. 사양/설계/계획/검증 기록과 코드 변경을 함께 관리하며 외부 의존 버전을 기록한다. 이 계획은 기존 DT Demo 계획에 추후 반영할 검토 문서이다.

## 9. 변경 이력

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| v0.1 | 2026-11-25 | Architecture 및 통합 개발 목표 일정 초안 |
| v0.2 | 2026-11-26 | 기반 패키지 선행 진행 현황 반영, 1번 아이템 11/27 착수 및 11/30 확정 목표, 통합 준비 검토 추가. M1/M2 목표 유지 |
