# Device Manager 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 장치 Registry와 매핑

내부 명령과 Recipe가 사용하는 논리 이름 X1·Y·Z·Loader에 실제·가상 장치 식별자를 매핑한다. 동일한 논리 이름의 실제·가상 장치는 각자의 식별자와 상태를 유지한다. Loader는 밸브 출력과 양단 센서 I/O를 매핑한다. 실제 장치 식별자, 가상 식별자와 I/O 채널 값은 통합 대상 구성으로 확인한다.

## 지령 라우팅

| 요청 | 대상 |
|---|---|
| DT 일반 운전 | 해당 논리 장치의 가상 대상 |
| Sync 일반 운전 | 해당 논리 장치의 실제·가상 대상 모두 |
| 공통 Stop | DT의 가상 운전 대상 전체 또는 Sync의 실제·가상 운전 대상 전체. DT에서 State Alignment로 초기 복귀 중인 실제 Loader도 포함 |
| 명시적 Pairing·Alignment | 승인된 요청에 지정된 개별 대상 |

일반 지령 전송 전 현재 모드에서 요청에 필요한 매핑 전체를 확인한다. 매핑 누락·무효 시 System Controller가 전체를 거절할 수 있도록 문제를 반환한다. 예를 들어 Sync에서 가상 X1이 빠졌다면 실제 X1에도 운전 지령을 보내지 않는다.

실행 중 일부 대상이 지령을 거부하거나 접수 여부가 불명이면 확인 가능한 결과를 대상별로 전달한다. 전체 Stop과 Fault 판단은 [System Controller](system-controller.md)가 담당한다.

## 피드백

Motion Server Interface에서 전달받은 실제·가상 축과 I/O 피드백을 각각 보관해 읽기 전용 Snapshot으로 제공한다. 운전 모듈은 이를 사용해 동작 완료를 판단한다. System Controller는 공통 Stop의 정지를, Recipe Manager는 티칭 좌표를, HMI Interface와 Omniverse Interface는 각 소비자에 필요한 표시 상태를 확인한다.

Loader의 가상 신호 흐름은 가상 DO → Soft ESC의 밸브·실린더 모델 → 가상 DI다. 양단 센서 OFF는 중간 위치·방향을 확정할 근거로 사용하지 않는다. 가상 Loader 시험에서는 초기·반대 방향 출력을 매핑하고 방향 명령 시 비활성 출력을 먼저 해제한다. 공통 Stop은 두 출력을 해제하며 이후 수신한 유효한 피드백을 정지 판정에 사용한다. [장치 및 I/O 사양](../../../specifications/DT_Demo_System_Specification.md#3-장치-및-io-사양)

## Parameter/PDO Pairing과 State Alignment

System Controller가 명시적인 HMI·Pendant 요청의 Ready 상태와 Motion Server 제어권을 확인한 뒤 Device Manager에 실행을 맡긴다. DT·Sync 모두 가능하고 수동 조작 소스 선택과 무관하다. 장치 ID 매핑 설정과 정렬·파라미터 작업의 조작은 HMI의 [Device Setup 화면](hmi-interface.md#화면과-조작)에서도 제공한다. 모드 전환만으로 실행하지 않는다.

### Parameter/PDO Pairing

실제→가상 및 가상→실제 방향으로 복사한다. 페어링된 대상의 정지를 확인하고 원본 값과 대상 현재 값을 비교해 적용한 뒤, 대상 값을 다시 읽어 검증한다. 결과와 실패 원인은 System Controller에 전달한다.

| 구분 | 적용 항목 |
|---|---|
| Motion Parameters | PP 속도·가속도·감속도와 S/W Limit |
| PDO Configuration | RxPDO·TxPDO Mapping과 PDO Assignment |

PDO는 항목·순서·비트 길이·크기·의미를 맞추고, Slave 주소와 프로세스 이미지 오프셋은 장치별로 관리한다. 일반 SDO 파라미터 적용과 EtherCAT 상태 전환·프로세스 이미지 갱신이 필요한 PDO 재구성은 각각 검증한다. 기존 API 지원 범위와 전환 순서는 구현 단계에서 확인한다.

### State Alignment

System Controller의 승인에 따라 Device Manager가 절차를 실행하고, 장치 피드백으로 완료 조건을 확인한다.

1. 실제 기준 장치의 정지를 확인한 뒤 축 위치와 Loader 양단 센서를 읽는다.
2. 실제 Loader의 양단 센서가 모두 OFF이면 초기 끝단 복귀를 요청하고 센서를 확인한다. 명시적 Alignment의 이 단계는 DT에서도 허용한다.
3. 대상 가상축의 Servo를 Enable하고 실제 Enable 피드백을 확인한 뒤, 실제축 위치를 목표로 일반 PP 이동을 실행한다. 실제 Loader 상태에 맞춰 가상 Loader에 I/O 지령을 보낸다.
4. 대상 가상축의 위치 도달·정지와 Loader 센서 일치를 확인해 완료를 판정한다. 완료 또는 실패와 실패 사유를 System Controller에 보고한다.

DT에서 실제 Loader 초기 복귀 중 공통 Stop을 받으면 복귀를 중단하고 실제 Loader의 Stop을 실행한다. 이 경우 정렬 작업을 실패로 종료해 사유를 보고하고, 실제 Loader의 정지 여부도 System Controller에 전달할 피드백에 포함한다.

Alignment는 기존 Motion Server의 PP·I/O 경로를 사용한다. 이동은 Running 상태로 처리한다. HMI는 작업 진행 상태와 읽기 확인 정보를 표시한다. 위치 허용 오차와 작업별 타임아웃은 구현 및 시험에서 확인한다. 자동 Pairing·Alignment는 M2 통합 범위다. [상세 시스템 사양](../../../specifications/DT_Demo_System_Specification.md#9-parameter-pairing-및-state-alignment)
