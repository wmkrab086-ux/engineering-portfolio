# Fluent batch runner · 연구 당시 코드

[프로젝트 설명](../../projects/fluent-automation/README.md) · [코드 보기](run_fluent_batch.py)

연구자가 제공한 실행 코드를 동작 변경 없이 정리한 버전입니다. 코드 작성에는 생성형 AI를 활용했습니다. 이 저장소를 만들면서 Fluent를 실행하거나 수치해석 결과를 새로 생성하지는 않았습니다.

## 필요한 환경과 파일

- Linux 및 Ansys Fluent 실행 환경·라이선스
- Python, Pandas, Excel 읽기를 위한 OpenPyXL
- 코드의 `fluent_bin` 경로와 Named Selection에 맞는 해석 모델
- 작업 디렉터리의 다음 파일

| 파일 | 역할 |
|---|---|
| `Sobol_Operational_Cases_constantInfiltration.xlsx` | 작동조건표 |
| `Furnace_Applied.cas.h5` | 기준 case |
| `Furnace_Applied.dat.h5` | 기준 data |
| `PDF_slabHexa.pdf` | Fluent 연소 PDF 테이블. 문서 형식 PDF와 구분 |
| `Flamelet_slabHexa.fla` | Flamelet 관련 파일 |

해석 입력 파일과 실제 작동조건표는 저장소에 포함하지 않았습니다.

## 조건표 열

| 열 이름 | 코드의 사용 방식 |
|---|---|
| `case_no` | `Sobol_24` 등 번호를 포함하는 식별자 |
| `bc_fuel_inlet` | 각 지정 연료 inlet에 입력하는 질량유량 |
| `bc_air_inlet` | 각 지정 air inlet에 입력하는 질량유량 |
| `air_temp` | 공기 온도 [K], 초기 온도 기본값은 여기에 200 K를 더해 설정 |
| `bc_burner_outlet` | 각 지정 burner outlet에 입력하는 질량유량 |

유량은 각 지정 경계에 같은 값을 넣습니다. 전체 유량을 자동으로 경계 개수로 나누는 기능은 없으므로, 조건표는 원래 연구의 경계별 정의에 맞아야 합니다. 단위와 Fluent 저널 명령은 실제 case 및 Fluent 버전에서 확인해야 합니다.

## 실행

필요한 입력 파일과 해석 환경을 준비한 별도 작업 디렉터리에 코드를 두고, 경로·범위·동시 실행 수·코어 수를 확인한 뒤 실행합니다.

```bash
python -m pip install -r requirements.txt
python run_fluent_batch.py
```

이 코드는 실행 즉시 조건표를 읽고 실제 계산을 시작합니다. 샘플 실행이나 dry-run 옵션은 없습니다. `requirements.txt`는 필요한 패키지 목록이며, 원 연구 환경의 버전을 고정한 재현 환경 파일은 아닙니다.

## 케이스별 생성 파일

| 파일 | 내용 |
|---|---|
| `bk.jou` | 경계조건 변경·초기화·계산·추출 저널 |
| `mon.log` | Fluent 실행의 표준 출력 및 오류 출력 |
| `case_cell_10_Temp.csv` | 첫 10회 반복 후 추출하도록 설정한 결과 |
| `case_cell_Temp.csv` | 추가 9,990회 반복 후 추출하도록 설정한 결과 |
| `Furnace_Applied.cas.h5`, `Furnace_Applied.dat.h5` | 계산 후 저장하도록 설정한 해석 파일 |

코드상의 추출 명령에는 `temperature`, `dt-dx`, `dt-dy`, `dt-dz`가 포함됩니다. CSV의 실제 좌표·헤더와 대상 영역은 Fluent 및 원본 case 설정에 따라 확인해야 합니다.

## 현재 버전의 한계

- 총 10,000회 반복을 요청하며 수렴을 판정하지 않습니다.
- `subprocess.run` 반환코드를 확인하지 않아 실행 실패 후에도 완료 메시지가 표시될 수 있습니다.
- 누락된 기준 파일을 사전에 오류 처리하지 않고, 존재하는 파일만 복사합니다.
- 재시도·중단 후 재개·기존 결과 보호 기능을 별도로 구현하지 않았습니다. 기존 작업 디렉터리에서 다시 실행하면 저널·로그·결과를 덮어쓸 수 있습니다.

이 한계들은 원본 코드의 범위를 설명한 것입니다. 실제 연구 성과로 구현하지 않은 오류 복구나 수렴 자동 판정을 추가로 주장하지 않습니다.
