# Auto Controller 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 시작과 준비

HMI 또는 Pendant에서 접수된 Auto Start 한 건을 전체 자동 운전 한 건으로 관리한다. 시작 조건은 Auto·Ready, 유효한 저장 Recipe, 제어권·통신·장치 준비와 필요한 Servo·Homing이다. 실행 중 추가 Start는 거절한다. Recipe Manager가 제공한 저장 Snapshot을 사용한다.

Cycle Preparation 단계에서 초기 위치를 확인하고, 필요하면 갠트리·Loader를 복귀시킨다. 초기 위치 불일치는 준비 이동으로 처리한다. 준비 중 Running을 유지한다. 준비 실패·타임아웃은 System Controller에 보고하고 실행을 중단한다. 초기 위치, 복귀 순서, 비간섭 조건은 실제 기구 구성에 맞춰 확정한다.

## 한 사이클 실행

Sequencer는 Auto Controller의 하위 모듈로 한 사이클을 실행한다.

| 단계 | 실행 | 다음 단계 조건 |
|---|---|---|
| Start Check | Cycle Preparation 완료, 장치 준비·Loader 간섭 조건 확인 | 시작 조건 충족 |
| PCB Loading | Loader 로딩 지령 | 로딩 완료 끝단 센서 확인 |
| Gantry Path Execution | P1~PN 순차 PP 및 Dwell | 각 구간의 모든 대상 완료 |
| PCB Unloading | 갠트리 비간섭 위치 확인 후 Loader 언로딩 | 언로딩 완료 끝단 센서 확인 |
| Cycle Complete | Done 결과 반환 | 상위 Auto Control로 반환 |

각 경유점은 X1·Y·Z 독립 PP로 실행한다. DT는 가상축 전체, Sync는 실제·가상축 전체의 도달·정지를 확인한 후 Dwell을 시작한다. Loader 완료도 DT는 가상 센서, Sync는 실제·가상 센서 모두를 확인한다. 마지막 사용 점의 이동과 Dwell이 끝나면 PCB Unloading을 이어간다.

## 반복과 최종 보고

- Repeat는 HMI에서 Ready일 때 설정한다. 새 Start에서 완료 횟수를 0으로 초기화하고 정상 완료한 사이클만 집계한다.
- 현재 실행의 사이클 결과가 Done이고 Repeat가 켜져 있으면 Running을 유지하며 다음 Cycle Preparation을 시작한다. Repeat가 꺼져 있으면 전체 운전을 완료한다.
- Stop 또는 Fault에서 후속 지령과 반복 예약을 취소한다. Stop 접수 후 늦게 도착한 사이클 완료를 집계하거나 다음 사이클을 시작하는 데 사용하지 않는다. 복구 후 새 Start는 실행 조건 확인과 Cycle Preparation부터 시작한다.
- 전체 Auto Start 한 건에 대해 대상 실행, 완료·실패·취소 여부와 실패·취소 사유를 System Controller에 한 번 보고한다. 개별 사이클 결과와 완료 횟수는 Auto Controller가 관리한다.

[Auto 및 공정 Sequence 사양](../../../specifications/DT_Demo_System_Specification.md#8-auto-control-및-공정-sequence) · [Recipe Manager](recipe-manager.md)
