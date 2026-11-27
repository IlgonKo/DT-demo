# 가상 X1 수동 운전 검증

2026-11-27 · L2 · DT Manual · 가상 X1 단축

## 시험 환경

사용자가 준비한 Motion Server + Soft ESC 환경에 기존 TCP API로 연결했다. 사전 상태 조회에서 Motion Server Basic 모드 정상 초기화, 직선축 3개, 모듈형 CPX 가상 I/O 한 개를 확인했다. 이 시험에서는 축 인덱스 0을 논리 가상 X1로 사용했다. 사용자 설명 기준 실제 축은 연결되어 있지 않았다. 시험 대상의 배포 커밋은 확인하지 않았다.

## 확인 결과

| 검증 | 결과 |
|---|---|
| 웹 HMI | Chrome에서 화면과 WebSocket의 X1 피드백이 표시됐고 JavaScript 오류가 없었다. |
| 접수와 조작 소스 | HMI/Pendant 선택, 비선택 HMI의 일반 명령 거절, 명시적 제어권 획득·반납을 확인했다. |
| HMI의 X1 명령 경로 | Servo On/Off, PP 이동 완료, Homing 완료, 공통 Stop과 Ready 복귀를 HTTP 명령과 WebSocket 피드백으로 확인했다. |
| Jog 입력 유실 | Jog 유지 입력 전송을 중단하자 정지했다. 이전 입력 키의 유지 메시지로는 움직이지 않았으며, 새 Jog 입력으로 움직인 뒤 공통 Stop으로 정지했다. |
| B8 | 가상 X1에서 이동 중 B8=1, Stop 후 B8=0을 관찰했다. |
| 물리 DualSense | L2로 Servo On, 왼쪽 스틱 우측 입력으로 X1 이동, 스틱 중립에서 정지, L2 해제에서 Servo Off를 확인했다. 시험 후 제어권을 반납했다. |
| 폴더 재구성 후 | 연결부터 PP·Jog·Stop·Homing과 제어권 반납까지 HMI 명령 경로를 다시 실행해 통과했다. Jog 정지·이전 입력 갱신 방지 관련 단위 테스트 3개가 통과했다. |

첫 통합 시험의 최종 상태는 위치 0 mm, Servo Off, 제어권 미보유였다.

## DualSense 단절 재시험

초기 두 번의 Bluetooth 단절 시험에서는 X1 정지가 관찰됐으나 Motion Server TCP가 함께 끊겨 제어권이 회수됐다. 첫 시험에서 서버는 Jog Stop과 PP 모드 복원 후 TCP 종료를 기록했다. 두 번째 시험에서는 Jog Stop 수신 기록 없이 TCP 종료와 제어권 소유 연결 단절에 따른 Quick Stop이 기록됐다. 두 시점 모두 Windows의 Bluetooth HID 단절 이벤트와 일치했다.

DualSense와 별도로 Motion Server에서 Jog Stop을 14회 반복했을 때 응답은 약 109–119 ms, Heartbeat 수신 간격은 최대 172 ms였다. 이 계측에서 수신 간격은 200 ms 이내였다. Pendant의 SDL 핫플러그 처리를 별도 작업 스레드로 분리하고, 재연결 시 중립 복귀 전 유지된 입력을 무시하는 단위 테스트를 추가했다.

**물리 Bluetooth 단절·재연결 재시험 통과.** Jog가 진행 중일 때 Bluetooth 연결을 끊자 X1의 정지 피드백을 확인했다. HMI 상태 샘플에서 분리 감지부터 정지 확인까지 약 102 ms가 걸렸다. Motion Server TCP 세션과 제어권은 단절, 정지, 재연결 및 새 Jog에 걸쳐 유지됐다. 재연결 뒤 2초 이상 X1 위치가 변하지 않았고, 이후 새 L2·스틱 입력에서만 이동했다. 종료 시 Servo Off와 제어권 반납을 확인했다.

재시험 중 Heartbeat 수신 간격은 재연결 구간에서 최대 228.9 ms까지 늘어났다. 이 간격을 수용한 Orchestrator의 수신 대기 500 ms를 기본값으로 적용했다. 서버의 challenge 및 ACK 설정은 유지했다. 단위 테스트 4개가 통과했다.

## 남은 검증

HMI 화면에서의 단절·복구 표시, LED·햅틱, 가상 다축/Loader, 실축 Sync, Omniverse 연동은 후속 범위다. [L2 범위와 M1 완료 기준](../planning/orchestrator-implementation-plan.md#l2-가상-환경-수동-운전-검증-범위)
