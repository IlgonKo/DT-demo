# Recipe Manager 사양

[Overall 사양](../architecture.md) · 기준일 2026-11-27

## 저장 구조와 편집 정책

| 데이터 | 형식·의미 |
|---|---|
| Recipe 이름 | 저장·선택에 사용하는 이름 |
| 장치 참조 | X1·Y·Z 등 논리 장치 이름 |
| 경유점 | P1~P10에 최대 10개 저장 |
| 사용 포인트 수 N | 사용자가 Recipe별로 1~10 지정. Auto는 P1부터 PN까지 실행 |
| 좌표 | 각 점의 X1·Y·Z 목표 위치 |
| PP 속도 | 축별 기본값 및 경유점별 변경값 |
| PP 가속도·감속도 | 축별 기본값 및 경유점별 변경값 |
| Dwell | 해당 점의 모든 대상 축 도달·정지 후 대기 시간 |

Recipe의 신규 생성, 편집·조회·검증, 저장 및 다른 이름으로 저장을 지원하고 마지막 저장본의 읽기 전용 Snapshot을 Auto Controller에 제공한다. 편집·불러오기·저장은 Ready에서 허용한다. 직접 좌표 입력 오류와 S/W Limit 초과를 표시한다. 미저장 변경은 별도로 표시하고 Auto 실행에는 저장본을 사용한다.

Recipe별로 최대 10개 포인트를 저장한다. 사용자가 HMI에서 설정한 개수 N을 함께 저장한다. Auto Start 전에 P1~PN이 등록되어 있고 유효한지 확인한다. 사용 개수를 줄인 뒤에도 뒤쪽에 저장된 포인트를 보존한다. 포인트 역할과 좌표는 사용자가 정의한다.

## 티칭

1. HMI 또는 Pendant가 P1~P10 중 한 점의 현재 위치 등록을 요청한다.
2. System Controller가 Manual·Ready와 대상 축의 정지를 확인한다.
3. Recipe Manager가 Device Manager의 Snapshot에서 X1·Y·Z 현재 좌표를 한 점에 함께 등록한다. DT는 가상축, Sync는 실제축 좌표를 사용한다.
4. 등록값은 편집 중인 Recipe에 반영하며, 저장하면 다음 Auto 실행에 사용할 수 있다.

티칭 위치까지의 이동은 [Manual Controller](manual-controller.md)가 수행한다. 경유점 이동과 Dwell은 [Auto Controller](auto-controller.md)가 실행한다. 저장 형식과 데이터 구조는 구현 단계에서 정한다. [시스템 사양 §7](../../../specifications/DT_Demo_System_Specification.md#7-teaching-및-recipe)
