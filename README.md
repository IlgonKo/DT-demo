# DT-demo

Fieldbus 기반 Digital Twin 데모의 합의 내용, 시스템 사양 및 발표 자료를 관리한다.

## 문서

| 문서 | 용도 |
|---|---|
| [시스템 사양서 — Markdown](docs/specifications/DT_Demo_System_Specification.md) | 기능 요구사항, 실행 조건, 절차, 완료·실패 판정 및 인터페이스 |
| [시스템 사양서 — Word](docs/specifications/Festo_DT_Demo_System_Specification_v2.docx) | 편집 가능한 사양서 |
| [시스템 사양서 — PDF](docs/specifications/Festo_DT_Demo_System_Specification_v2.pdf) | 공유·열람용 사양서, 24페이지 |
| [합의 작업 문서](docs/agreements/DT_Demo_Working_Agreements.md) | 상세 합의·결정 기록 및 구현 시 확정 항목. 기준 Version 62 |
| [Overview & Architecture — PowerPoint](presentations/Festo_DT_Demo_Overview_Architecture_v5.pptx) | 10장. Detail Specification 제외 |
| [관계도](docs/diagrams) | 시스템·네트워크·상태 관계도의 Mermaid 원본과 PNG |

## 데모 범위

- 공정: PCB Loading → Gantry Path Execution → PCB Unloading. 실제 재료 토출은 제외한다.
- Demo Control System: Orchestrator + 기존 Motion Server.
- Soft ESC가 가상 장치 동작 모델과 I/O 응답을 계산한다.
- DT는 가상 장치, Sync는 실제·가상 장치에 같은 논리 지령을 전달한다.
- Omniverse는 모든 모드에서 가상 장치 상태를 추종한다. Digital Twin 연결에는 ROS 2를 사용한다.
- Festo AX, Omniverse 내 장치 모델 통합, CSP·축간 보간·블렌딩은 1차 범위에서 제외한다.

## 기준 및 문서 관리

현재 기준일은 2026-11-23이다. 시스템 사양서는 합의 내용을 구현 요구사항으로 재구성한 문서이며, 합의 작업 문서의 단순 변환본과 구분한다.

기능 변경 시 합의 기록과 시스템 사양서를 함께 갱신하고 Word·PDF를 같은 내용으로 유지한다. 구현 시 확정할 형번·수치·기구 조건은 사양서 15장의 TBD로 관리한다. PPT에는 Overview와 Architecture만 반영한다.

이 저장소의 최초 커밋에는 문서와 관계도만 포함한다. Motion Server 및 Soft ESC 구현 코드는 포함하지 않는다.
