# DT Demo — Orchestrator Implementation Plan

**2026-11-27 | v0.3 | ICEops 논의 기반 후속 확장 계획 반영 · 목표 일정 초안**
관련 문서: [Orchestrator Architecture](https://chatgpt.com/space/page_a5dfae25ee6c81918c25942b651db7f3), [Soft ESC Gap Analysis](https://chatgpt.com/space/page_03103215e4088191bbc5aaf06940a026).

## 1. Milestones

- M1: 2026-12-11 Manual Control + Omniverse Integration. DT/Sync, HMI/Pendant, 가상축 및 Loader Follow, Collision/Stop/Fault.

- M2: 2026-12-25경 Full Operation Integration. Auto, P1~P6 Recipe, Repeat, Parameter/PDO Pairing, State Alignment, 회귀 검증. 공휴일을 고려해 12/24 사전 검증 목표.

M1과 M2는 모두 12월 1차 데모(Phase 1)의 Milestone이다. 이후 Phase 2는 기존 CMMT-AS FMU의 Omniverse 실행·물리 연동 및 Adapter 확장을 검토하는 후속 단계다. 이전 대화에서 12/25 자동운전을 Phase 2로 표현한 부분과 구분하여, 이 문서에서는 M1/M2 명칭으로 일정 혼동을 방지한다. Phase 2의 달력 일정은 Phase 1 완료와 호환성 검증 후 확정한다.

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

## 9. Phase 2 — FMU·Omniverse 연동 및 Adapter 확장

### 9.1 반영 근거와 결정 상태

2026-11-27 「ICEops 개발 주체 설명」 대화와 본 Planning 대화에 공유된 내용을 반영한다. 사용자는 12월에는 기존 계획대로 1차 데모를 마무리하고 이후 확장을 이어가는 방향을 정했다. 기존에 함께 개발한 Festo CMMT-AS Drive FMU를 재사용하는 것이 출발점이며, 새 Drive FMU 개발을 필수 선행 작업으로 잡지 않는다.

| 항목 | 상태 | 계획 반영 |
|---|---|---|
| 12월 1차 데모 우선 완료 | 사용자 결정 | M1/M2 목표와 Acceptance Criteria 유지 |
| 기존 CMMT-AS FMU 재사용 | 기존 개발 자산에 대한 사용자 확인 | 실행 산출물·버전·변수·대상 OS 확인 후 사용 |
| FMU의 Omniverse 실행 및 물리 피드백 | 후속 검토 방향 | 단일 축 PoC부터 단계적으로 검증 |
| NVIDIA ovfmi 사용 | 후보 | 현재 환경 및 FMU 호환성 확인 후 채택 판단 |
| Time Gear | 사용자 제안 · 상세 설계 미확정 | 별도 검증 작업으로 편성 |
| 단일 축 PoC 약 1주 | 이전 assistant 잠정 추정 | 확약 일정이나 완료 기준으로 사용하지 않음 |

ICEops 등 타사 제품의 개발 주체·기능·공개 여부를 우리 구현의 검증 근거로 사용하지 않는다. 우리 데모의 차별점 검증은 실제 제어환경에서 Fieldbus/Device Profile을 거쳐 가상 장치를 구동하고, 같은 운전·Recipe의 가상 검증과 실제 적용을 연결하는 시나리오로 구체화한다. 경쟁 우위의 확정 판단은 비교 근거 확보 후 수행한다.

### 9.2 Phase 1 유지 범위와 Phase 2 목표

| 구분 | Phase 1 — 12월 1차 데모 | Phase 2 — 후속 검토 |
|---|---|---|
| 동작 계산 | Soft ESC 측 모델 실행, Omniverse는 가상 상태 추종 | 기존 Drive FMU를 Omniverse 연동 실행 환경에서 구동하고 물리 피드백 연결 |
| 제어 경로 | Motion Server + Soft ESC + Orchestrator | Fieldbus/Device Profile Adapter와 모델 실행 경계 정리 |
| 운전 기능 | M1 Manual, M2 Auto·Recipe·Pairing·Alignment | 같은 제어 경로의 단일 축 PP와 물리 상호작용 검증부터 시작 |
| 시간 | 기존 실시간 운전 기준 유지 | 실시간 통신과 모델 Simulation Time 사이 Time Gear 검토 |
| 완료 판단 | 기존 M1/M2 Acceptance Criteria | 호환성, 계산 책임, 시간 계약 및 재현 가능한 PoC 결과 |

Phase 2의 목표 실행 위치와 프로세스 구성은 확정 전이다. FMU와 PhysX가 동일 축 운동을 중복 계산·강제하지 않도록 모델 책임을 먼저 정한다. 1차 데모 완료를 FMU·PhysX 연동 완료로 보고하지 않는다.

### 9.3 선행 확인 및 개발 순서

Phase 1 완료 후 아래 순서로 진행한다. Omniverse 담당자와의 역할 분담·가용성은 착수 시 확인하며 별도 추가 개발 인력이나 AI의 독립 백그라운드 작업을 가정하지 않는다.

| 순서 | 작업 | 산출물 및 완료 기준 | 기존 잠정 공수 |
|---|---|---|---|
| P2-0 | 기존 FMU·실행 환경 확인 | FMU 파일/Commit, FMI 버전·방식, 변수 타입·단위·초기화·Reset, OS 바이너리, Kit/Isaac Sim 환경 및 실행 후보 호환성 표 | 미산정 |
| P2-1 | 기존 CMMT-AS FMU 단독 실행 | 대상 환경에서 초기화·Step·종료와 기준 동작 재현, 실행 로그 | 0.5~1일 |
| P2-2 | USD/PhysX 연결 | 변수 매핑·단위·좌표계, 입출력 교환 순서 및 물리 피드백의 계산 책임 확정, 단일 축 검증 | 1~2일 |
| P2-3 | Soft ESC와 모델 양방향 연결 | Adapter 입력·피드백, 상태 전이, Stop/Fault 및 재초기화 동작, 기존 제어 경로로 단일 축 PP 실행 | 2~3일 |
| P2-4 | Time Gear PoC | 시간 계약 및 배율별 재현성·오류·정지·통신 신뢰성 검증 | 별도 산정 |

P2-1~3의 공수는 앞선 대화의 조건부 추정이며 P2-0, 호환성 문제 해결, Time Gear 작업은 포함하지 않는다. 따라서 Phase 2 전체를 1주로 확정하지 않는다. P2-0 결과로 실제 범위·담당·일정을 다시 산정한다. 라이브러리 후보의 버전·라이선스·지원 기능도 채택 시 원문과 실제 실행으로 검증한다.

### 9.4 Time Gear 검토 항목

사용자 제안은 제어환경·Fieldbus 통신을 실시간으로 유지하면서 Adapter가 FMU 쪽 진행 시간을 가속·감속하는 구조다. 배율은 `g = Δt_sim / Δt_wall`로 정의한다. 예를 들어 wall-clock 1 ms마다 모델 시간이 2 ms 진행하면 g=2다. 이는 통신 주기를 두 배 빠르게 만드는 기능과 구분한다.

| 시간 영역 | 설계 검토 원칙 |
|---|---|
| 제어환경 / EtherCAT / Heartbeat / Watchdog | Wall-clock 기준 유지. 통신 장애 판정을 배율로 늘이거나 줄이지 않음 |
| FMU / PhysX | 연결된 모델들이 같은 Simulation Time을 사용하도록 Step 주기·Substep·실행 순서 조율 |
| PP 명령 및 도달 피드백 | 모델의 위치·속도 피드백과 실제 완료 시점을 함께 검증. 배율에 따른 wall-clock 관측 속도 및 추종 오차 의미를 정의 |
| Recipe의 Dwell / 공정 Timeout | 어느 시계를 사용하는지 항목별 명시. 제어환경이 실시간인 상태에서는 전체 Recipe가 동일 배속으로 끝난다고 가정하지 않음 |
| 배율 변경 / Pause / Reset | 허용 시점과 상태 전이, 적분 상태·시간 연속성 및 재초기화 정책을 설계에서 확정 |
| 계산 성능 | 목표 배율을 감당하지 못할 때 Overrun 탐지·기록·처리 정책 정의 |

PP부터 검증하고, CSP/PV 등 연속 지령과의 시간 의미는 별도 검토한다. Phase 1의 실제·가상 동시 지령 운전(Sync)에는 비단위 배율을 적용하지 않는다. Phase 2도 실제 장치를 포함한 동시 운전은 g=1을 기본 검증 조건으로 두고, 가감속은 가상 장치 PoC에서 먼저 평가한다.

Time Gear 시험안은 g=1 기준선, g=0.5 감속, g=2 가속이다. 목표값은 제안이며 FMU·물리엔진의 안정적인 Step 범위와 성능 확인 후 확정한다. 각 조건에서 시뮬레이션 시간/실시간, 위치·속도·도달, Stop/Fault, 통신 Timeout, Reset 및 반복 결과를 기록한다.

### 9.5 현재 Architecture/API 작업에 반영할 경계

11/27~30 계약 검토에서는 장치/운전 상태와 모델 실행 방식을 분리하고, Command/Event/State에 사용하는 Timestamp의 시계와 단위를 명시한다. Fieldbus/Device Profile Adapter, Behavior Model, FMU 실행기 및 Omniverse 연동부의 책임 경계를 기록한다. Phase 2에 필요한 변수 매핑과 모델 실행 위치 변경 가능성을 검토하되 Time Gear 구현이나 FMU 실행 위치 변경을 M1/M2 완료 조건에 추가하지 않는다.

Phase 2 착수 전 P2-0 호환성 표, 단일 축 시험 시나리오, 역할 분담 및 시간 계약을 검토한다. 이후 검증된 조합만 외부 의존 버전으로 기록하고 기존 시스템 사양서의 범위 변경은 별도 합의로 관리한다.

## 10. 변경 이력

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| v0.1 | 2026-11-25 | Architecture 및 통합 개발 목표 일정 초안 |
| v0.2 | 2026-11-26 | 기반 패키지 선행 진행 현황 반영, 1번 아이템 11/27 착수 및 11/30 확정 목표, 통합 준비 검토 추가. M1/M2 목표 유지 |
| v0.3 | 2026-11-27 | ICEops 대화 반영. 12월 M1/M2를 Phase 1로 정리하고 이후 기존 CMMT-AS FMU 재사용·Omniverse 물리 연동·Adapter 및 Time Gear 검토 계획 추가. 추정 공수와 미확정 설계 구분 |
