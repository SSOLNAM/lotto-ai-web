import streamlit as st
import pandas as pd
from lotto_logic import LottoEngine # 우리가 만든 엔진 가져오기

# 페이지 설정 (제목, 아이콘 등)
st.set_page_config(
    page_title="AI 로또 명당",
    page_icon="🎱",
    layout="centered"
)

# 스타일 꾸미기 (CSS 주입)
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .ball {
        display: inline-block;
        width: 40px; height: 40px;
        line-height: 40px;
        border-radius: 50%;
        text-align: center;
        color: white;
        font-weight: bold;
        margin: 2px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .ball-yellow { background-color: #fbc400; text-shadow: 1px 1px 2px #b08900; }
    .ball-blue { background-color: #69c8f2; text-shadow: 1px 1px 2px #3b8eb5; }
    .ball-red { background-color: #ff7272; text-shadow: 1px 1px 2px #c44545; }
    .ball-grey { background-color: #aaaaaa; text-shadow: 1px 1px 2px #666666; }
    .ball-green { background-color: #b0d840; text-shadow: 1px 1px 2px #7fa120; }
</style>
""", unsafe_allow_html=True)

# 공 색상 결정 함수
def get_ball_html(num):
    color_class = "ball-green"
    if num <= 10: color_class = "ball-yellow"
    elif num <= 20: color_class = "ball-blue"
    elif num <= 30: color_class = "ball-red"
    elif num <= 40: color_class = "ball-grey"
    
    return f'<div class="ball {color_class}">{num}</div>'

# --- 메인 화면 ---
st.title("🎱 AI 통계 기반 로또 생성기")
st.caption("최근 50회차 데이터 분석 & 7분할 구간 패턴 적용 (수익률 12% 엔진)")

# 엔진 로드 (캐싱하여 속도 향상)
@st.cache_resource
def load_engine():
    return LottoEngine()

engine = load_engine()

# 사이드바 (설정)
with st.sidebar:
    st.header("⚙️ 옵션 설정")
    st.info("꿈에서 본 숫자가 있나요?")
    
    fixed_input = st.multiselect(
        "고정수 (무조건 포함)",
        options=range(1, 46),
        max_selections=5
    )
    
    exclude_input = st.multiselect(
        "제외수 (절대 안 나옴)",
        options=range(1, 46)
    )
    
    game_count = st.slider("생성할 게임 수", 1, 10, 5)

# 메인 버튼
if st.button("✨ AI 번호 생성하기", type="primary", use_container_width=True):
    with st.spinner("AI가 최적의 패턴을 분석 중입니다..."):
        # 엔진 실행
        try:
            result = engine.generate_numbers(
                count=game_count,
                fixed=fixed_input,
                exclude=exclude_input
            )
            
            # 분석 결과 표시
            st.success("분석 완료! 행운의 번호가 나왔습니다.")
            
            with st.expander("📊 AI 분석 리포트 보기", expanded=True):
                st.write(f"**적용된 최적 7분할 패턴:** `{result['ai_pattern']}`")
                st.caption("※ 1번대부터 40번대까지 번호가 골고루 분포된 황금 비율입니다.")
            
            st.divider()
            
            # 결과 카드 출력
            for game in result['games']:
                cols = st.columns([1, 4])
                with cols[0]:
                    st.markdown(f"**GAME {game['game_seq']}**")
                    st.caption(f"합계: {game['sum']}")
                with cols[1]:
                    # 공 HTML 생성
                    balls_html = "".join([get_ball_html(n) for n in game['numbers']])
                    st.markdown(balls_html, unsafe_allow_html=True)
                st.divider()
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

else:
    st.info("위 버튼을 눌러 번호를 생성해보세요!")