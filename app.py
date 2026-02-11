import streamlit as st
import pandas as pd
import os
from lotto_logic import LottoEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

def load_raw_data():
    """헤더 없는 CSV 로드"""
    if os.path.exists(CSV_PATH):
        # [수정] 헤더가 없음을 명시하고 이름 부여
        df = pd.read_csv(CSV_PATH, header=None, names=['회차', '1', '2', '3', '4', '5', '6', '보너스'])
        return df
    return pd.DataFrame(columns=['회차', '1', '2', '3', '4', '5', '6', '보너스'])

def save_data(df):
    """헤더 없이 데이터만 저장"""
    # [수정] 제목줄 없이(header=False) 데이터만 저장합니다.
    df.to_csv(CSV_PATH, index=False, header=False)

st.set_page_config(page_title="Lotto AI 유연한 엔진", layout="wide")
st.title("🎰 로또 당첨 번호 관리 및 AI 생성기")

menu = st.sidebar.selectbox("메뉴 선택", ["번호 생성하기", "당첨 번호 입력/업데이트", "전체 당첨 내역 확인"])

# 엔진 로드
try:
    engine = LottoEngine()
except Exception as e:
    st.error(f"엔진 로드 중 오류 발생: {e}")
    st.stop()

if menu == "번호 생성하기":
    st.header("🤖 AI 번호 생성")
    count = st.number_input("생성할 게임 수", min_value=1, max_value=10, value=5)
    if st.button("번호 생성! ✨"):
        result = engine.generate_numbers(count=count)
        for game in result['games']:
            st.subheader(f"Game {game['game_seq']}")
            cols = st.columns(6)
            for idx, num in enumerate(game['numbers']):
                cols[idx].button(str(num), key=f"btn_{game['game_seq']}_{num}")
            st.write(f"📊 합계: {game['sum']} | 홀짝: {game['odd_even']}")
            st.divider()

elif menu == "당첨 번호 입력/업데이트":
    st.header("📝 매주 당첨 번호 추가")
    with st.form("input_form"):
        col_r, col1, col2, col3, col4, col5, col6, col_b = st.columns(8)
        new_round = col_r.text_input("회차 (예: 1,210)")
        n1 = col1.number_input("1번", 1, 45)
        n2 = col2.number_input("2번", 1, 45)
        n3 = col3.number_input("3번", 1, 45)
        n4 = col4.number_input("4번", 1, 45)
        n5 = col5.number_input("5번", 1, 45)
        n6 = col6.number_input("6번", 1, 45)
        bn = col_b.number_input("보너스", 1, 45)
        submit = st.form_submit_button("번호 추가하기")
        if submit:
            df = load_raw_data()
            if new_round in df['회차'].values:
                st.error("이미 존재하는 회차입니다.")
            else:
                new_data = {'회차': new_round, '1': n1, '2': n2, '3': n3, '4': n4, '5': n5, '6': n6, '보너스': bn}
                # 새 데이터를 맨 위에 추가
                df = pd.concat([pd.DataFrame([new_data]), df], ignore_index=True)
                save_data(df)
                st.success(f"{new_round}회 당첨 번호가 저장되었습니다!")
                engine.refresh_data()

elif menu == "전체 당첨 내역 확인":
    st.header("📜 전체 당첨 번호 목록")
    df = load_raw_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("데이터가 없습니다.")