# Motion Server Interface 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 경계와 TCP 계약

독립 모듈로 기존 Motion Server TCP API를 사용한다. 연결, Heartbeat/ACK, 요청·응답 매칭과 재연결을 담당한다. Servo, Jog/PV, PP, Homing, Stop, I/O, 파라미터, 초기화·진단에 필요한 기존 API의 지원 범위를 확인한다.

TCP 요청에 포함한 `request_id`를 서버의 success/fail 응답과 연결한다. 비동기 동작의 success는 서버의 요청 수락을 의미한다. 축과 I/O의 후속 피드백·상태는 Device Manager에 전달하며, 완료 판단은 해당 실행 모듈이 수행한다. 응답과 상태는 같은 TCP 연결에서 수신한다. 연결의 Heartbeat challenge는 기존 전송 규칙에 따라 ACK하며 운전 요청과 따로 처리한다.

| 항목 | 사양 |
|---|---|
| 프로토콜 | 기존 Motion Server TCP API |
| 일반 명령 | 새 명령·변경이 필요할 때 전송 |
| Feedback | 기존 서버 설정 주기 사용. 초기 설정 약 100ms |
| 생존 감시 | 기존 서버 Heartbeat / ACK만 사용 |
| 서버 Heartbeat | 현재 서버 설정 유지. 기존 기본값은 challenge 주기 50 ms, 서버의 ACK 대기 200 ms |
| 클라이언트 수신 대기 | Orchestrator 측 challenge 수신 제한 기본 500 ms. 수신한 challenge에는 즉시 ACK하며 소켓 종료를 감지하면 즉시 연결 종료로 처리 |
| 장치 Feedback | Feedback 주기와 연결 생존 감시는 독립적이며, Feedback 전용 watchdog은 사용하지 않음 |

## 연결 복구와 타임아웃

| 상황 | 처리 |
|---|---|
| 소켓·Heartbeat 경로로 연결 종료 | Orchestrator 통신 Fault, 신규 동작 차단, 실행·반복·대기 명령 취소 |
| 제어권 소유 연결 종료 | 기존 서버가 전체 구성 축 지령 정리·Disable/Quick Stop 후 제어권 해제 |
| 비소유 연결 종료 | 해당 종료만으로 축 동작 변경 없음 |
| 재연결 | 상태·진단 및 Heartbeat 통신 재개. HMI에서 새 제어권 요청 필요 |
| 운전 재개 | 복구·준비 확인 후 새 명령. 자동 Enable·지령 재실행 없음 |

장치 동작 지령의 응답 타임아웃은 결과 불명으로 전달한다. 이미 전송한 동작 지령은 자동 재전송하지 않는다. Sync에서 일부 대상만 접수됐거나 접수 여부가 불명일 때의 공통 Stop과 Fault는 [System Controller](system-controller.md)가 처리한다. 서버 연결 종료 시 기존 축 처리와 Loader I/O 출력을 구분한다. 연결 종료만으로 서버가 I/O 출력을 자동 초기화하지 않는다.

## 연동 확인

DT/Sync별 대상만 Stop 요청을 받도록, 현재 Motion Server에서 사용할 축 정지 API와 Loader I/O 동작을 매핑한다. HMI의 Quick Stop은 상태 갱신 중단 중에도 요청할 수 있다. 확인한 Motion Server 소스 `ea7ed1e`에서는 제어권 반납·연결 종료 경로의 Quick Stop 동작을 확인했다. HMI가 호출할 독립 Quick Stop 명령 경로와 적용 대상·시스템 상태 처리는 통합 대상 버전에서 확인한다.

Motion Server의 동작 중 명령 거부 기능은 추가 예정으로 기록한다. 통합 대상 버전에 포함된 기존 기능을 사용한다. 기존 Python 클라이언트 재사용 범위, 구체적인 명령 스키마와 응답 시간은 구현 단계에서 확인한다. [시스템 사양 §10](../../../specifications/DT_Demo_System_Specification.md#10-motion-server-인터페이스-및-시간-관리)
