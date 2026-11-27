# DT Demo — Repository 구성

**2026-11-27 | v0.2 | 저장소 경계 확정**

관련 문서: [Software Architecture](architecture.md), [Implementation Plan](../../planning/orchestrator-implementation-plan.md).

## 1. 합의된 저장소 경계

DT-demo에 Orchestrator와 HMI를 함께 두고, Motion Server와 Soft ESC는 각각 기존 독립 Repository를 유지한다. 전체 Repository는 세 개다.

| Repository | 역할 | 관리 범위 |
|---|---|---|
| DT-demo | Application Layer | Orchestrator, HMI, Configuration, Recipe, 시스템 사양, 통합 테스트 |
| motion-server | Motion Control Platform | 여러 Application에서 사용하는 모션 제어 기능 |
| ethercat-device-simulator | Virtual Device Platform | Soft ESC 및 가상 장치 동작 모델 |

Orchestrator는 현재 DT Demo의 운전 정책과 공정 Sequence를 구현하는 Application Software다. Motion Server와 Soft ESC는 여러 Application에서 독립적으로 사용할 수 있는 범용 플랫폼에 가깝다. 따라서 현재의 책임 경계를 Repository 경계로 사용한다.

사용자와 ChatGPT/Codex가 공동 개발하는 규모에서는 사양서, 구현, 테스트의 변경을 하나의 Commit으로 관리하는 것이 유리하다. Omniverse 연동 담당자와의 인터페이스는 별도 계약으로 관리한다.

## 2. 동일 Repository와 별도 Repository 비교

| 비교 항목 | 동일 Repository | 별도 Repository |
|---|---|---|
| 사양서와 구현 일관성 | 같은 Commit으로 관리하기 유리 | Repository 간 변경 추적 필요 |
| HMI와 Orchestrator 연계 | 연계 변경이 간단 | 호환 버전 관리 필요 |
| 통합 테스트 | 같은 변경에 포함하기 간단 | 의존성 및 조합 관리 필요 |
| 독립 배포 및 릴리스 | 디렉터리별 빌드·태그 정책으로 가능 | 독립 수명주기 관리에 유리 |
| 범용 제품화 | 필요 시 공통 Core 분리 가능 | 초기부터 독립 관리하기 유리 |
| 현재 개발 규모 | 적합 | 관리 항목 증가 |
| 12월 Milestone 대응 | 통합 변경 및 검증에 유리 | 버전 조율 부담 증가 |

## 3. 권장 구조와 책임

기존 문서 구조는 유지하고, 구현 영역은 개발에 맞춰 추가한다. 아래 경로는 목표 구조이며 모든 디렉터리나 실행 파일이 이미 존재한다는 의미는 아니다.

| 경로 | 책임 |
|---|---|
| README.md | 프로젝트 개요, 문서·실행 진입점 |
| docs/agreements/ | 합의 및 결정 기록 |
| docs/specifications/ | 시스템 요구사항 |
| docs/design/orchestrator/ | Orchestrator 설계 및 Repository 구성 |
| docs/planning/ | 개발 일정 및 Milestone |
| docs/validation/ | 검증 절차, 실행 결과 및 검증된 외부 버전 기록 |
| presentations/ | 발표 자료 |
| orchestrator/app.py | 모듈 생성·연결 및 실행 진입점 |
| orchestrator/core/system_controller.py | System Controller의 명령 접수, 상태와 운전 정책 |
| orchestrator/interfaces/motion_server/ | Motion Server TCP 연결 및 프로토콜 Adapter |
| orchestrator/interfaces/pendant/ | Pendant 입력 및 피드백 Adapter |
| orchestrator/interfaces/hmi/ | HMI API 및 상태 전달 |
| orchestrator/interfaces/omniverse/ | Omniverse 상태 발행 및 충돌 수신. ROS 2 사용 |
| orchestrator/devices/ | Device Manager의 장치 Registry·라우팅·상태 관리, Parameter/PDO Pairing 및 State Alignment |
| orchestrator/operations/manual_controller.py | Manual Controller의 수동 운전 |
| orchestrator/operations/auto/ | Auto Controller의 자동 운전과 하위 Sequencer |
| orchestrator/recipes/ | Recipe 로딩·검증·Snapshot을 처리하는 코드 |
| hmi/ | 화면 구현 |
| config/ | 장치 구성, 연결 정보, 운전 설정 |
| recipes/ | 실행에 사용하는 Recipe 데이터 및 예제 |
| tests/unit/ | Mock Interface 기반 모듈 검증 |
| tests/integration/ | 모듈 및 TCP/API 연동 검증 |
| tests/system/ | 전체 시스템 검증 시나리오 |
| Dockerfile | Orchestrator Container 빌드 정의 |
| compose.yaml | 시스템 실행 구성 |

`orchestrator/recipes/`는 처리 코드, 최상위 `recipes/`는 데이터로 구분한다. 비밀번호나 인증정보는 버전 관리 대상에 포함하지 않는다.

## 4. 외부 의존성과 배포 재현성

Motion Server와 Soft ESC 소스는 DT-demo로 복제하지 않는다. 통합 검증 시 다음 정보를 `docs/validation/`에 함께 기록하는 방식을 제안한다.

| 기록 항목 | 내용 |
|---|---|
| Application 버전 | 검증한 DT-demo Commit ID |
| Motion Server 버전 | Repository URL, Release Tag가 있으면 해당 Tag, 전체 Commit ID |
| Soft ESC 버전 | Repository URL, Release Tag가 있으면 해당 Tag, 전체 Commit ID |
| 실행 환경 | 장치 구성, 설정 및 Recipe 식별 정보 |
| 배포 이미지 | Container를 사용하는 경우 Image Tag와 불변 Digest |
| 검증 결과 | 일자, DT/Sync 모드, 시험 환경 유형(단위·Motion Server+Soft ESC·실장치 포함), 결과 및 미완료 항목 |

브랜치명이나 `latest`만으로 검증 조합을 식별하지 않는다. HMI와 Orchestrator는 같은 Repository에서도 독립 빌드·배포할 수 있으며, 구체적인 빌드 정책은 구현 단계에서 확정한다.

## 5. Milestone 및 향후 분리 기준

2026-12-11 Manual Control + Omniverse 통합 테스트, 2026-12-25경 Auto Control + Parameter Pairing + State Alignment 테스트를 목표로 한다. 상세 일정과 Acceptance Criteria는 Implementation Plan을 따른다. 이 문서는 향후 DT Demo 계획에 반영할 제안이며 기존 시스템 사양의 확정 변경을 의미하지 않는다.

Orchestrator가 여러 Demo 또는 고객 Application에서 공통으로 사용되고, 독립 릴리스·호환성 관리가 필요해지면 범용 Core를 별도 Repository로 분리하는 방안을 재검토한다. 현재는 Application 정책과 공통 기능의 모듈 경계를 유지하며 개발한다.
