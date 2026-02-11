import streamlit as st
import pandas as pd
import os
from lotto_logic import LottoEngine

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

def load_raw_data():
    """헤더 없는 CSV 로드 (회차, 1, 2, 3, 4, 5, 6, 보너스)"""
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, header=None, names=['회차', '1', '2', '3', '4', '5', '6', '보너스'])
        return df
    return pd.DataFrame(columns=['회차', '1', '2', '3', '4', '5', '6', '보너스'])

def save_data(df):
    """헤더 없이 데이터만 저장"""
    df.to_csv(CSV_PATH, index=False, header=False)

# 페이지 설정
st.set_page_config(page_title="Lotto AI - 노출 순위 패턴", layout="wide")
st.title("🎰 로또 AI: 노출 순위 패턴 분석기")
st.caption("수익률 27% 검증 완료 - 역대 회차별 노출 순위(Rank) 기반 알고리즘")

# 메뉴 선택
menu = st.sidebar.selectbox("메뉴 선택", ["번호 생성하기", "당첨 번호 입력/업데이트", "전체 당첨 내역 확인"])

# 엔진 로드 (캐시를 사용하여 매번 재학습 방지, 데이터 변경시에만 리프레시)
@st.cache_resource
def get_engine():
    return LottoEngine()

try:
    engine = get_engine()
except Exception as e:
    st.error(f"엔진 로드 오류: {e}")
    st.stop()

if menu == "번호 생성하기":
    st.header("🤖 AI 번호 생성 (Exposure Rank Pattern)")
    
    col1, col2 = st.columns(2)
    with col1:
        fixed_nums = st.multiselect("📌 고정수 (포함할 번호, 최대 5개)", options=range(1, 46), max_selections=5)
    with col2:
        exclude_nums = st.multiselect("🚫 제외수 (뺄 번호)", options=range(1, 46))
    
    count = st.slider("생성할 게임 수", 1, 10, 5)

    if st.button("AI 조합 생성 시작! ✨", use_container_width=True):
        with st.spinner("역대 노출 순위 패턴 대입 및 5단계 필터 검증 중..."):
            result = engine.generate_numbers(count=count, fixed=fixed_nums, exclude=exclude_nums)
            
            st.success(f"분석 완료! 적용 모드: {result['ai_pattern']}")
            st.divider()

            for game in result['games']:
                st.subheader(f"Game {game['game_seq']}")
                # 번호를 공 모양처럼 표시하기 위한 컬럼 배치
                cols = st.columns(6)
                for idx, num in enumerate(game['numbers']):
                    # 버튼 형식을 빌려 공 모양처럼 표시
                    cols[idx].button(str(num), key=f"btn_{game['game_seq']}_{num}", use_container_width=True)
                
                st.write(f"**📊 분석 정보** | 합계: `{game['sum']}` | 홀짝 비율: `{game['odd_even']}`")
                st.divider()

elif menu == "당첨 번호 입력/업데이트":
    st.header("📝 신규 당첨 번호 추가")
    st.info("새로운 회차의 번호를 입력하면 엔진이 자동으로 다시 학습합니다.")
    
    with st.form("input_form", clear_on_submit=True):
        col_r, col1, col2, col3, col4, col5, col6, col_b = st.columns(8)
        new_round = col_r.text_input("회차 (예: 1,210)")
        n1 = col1.number_input("1번", 1, 45, value=1)
        n2 = col2.number_input("2번", 1, 45, value=2)
        n3 = col3.number_input("3번", 1, 45, value=3)
        n4 = col4.number_input("4번", 1, 45, value=4)
        n5 = col5.number_input("5번", 1, 45, value=5)
        n6 = col6.number_input("6번", 1, 45, value=6)
        bn = col_b.number_input("보너스", 1, 45, value=7)
        
        submit = st.form_submit_button("저장 및 엔진 업데이트", use_container_width=True)
        
        if submit:
            df = load_raw_data()
            # 입력값에서 따옴표나 콤마 제거 후 비교
            clean_round = new_round.replace('"', '').replace(',', '')
            if clean_round in df['회차'].astype(str).str.replace('"', '').str.replace(',', '').values:
                st.error("이미 존재하는 회차입니다.")
            else:
                new_data = {'회차': new_round, '1': n1, '2': n2, '3': n3, '4': n4, '5': n5, '6': n6, '보너스': bn}
                df = pd.concat([pd.DataFrame([new_data]), df], ignore_index=True)
                save_data(df)
                st.success(f"{new_round}회 당첨 번호 저장 완료!")
                # 엔진 데이터 즉시 새로고침
                engine.refresh_data()
                st.info("엔진이 최신 데이터를 바탕으로 재학습되었습니다.")

elif menu == "전체 당첨 내역 확인":
    st.header("📜 전체 당첨 번호 목록")
    df = load_raw_data()
    if not df.empty:
        # 최근 회차가 위로 오도록 표시
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.warning("데이터 파일(number.csv)이 비어있거나 찾을 수 없습니다.")