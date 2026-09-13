import pandas as pd
import os
import shutil
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# 1. 파일 경로 및 실행 범위 설정
# ==========================================
excel_path = 'Sobol_Operational_Cases_constantInfiltration.xlsx'
base_cas = 'Furnace_Applied.cas.h5'
base_dat = 'Furnace_Applied.dat.h5'
pdf_file = 'PDF_slabHexa.pdf'
fla_file = 'Flamelet_slabHexa.fla'

# 실행 범위 설정 (예: 23번부터 80번까지)
START_CASE_NUM = 24
END_CASE_NUM = 128

# 리눅스 서버 내 Fluent 실행 경로
fluent_bin = '/usr/local/ansys_inc/v251/fluent/bin/fluent'

# 경계조건 Named Selection
fuel_inlets = [
    "burner_front_massflow_inlet1_fuel_x", "burner_front_massflow_inlet2_fuel_x",
    "burner_rear_massflow_inlet1_fuel_-x", "burner_rear_massflow_inlet2_fuel_-x"
]
air_inlets = ["burner_front_massflow_inlet_air_x", "burner_rear_massflow_inlet_air_-x"]
outlets = ["burner_front_massflow_outlet", "burner_rear_massflow_outlet_-x"]

# ==========================================
# 2. 데이터 로드 및 범위 필터링
# ==========================================
df_all = pd.read_excel(excel_path)

def extract_number(case_str):
    """'Sobol_23' 형태의 문자열에서 숫자 23만 추출하는 함수"""
    match = re.search(r'\d+', str(case_str))
    return int(match.group()) if match else -1

# 숫자만 추출하여 새로운 열 생성 후 필터링
df_all['num_only'] = df_all['case_no'].apply(extract_number)
df_target = df_all[(df_all['num_only'] >= START_CASE_NUM) & (df_all['num_only'] <= END_CASE_NUM)].copy()

def to_fluent_val(val):
    return f"{val:.3g}"

# ==========================================
# 3. 개별 케이스 작업 함수
# ==========================================
def run_fluent_case(case_data):
    case_id = str(case_data['case_no'])
    case_dir = f"Case_{case_id}"

    if not os.path.exists(case_dir):
        os.makedirs(case_dir)

    # 파일 복사
    for f in [base_cas, base_dat, pdf_file, fla_file]:
        if os.path.exists(f):
            shutil.copy(f, os.path.join(case_dir, f))

    # 조건값 계산
    f_val = to_fluent_val(case_data['bc_fuel_inlet'])
    a_val = to_fluent_val(case_data['bc_air_inlet'])
    a_temp_raw = case_data['air_temp']
    a_temp = to_fluent_val(a_temp_raw)
    init_temp = to_fluent_val(a_temp_raw + 200) # 공기온도 + 200K
    o_val = to_fluent_val(case_data['bc_burner_outlet'])

    # 저널 파일(bk.jou) 생성
    jou_path = os.path.join(case_dir, 'bk.jou')
    with open(jou_path, 'w') as f:
        f.write('/file/confirm-overwrite? no\n')
        f.write(f'/file/read-case-data "{base_cas}"\n\n')

        f.write('; --- BC Updates ---\n')
        for inlet in fuel_inlets:
            f.write(f'/define/boundary-conditions/set/mass-flow-inlet {inlet} () mass-flow-rate n {f_val} q\n')
        for inlet in air_inlets:
            f.write(f'/define/boundary-conditions/set/mass-flow-inlet {inlet} () mass-flow-rate n {a_val} temperature n {a_temp} q\n')
        for outlet in outlets:
            f.write(f'/define/boundary-conditions/set/mass-flow-outlet {outlet} () mass-flow-rate n {o_val} q\n')

        f.write('\n; --- Initialization ---\n')
        f.write('/solve/initialize/hyb-initialization\n')
        f.write(f'/solve/initialize/set-defaults/temperature {init_temp}\n')
        f.write('/solve/initialize/initialize-flow\n')

        f.write('\n; --- Solve & Export ---\n')
        f.write('/solve/iterate 10\n')
        f.write('q\nq\n')
        f.write('/file/export/ascii "case_cell_10_Temp.csv" () yes temperature dt-dx dt-dy dt-dz q no\n')

        f.write('/solve/iterate 9990\n')
        f.write('q\nq\n')
        f.write('/file/export/ascii "case_cell_Temp.csv" () yes temperature dt-dx dt-dy dt-dz q no\n')

        f.write(f'/file/write-case-data "{base_cas}"\n')
        f.write('/exit\nquit\nexit\n')

    print(f"▶ [시작] {case_dir} (16코어 할당)")
    cmd = f"{fluent_bin} 3ddp -alnamd64 -t16 -pib -g -i bk.jou -pic shmem"

    log_path = os.path.join(case_dir, 'mon.log')
    with open(log_path, 'w') as log_file:
        subprocess.run(cmd, shell=True, cwd=case_dir, stdout=log_file, stderr=subprocess.STDOUT)

    print(f"■ [종료] {case_dir} 완료")
    return case_dir

# ==========================================
# 4. 병렬 실행 제어
# ==========================================
case_list = df_target.to_dict('records')

print(f"총 {len(df_all)}개 중 {len(case_list)}개 케이스({START_CASE_NUM}~{END_CASE_NUM}) 연산을 시작합니다.")
print(f"동시 실행 제한: 3개 (총 사용 코어: 48코어)")

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(run_fluent_case, case_list))

print(f"\n🎉 {START_CASE_NUM}번부터 {END_CASE_NUM}번까지의 모든 계산이 완료되었습니다!")
