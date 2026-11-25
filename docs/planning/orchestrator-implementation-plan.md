# DT Demo — Orchestrator Implementation Plan

**2026-11-25 | v0.1 | 목표 일정 초안**
관련 문서: [Orchestrator Architecture](https://chatgpt.com/space/page_a5dfae25ee6c81918c25942b651db7f3), [Soft ESC Gap Analysis](https://chatgpt.com/space/page_03103215e4088191bbc5aaf06940a026).

## 1. Milestones

- M1: 2026-12-11 Manual Control + Omniverse Integration. DT/Sync, HMI/Pendant, 가상축 및 Loader Follow, Collision/Stop/Fault.

- M2: 2026-12-25경 Full Operation Integration. Auto, P1~P6 Recipe, Repeat, Parameter/PDO Pairing, State Alignment, 회귀 검증. 공휴일을 고려해 12/24 사전 검증 목표.

## 2. 역할 및 가용성

Omniverse만 별도 담당자. 사용자와 ChatGPT/Codex가 Orchestrator, HMI, Soft ESC 및 Motion Server 연동을 공동 진행한다. 사용자는 설계 결정 및 실제 장비 시험, AI는 접근 가능한 개발 환경에서 코드 분석/구현/자동화 시험/문서 지원, 디버깅은 공동 수행. AI의 독립 백그라운드 개발이나 별도 인력 투입을 가정하지 않는다. 가용 공수 미확정으로 일정은 목표이며 일부 주말 포함.

## 3. 통합 개발 일정

| 기간 | 작업 | 완료 목표 |
|---|---|---|
| 11/25~27 | Architecture/API 및 ROS2 계약 확정 | 공통 Command/Event/State, 장치 매핑, API 확인 |
| 11/26~12/2 | Soft ESC RF-015/RF-013 | 가상축 Manual, Virtual IO 및 Loader |
| 12/1~4 | Orchestrator Core | Motion Server IF, Device Manager, System Controller |
| 12/3~7 | Manual/Pendant | Servo, Jog, PV, PP, Homing, Loader, Stop |
| 12/5~9 | HMI/ROS2 | 기본 화면, 가상 상태 Publish, Collision Subscribe |
| 12/9~10 | M1 사전 통합 | DT/Sync, 실제/가상 장치, 장애 복구 |
| 12/11 | M1 시험 | Manual + Omniverse |
| 12/14~17 | Recipe/Auto | Teaching, 저장, Start/Stop/Repeat |
| 12/16~20 | Sequencer | Cycle Preparation, Loading, P1~P6/Dwell, Unloading |
| 12/18~22 | Device Setup/HMI | Parameter/PDO Pairing, State Alignment, Auto/Setup 화면 |
| 12/22~24 | M2 사전 통합 | 전체 운전 및 회귀 검증 |
| 12/25경 | M2 시험 | Full Demo |

겹치는 날짜는 별도 개발 인력을 의미하지 않으며 작업 전환/검증을 포함한 목표 구간이다. 선행 기능 완료에 따라 순차적으로 조정한다.

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

Omniverse 담당자와 11/27까지 ROS2 Topic, Joint/IO 이름, 단위, Collision 의미 확인. Soft ESC RF-013 Virtual IO가 Loader 시험 선행 조건. RF-015 직선축 동작 검증, RF-012 Edge #2 배포 검증도 포함. 기존 Motion Server API 및 PDO 재구성 제약을 조기 확인한다. 일반 SDO Pairing과 PDO Pairing은 분리한다. HMI 디자인, 상세 Diagnostic, LED/Haptic 세부 완성도는 일정에 따라 후순위. 핵심 제어/Stop/Fault 기능은 축소하지 않는다.

## 8. Repository 및 관리

DT-demo와 Orchestrator/HMI를 동일 Repository에 두는 방향을 제안한다(사용자 최종 확인 전). Motion Server와 Soft ESC는 독립 Repository 유지. 사양/설계/계획/검증 기록과 코드 변경을 함께 관리하며 외부 의존 버전을 기록한다. 이 계획은 기존 DT Demo 계획에 추후 반영할 검토 문서이다.
