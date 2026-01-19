import streamlit as st

import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (가장 먼저 와야 함)
st.set_page_config(
    page_title="나의 스트림릿 앱",
    page_icon="📊",
    layout="wide"  # 'centered' 또는 'wide'
)

# 2. 사이드바 (옵션 및 설정)
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    st.write("원하는 옵션을 선택하세요.")
    
    # 셀렉트박스
    category = st.selectbox(
        "카테고리 선택",
        ["개요", "상세 분석", "설정"]
    )
    
    # 슬라이더
    range_val = st.slider("범위 설정", 0, 100, 50)
    
    st.markdown("---")
    st.info(f"현재 선택: **{category}**")

# 3. 메인 본문 영역
st.title("📊 기본 대시보드 예제")
st.markdown("스트림릿으로 만든 **기본 레이아웃**입니다. 데이터를 시각화하고 상호작용할 수 있습니다.")

# 구분선
st.divider() 

# 4. 레이아웃 나누기 (2단 구성)
col1, col2 = st.columns([1, 1])  # 1:1 비율로 나누기

with col1:
    st.subheader("📋 데이터 미리보기")
    # 예시 데이터 생성
    data = pd.DataFrame(
        np.random.randn(10, 3),
        columns=['A', 'B', 'C']
    )
    # 데이터프레임 출력
    st.dataframe(data, use_container_width=True)

with col2:
    st.subheader("📈 차트 시각화")
    # 라인 차트 그리기
    st.line_chart(data)

# 5. 사용자 입력 및 버튼 인터랙션
st.subheader("💬 사용자 입력")
user_input = st.text_input("의견을 남겨주세요:")

if st.button("전송하기"):
    if user_input:
        st.success(f"입력하신 내용이 저장되었습니다: {user_input}")
    else:
        st.warning("내용을 입력해주세요!")