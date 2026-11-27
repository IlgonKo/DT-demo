# System Controller 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 책임과 명령 접수

Init·Ready·Running·Fault, Target Mode, Operation Mode, Manual Control Source를 관리한다. Motion Server 제어권은 수동 조작 소스와 구분한다. HMI에서 명시적으로 제어권 획득·반납을 요청하고 서버의 현재 상태를 반영한다. 연결·재연결에 따른 자동 획득은 없다.

HMI와 Pendant의 공통 명령에 포함된 출처, 현재 상태·모드, 수동 조작 소스, 제어권, 동작별 장치 준비 조건을 확인한다. HMI의 DT/Sync, Manual/Auto 및 조작 소스 변경은 Ready와 전환 조건을 충족하면 적용한다. 선택된 조작 소스의 조작 방식 변경도 Ready에서 적용한다. 조작 방식은 HMI의 Jog/Positioning, Pendant의 Single/Multi Axis다. 일반 수동 동작은 선택된 소스에서만 접수한다. HMI의 Stop·초기화·Fault 해제는 Pendant가 선택된 동안에도 요청할 수 있다.

접수 판단은 직렬화하고 장치 응답 대기는 실행 흐름에서 처리한다. 실행 중인 동작과 충돌하는 일반 명령은 즉시 거절한다. 매핑이 하나라도 빠졌거나 유효하지 않은 일반 운전 요청도 전체 거절한다. Stop과 Fault 처리는 우선한다.

### State Alignment 승인

명시적인 HMI·Pendant 요청에 대해 Ready 상태와 Motion Server 제어권을 확인한다. 승인 시 Device Manager에 실행을 맡기고 정렬 중 이동은 Running으로 관리한다. DT에서 실제 Loader의 초기 복귀는 승인된 State Alignment 절차에 한해 허용한다. Device Manager의 완료·실패 보고를 받아 시스템 상태와 Fault 전이 여부를 결정한다.

## 상태와 실행 결과

Init은 설정·통신·장치 준비 확인, Ready는 운전 요청 대기, Running은 동작 실행과 정지 확인, Fault는 운전 차단 이상과 복구 대기 상태다. 개별 장치 상태는 Device Manager에서 확인한다.

| 전이 | 조건·결과 |
|---|---|
| 시작 → Init | 설정 로드, 연결 및 장치 구성·Pairing 확인 |
| Init → Ready | 필수 초기화·통신·장치 정지·현재 모드 준비 확인, 운전 차단 Fault 없음 |
| Ready → Running | 유효한 동작 요청과 실행 조건 충족 |
| Running → Ready | 전체 동작·운전 종료 또는 통상 정지 완료 |
| Init / Ready / Running → Fault | 운전 차단 이상 또는 초기화 후 필수 확인 실패 |
| Fault → Ready | 원인 해소, 필요한 장치 Reset, 사용자 확인, 정지·준비 상태 확인 |
| 모든 상태 → Init | 사용자 초기화 요청. 제한 시간 정지 시도 후 Init 진행 |
| Init 중 초기화 요청 | 기존 초기화를 계속 수행하고 중복 시작하지 않음 |

Manual Controller는 수동 동작 한 건, Auto Controller는 Auto Start부터 전체 자동 운전 한 건의 최종 결과를 한 번 보고한다. 대상 실행, 완료·실패·취소, 실패·취소 사유가 포함된다. 현재 유효한 실행의 완료 보고만 상태 전이에 반영한다. 실행 실패의 Fault 전이는 실패 사유와 현재 장치 상태를 함께 확인해 결정한다. 내부 실행 ID 채택과 실행·보고 연결 방식은 구현 단계에서 정한다.

## 공통 Stop

1. Stop을 접수하면 다른 운전보다 우선 처리하고 현재 실행을 취소한다. 실행 모듈에 취소를 전달하여 후속 지령과 Auto 반복 예약을 중단한다.
2. Device Manager를 통해 현재 운전 대상 전체에 정지를 요청한다. DT는 가상 전체, Sync는 실제·가상 전체다. DT의 State Alignment에서 실제 Loader가 초기 끝단으로 복귀 중이면 그 Loader를 정지 요청과 정지 확인 대상에 추가한다. 정렬 작업은 실패로 종료하고 초기 복귀 중 Stop을 원인으로 기록한다.
3. Stop 요청 이후 받은 유효한 피드백으로 대상별 정지를 확인한다. 타이머는 Stop 접수 시점부터 시작하고, 기본값은 2초이며 Orchestrator 설정으로 변경 가능하다.
4. 통상 Stop의 정지 확인 중 Running을 유지한다. 모든 대상이 정지하고 운전 차단 Fault가 없으면 Ready로 전환한다. 제한 시간에 정지가 확인되지 않은 대상은 정지 미확인으로 표시하고 Fault로 전이한다.

정렬 작업의 실패 기록과 시스템 상태 전이를 구분한다. 실제 Loader의 정지를 포함해 공통 Stop의 정지 확인 기준을 적용한다.

Stop 접수 이후 들어온 기존 완료 보고는 완료 횟수 집계, 다음 사이클 시작, 새 실행의 상태 전이에 사용하지 않는다. 예를 들어 취소된 A의 보고가 B 실행 중 도착해도 B에는 반영하지 않는다.

### 대상별 정지 확인

- **축**은 유효한 피드백의 Statusword B8=0으로 즉시 정지 판정한다. 별도 유지 시간은 두지 않는다. 실제·가상 축의 B8 동작을 통합 시험에서 검증하고 실제 속도는 진단·검증에 사용한다. Fault 여부는 별도로 확인한다.
- **Loader**는 Stop 후 유효한 피드백에서 끝단 센서 하나만 ON이며 해당 끝단을 유지하는 실제 공압 회로 또는 가상 모델 동작이 사전 검증된 경우 정지로 판정한다. 양쪽 OFF는 정지 미확인이다. 제한 시간에 이 조건을 충족하지 못하면 Loader 정지 미확인으로 표시한다. 이 표시는 정지를 확인하지 못했다는 뜻이며 회로 고장 원인은 별도 진단 대상이다.

## Fault와 복구

Sync 지령의 일부 접수가 확인되거나 전송 후 응답 제한 시간이 지나 실행 여부가 불명이면 현재 실행을 중단하고 Sync 운전 대상 전체에 공통 Stop을 요청한 뒤 Fault로 전환한다. 불명인 경우 원래 지령을 재전송하지 않고 지령 접수 여부 미확인을 원인으로 기록한다. 대상별 정지 확인과 미확인 표시는 공통 Stop 기준을 적용한다.

Motion Server 소켓 종료 또는 Heartbeat 단절은 통신 Fault로 처리한다. 신규 동작을 막고 실행·반복·대기 지령을 취소한다. 재연결 후 제어권은 HMI에서 새로 요청하며 운전을 시작하려면 복구·준비 확인과 새 명령이 필요하다.

Omniverse 충돌은 Omniverse Interface에서 받아 모드별 Stop·취소·Fault로 처리한다. 충돌 해소용 단축 Jog 예외는 기존 사양을 따른다. Fault 해제는 원인 해소, 필요한 장치 Reset, 사용자 확인, 정지·준비 확인 후 Ready로 전환한다. 충돌 해소 메시지로 자동 전환하거나 운전을 재개하지 않는다.

사용자 초기화는 모든 상태에서 요청할 수 있다. 신규 지령 차단과 실행 취소 후 제한 시간까지 정지를 시도하고 Init에 진입한다. Init 중 중복 초기화는 시작하지 않는다. 초기화 후 정지·준비가 확인되면 Ready로 전환하고, 확인 실패 시 Fault로 전환한다. Homing은 필요한 개별 동작의 실행 조건으로 확인한다.

[운전 모드와 권한](../../../specifications/DT_Demo_System_Specification.md#4-운전-모드와-제어권) · [시스템 상태 및 복구](../../../specifications/DT_Demo_System_Specification.md#5-시스템-상태-및-복구)
