import streamlit as st
import pandas as pd
import os
from lotto_logic import LottoEngine

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

def load_raw_data():
    """CSV 파일 로드 (제목 줄 제외 로직 포함)"""
    if os.path.exists(CSV_PATH):
        # 첫 번째 줄(제목)을 건너뛰고 로드
        df = pd.read_csv(CSV_PATH, skiprows=0)
        # 만약 첫 줄이 한글 제목 등이면 아래처럼 필터링
        df = df[df['회차'].get(0) != '회차'] 
        return df
    return pd.DataFrame(columns=['회차', '1', '2', '3', '4', '5', '6', '보너스'])

def save_data(df):
    """CSV 파일 저장 (인덱스 없이 저장)"""
    df.to_csv(CSV_PATH, index=False)

# 페이지 설정
st.set_page_config(page_title="Lotto AI 유연한 엔진", layout="wide")

st.title("🎰 로또 당첨 번호 관리 및 AI 생성기")

# 사이드바 메뉴
menu = st.sidebar.selectbox("메뉴 선택", ["번호 생성하기", "당첨 번호 입력/업데이트", "전체 당첨 내역 확인"])

engine = LottoEngine()

if menu == "번호 생성하기":
    st.header("🤖 AI 번호 생성 (유연한 7분할 엔진)")
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
            # 중복 회차 확인
            if new_round in df['회차'].values:
                st.error("이미 존재하는 회차입니다.")
            else:
                new_data = {
                    '회차': new_round, '1': n1, '2': n2, '3': n3, '4': n4, '5': n5, '6': n6, '보너스': bn
                }
                df = pd.concat([pd.DataFrame([new_data]), df], ignore_index=True)
                save_data(df)
                st.success(f"{new_round}회 당첨 번호가 저장되었습니다!")
                # 엔진 데이터 새로고침
                engine.refresh_data()

elif menu == "전체 당첨 내역 확인":
    st.header("📜 전체 당첨 번호 목록")
    df = load_raw_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("데이터가 없습니다.")