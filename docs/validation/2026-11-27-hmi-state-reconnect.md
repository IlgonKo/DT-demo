# HMI 상태 갱신 중단·재연결 검증

2026-11-27 · L2 · DT Manual · Chrome + Motion Server + Soft ESC

Chrome의 `/api/state` WebSocket에만 갱신 중단과 연결 종료를 재현했다. HTTP와 Motion Server TCP는 실제 시험 환경을 사용했다. 별도 WebSocket 구독으로 가상 X의 위치·Statusword, 제어권, Servo와 Loader 출력을 계측했다. HMI 상태 주기는 100 ms이고 갱신 중단 판단 기준은 5배인 500 ms였다.

| 시험 | 결과 |
|---|---|
| 열린 WebSocket의 상태 메시지 중단 | X Jog 중 상태 프레임을 중단했다. 마지막 프레임 후 약 535 ms에 HMI가 갱신 중단을 표시했다. 약 533 ms에 HTTP Jog 유지 해제 요청이 나갔고, 별도 구독에서 X의 B8=0과 `Ready`를 확인했다. Motion Server 연결과 제어권은 유지됐다. |
| 상태 중단 중 HMI 조작 | Servo On, Homing, Jog, PP, Loader 이동, 조작 소스 전환이 비활성화됐다. 공통 Stop과 전체 Servo Off(Disable)는 각각 HTTP 200으로 접수됐다. 모든 축의 정지·Servo Off와 Loader 정지 확인을 피드백으로 확인했다. |
| 마지막 값과 새 스냅샷 | 상태 중단 중 기존 Servo On과 Loader 밸브 ON, 마지막 수신 시각이 유지됐다. 같은 연결에서 상태 수신을 재개하자 새 전체 스냅샷의 Servo Off, Loader 밸브 OFF, 정지 확인으로 갱신됐다. |
| WebSocket 종료·재연결 | X Jog 중 WebSocket을 종료했다. 약 7 ms 후 일반 명령이 비활성화됐고 약 520 ms 후 새 WebSocket이 열렸다. 첫 전체 스냅샷으로 화면이 갱신됐으며 별도 HTTP 상태 조회는 없었다. |
| 기존 입력 재개 방지 | 재연결 뒤 이전 Jog 입력을 누른 채 약 650 ms 동안 위치가 변하지 않았고 이전 Jog 요청이 반복되지 않았다. 키를 놓은 뒤 새 입력을 주었을 때만 반대 방향 Jog가 허용됐다. |

시험 후 X·Y·Z는 0 mm, Servo Off 상태로 복구했다. Loader는 시험 전 Load 끝단과 해당 밸브 출력 상태로 복구했고 제어권을 반납했다. 단위 테스트 12개와 JavaScript 구문 검사를 통과했다.
