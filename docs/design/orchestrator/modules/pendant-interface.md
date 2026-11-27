# Pendant Interface 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 입력과 권한

Edge #1에 연결된 DualSense의 연결 상태와 버튼·스틱·Trigger 입력을 읽는다. 물리 입력 정의와 기능 매핑을 분리하고, 중복 할당과 알 수 없는 입력을 검증한다. 물리 프로필은 `device_profiles.json`의 SDL 입력→논리 입력 매핑, 기능 설정은 `config.json`의 논리 입력→기능 매핑을 기준으로 한다. 버튼 배치는 설정한다. 축 방향, Deadzone, 속도 단계와 Trigger 임계값은 설정한다. 기존 Gamepad Control Panel의 구조는 구현 시 참고한다.

같은 기능의 HMI 조작과 같은 공통 명령을 생성하며 출처를 Pendant로 지정한다. System Controller가 접수와 권한을 판단한다. Pendant의 조작 범위에는 별도 Motion Server 제어권 획득·반납이나 DT/Sync·Manual/Auto·Control Source 변경이 포함되지 않는다.

| 구분 | 기능 |
|---|---|
| 수동 | Trigger Servo On/Off, Single/Multi 전환, 선택 축 변경, 단축 Jog, 다축 PV, 속도 단계 변경, 선택 축 Homing, Loader 이동 |
| 공통 | Stop, Fault 해제, 초기화 |
| 티칭 | P1~P10 선택, 현재 위치 등록 |
| 설정 실행 | Parameter Pairing 방향 선택·실행, State Alignment 실행 |
| 자동 운전 | HMI에서 선택한 Auto 모드·저장 Recipe의 Auto Start |

일반 수동 조작에는 Manual 및 Pendant 선택이 필요하다. Single/Multi Axis 조작 방식 변경은 Ready에서 허용한다. Auto Start는 HMI에 설정된 Auto 모드와 저장 Recipe를 사용한다. 공통 Stop·복구, 티칭, 설정 실행은 각 기능의 허용 조건을 적용한다. Trigger의 직접 Servo On/Off와 스틱에 따른 Jog/PV 실행은 [Manual Controller](manual-controller.md) 사양을 따른다.

Jog/PV 조작 중 Pendant 입력이 끊기면 해당 동작을 Orchestrator가 정지시킨다. 재연결 후에는 새 조작 입력으로만 운전을 시작한다.

## LED와 햅틱

| 표시 상태 | LED | 햅틱 |
|---|---|---|
| Fault | 빨간 점멸 | 축 Fault 발생 시 강한 진동 1회 |
| Warning | 주황 점멸 | 없음 |
| Homing | 보라 점멸 | 별도 Homing 진동 없음. 축 이동 피드백은 적용 |
| 이동 | Festo Blue | 축 이동 시 약한 연속 진동 |
| Servo Enable·정지 | 초록 | 없음 |
| 제어권 보유·Servo Disable | 청록 | 없음 |
| 연결·제어권 없음 | 파랑 | 없음 |

LED 우선순위는 표의 위에서 아래 순서다. 이동 표시는 축 피드백을 기준으로 DT는 가상축, Sync는 실제·가상축 중 하나라도 이동하면 활성화한다. 햅틱 입력은 축 Fault와 축 이동에 한정한다. 가동 여부와 색상·밝기·점멸·진동 강도는 설정한다. 출력 실패는 데모 운전에 영향을 주지 않는다. [시스템 사양 §13](../../../specifications/DT_Demo_System_Specification.md#13-pendant-기능-및-설정)
