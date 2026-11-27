# HMI Interface 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 웹 명령

웹 HMI 입력을 출처 HMI와 필요한 인자를 담은 공통 명령으로 변환해 System Controller에 전달한다. 같은 HTTP 요청의 응답은 접수 또는 거절이며, 거절 시 이유를 돌려준다. HMI API에서 `request_id`를 사용하지 않는다. 명령별 실행 결과는 Orchestrator 내부에서 처리하고 화면은 WebSocket 상태를 표시한다.

응답을 받기 전에 연결이 끊기면 접수 여부 미확인으로 표시한다. 재연결 시 첫 WebSocket 상태로 화면을 복구한다. 이전 명령은 자동 재전송하지 않는다.

HMI에서 Jog/PV 조작 입력이 끊기면 진행 중인 해당 동작을 Orchestrator가 정지시킨다. 연결 복구 후 새 조작 입력을 받아야 다시 움직인다.

## 상태 전송과 재연결

- 최초 WebSocket 연결과 재연결에서 최신 전체 Snapshot을 첫 상태 메시지로 즉시 보낸다.
- 이후 설정된 주기마다 최신 전체 Snapshot을 같은 연결에서 순서대로 보낸다. 기본값은 100 ms(10 Hz)다. 상태 변경에 따른 추가 전송은 없다.
- Snapshot에는 Init·Ready·Running·Fault, DT/Sync와 Manual/Auto, 수동 조작 소스와 Motion Server 제어권, 실제·가상 축·I/O, 현재 Fault 및 자동 운전 진행 상태를 포함한다. HMI는 메시지를 받을 때 표시 상태를 교체한다.
- WebSocket 단절을 감지하면 즉시, 연결은 유지되더라도 마지막 유효 Snapshot 이후 전송 주기 × 중단 판단 배수가 경과하면 갱신 중단으로 처리한다. 기본 배수는 5로 기본 주기에선 500 ms다. 전송 주기와 배수는 Orchestrator 설정으로 변경 가능하다.
- 갱신 중단 시 마지막 값과 수신 시각을 표시하고 일반 운전 명령을 차단한다. HTTP 요청이 가능하면 Stop·Disable·Quick Stop은 보낼 수 있고 System Controller가 접수 여부를 판단한다. 최신 Snapshot을 다시 받아 현재 상태를 기준으로 조작 가능 여부를 갱신한다.

## 화면과 조작

화면 전환 후에도 공통 영역을 유지해 현재 상태·Fault 요약·모드·수동 조작 소스·연결·제어권을 표시한다. 제어권 획득·반납과 공통 Stop·초기화·Fault 해제를 제공한다. 모드와 조작 소스는 시스템이 실제 적용한 값을 표시한다. Auto의 조작 주체는 Sequencer로 표시한다.

| 화면 | 표시·조작 | 적용 조건·결과 |
|---|---|---|
| Auto Control | 저장 Recipe 선택, Start·Repeat, 현재 단계·경유점·Cycle 수, 실행 불가 사유 | Auto·Ready 및 실행 조건 확인. Repeat는 Ready에서만 변경 |
| Manual Control | 축 위치·Servo·Homing·Fault, Servo 축별·전체, Jog, PP 축별·선택 축, 축별 Homing, Loader 조작·센서·출력 | HMI Control Source에서 일반 수동 조작. Pendant 선택 시 조작 비활성, 상태 표시 유지 |
| Recipe | 새로 만들기·불러오기·저장·다른 이름 저장, P1~P10 표, 사용 포인트 수 설정, 티칭, 이동 조건, 변경·입력 오류 | 좌표·Dwell은 표, 축별 조건은 선택 행 상세. 편집은 Ready, 위치 등록은 Manual·Ready·정지 |
| Device Setup | 실제·가상 ID Pairing, 양방향 Parameter Pairing, PDO 구성, State Alignment, 작업 상태 | 적용 전 비교, 적용 후 읽기 확인. 실행은 [Device Manager](device-manager.md#parameterpdo-pairing과-state-alignment)가 맡는다. |
| Diagnostics | 연결·EtherCAT·제어권, 실제·가상 축·I/O 비교, Fault 상세·복구 안내, 이벤트 이력 | 모든 상태에서 조회 가능 |

DT Manual의 가상 Loader는 Unload(초기 끝단)와 Load 버튼, 각 센서와 밸브 출력, 현재 감지한 끝단을 표시한다. 공통 Stop의 Loader 정지 확인은 별도 항목으로 표시한다. Loader 이동 버튼은 HMI가 조작 소스이고 제어권과 유효한 Loader 피드백을 확보한 Ready 상태에서 활성화된다. 가상 모델의 끝단 유지 동작은 시험 구성에서 검증한다.

수동 화면의 축 이름은 X·Y·Z로 표시한다. 화면의 X는 논리 축 X1에 대응한다.

Sync 수동 화면에는 실제 위치를 주로 표시하고 가상 위치를 함께 표시한다. HMI의 수동 조작 방식은 Jog/Positioning이다. 상태 스트림의 연결 여부와 Motion Server의 연결·장치 피드백 상태를 구분해 표시한다. Diagnostics의 위치 차이는 실제−가상이다. Digital Twin 연결 단절과 충돌 Fault를 구분해 표시하며 Fault 상세에서 복구 조치를 안내한다. 이벤트 이력에는 Fault 발생·해제, 연결·제어권 변경과 초기화·Pairing·Alignment 작업을 표시한다. [시스템 사양 §12](../../../specifications/DT_Demo_System_Specification.md#12-hmi-기능-사양)
