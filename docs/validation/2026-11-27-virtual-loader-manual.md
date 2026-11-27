# 가상 Loader 수동 운전 검증

2026-11-27 · L2 · DT Manual · Motion Server + Soft ESC

## 시험 구성

- Motion Server `192.168.0.128:15000`, Soft ESC Edge #2 `192.168.0.12`. 가상 X1·Y·Z와 CPX-AP-I-EC `io0`를 사용했다.
- Soft ESC 배포 설정에 `cylinder_100mm` 프리셋으로 FMI 3.0 실린더 모델을 연결했다. 기존 배포 파일의 사본인 `build/compose.dt-loader-test.env`를 적용한 뒤 EtherCAT 연결을 재초기화했다.
- Orchestrator는 `config/virtual-loader-soft-esc.json`을 사용했다. 시험 구성에서는 후진 끝단이 초기, 전진 끝단이 반대 끝단이다.

```dotenv
DEVICE_SIMULATOR_IO_MODELS=loader0:cylinder_100mm
DEVICE_SIMULATOR_IO_io0_BINDINGS=2:DO:0=loader0.extend,2:DO:1=loader0.retract,1:DI:0=loader0.retracted,1:DI:1=loader0.extended
```

## 결과

| 시험 | 관찰 결과 |
|---|---|
| 실린더 모델 끝단 유지 | 양방향에서 기존 끝단을 떠나 양단 센서가 OFF인 동안 출력을 해제했다. 실린더가 기존 방향의 끝단까지 이동했고, 양쪽 출력 OFF와 해당 끝단 센서 하나만 ON인 상태를 각 방향에서 0.5초 동안 관찰했다. |
| Chrome HMI 양방향 | 반대 끝단과 초기 끝단 버튼에서 각각 HTTP 접수를 받았다. Motion Server 피드백에서 한 방향 밸브 출력 ON, 양단 센서 OFF, 목표 센서만 ON, 두 출력 OFF를 관찰했다. HMI의 센서·출력 표시도 일치했다. |
| HMI 공통 Stop | 반대 끝단 이동 중 양단 센서 OFF 및 전진 출력 ON을 관찰한 시점에 Chrome의 공통 Stop을 눌렀다. 시험 표본에서 약 60 ms 후 양쪽 출력 OFF, 반대 끝단 센서만 ON, 세 축 B8=0을 관찰했다. HMI의 Loader 정지 확인과 Ready를 확인했다. 끝단에 이미 정지한 상태에서도 공통 Stop을 확인했다. |
| 가상 3축 PP 중 공통 Stop | 시험 환경 재시작 후 각 축을 Homing하고 세 축 PP를 시작했다. 세 축 B8=1을 관찰한 뒤 Chrome에서 공통 Stop을 눌렀다. 세 축 B8=0과 Loader 초기 센서 ON·두 출력 OFF·정지 확인, Ready 복귀를 함께 확인했다. |
| 물리 DualSense | R1에서 반대 끝단, L1에서 초기 끝단에 도달했다. 각 방향의 단독 밸브 출력과 정지 후 양쪽 출력 OFF를 확인했다. ○(Circle)로 공통 Stop을 요청해 Loader 정지가 확인됐다. Pendant가 선택된 동안 HMI의 Loader 이동 요청은 거절됐으며 Motion Server 연결과 제어권은 유지됐다. |
| 단위 테스트 | 11개 통과. Loader 목표 센서·출력 해제, 공통 Stop의 실행 취소, 양단 센서 OFF에서 정지 확인 제한 시간 초과 및 Fault를 포함한다. |

시험 종료 후 HMI 조작 소스, Loader 초기 끝단 및 두 출력 OFF, 세 축 0 mm 및 Servo Off, Motion Server 제어권 반납을 확인했다. 시험용 Soft ESC 구성은 후속 가상 Loader 시험에 사용할 수 있게 적용 상태로 두었다.

가상 5/2 메모리 밸브는 출력 해제 후에도 밸브 방향을 유지한다. 이동 중 Stop이 들어오면 새 방향 지령을 진행하지 않고 출력을 해제하며, 끝단에 도달해 정지하기까지 확인을 계속한다. 양단 센서가 모두 OFF인 상태는 정지 미확인이다. 기본 2초 이내 정지를 확인하지 못하면 System Controller는 Fault로 전환한다.
