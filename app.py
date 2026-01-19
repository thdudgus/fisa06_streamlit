import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import datetime
from io import BytesIO
import matplotlib.font_manager as fm
import platform


def init_fonts():
    system_name = platform.system()
    if system_name == 'Windows':
        # 윈도우
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin': 
        # 맥(Mac)
        plt.rc('font', family='AppleGothic')
    else:
        # 리눅스 (구글 코랩, 스트림릿 클라우드 등)
        try:
            import koreanize_matplotlib
        except ImportError:
            pass # 설치가 안되어 있으면 무시 (하지만 깨질 수 있음)

    plt.rc('axes', unicode_minus=False) # 마이너스(-) 기호 깨짐 방지

# 페이지 로드 시 폰트 설정 실행
init_fonts()

# -----------------------------------------------------------------------------
# 1. 함수 정의
# -----------------------------------------------------------------------------
@st.cache_data
def get_krx_company_list() -> pd.DataFrame:
    try:
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        df_listing = pd.read_html(url, header=0, flavor='bs4', encoding='EUC-KR')[0]
        df_listing = df_listing[['회사명', '종목코드']].copy()
        df_listing['종목코드'] = df_listing['종목코드'].apply(lambda x: f'{x:06}')
        return df_listing
    except Exception as e:
        st.error(f"상장사 명단을 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame(columns=['회사명', '종목코드'])

def get_stock_code_by_company(company_name: str) -> str:
    if company_name.isdigit() and len(company_name) == 6:
        return company_name
    
    company_df = get_krx_company_list()
    codes = company_df[company_df['회사명'] == company_name]['종목코드'].values
    if len(codes) > 0:
        return codes[0]
    else:
        raise ValueError(f"'{company_name}'을 찾을 수 없습니다. 종목코드 6자리를 직접 입력해보세요.")

# -----------------------------------------------------------------------------
# 2. 페이지 설정 및 세션 초기화
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="주가 조회",
    page_icon="📈",
    layout="wide"
)

if 'price_df' not in st.session_state:
    st.session_state['price_df'] = None
if 'company_name_saved' not in st.session_state:
    st.session_state['company_name_saved'] = ""
if 'search_triggered' not in st.session_state:
    st.session_state['search_triggered'] = False

# -----------------------------------------------------------------------------
# 3. 사이드바 UI
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📈 주가 데이터 조회")
    st.write("회사명 또는 종목코드:")
    
    company_name = st.text_input("조회할 회사를 입력하세요.")
    confirm_btn = st.button(label="조회하기")
    
    today = datetime.datetime.now()
    jan_1 = datetime.date(today.year, 1, 1)
    dec_31 = datetime.date(today.year, 12, 31)
    
    selected_dates = st.date_input(
        "날짜를 입력하세요",
        (jan_1, datetime.date(today.year, today.month, today.day)),
        jan_1,
        dec_31,
        format="MM.DD.YYYY",
    )

# -----------------------------------------------------------------------------
# 4. 데이터 업데이트 로직
# -----------------------------------------------------------------------------
if confirm_btn:
    if not company_name:
        st.warning("조회할 회사 이름을 입력하세요.")
    else:
        with st.spinner('데이터를 수집하는 중...'):
            try:
                stock_code = get_stock_code_by_company(company_name)
                start_date_str = selected_dates[0].strftime("%Y%m%d")
                end_date_str = selected_dates[1].strftime("%Y%m%d")
                
                df = fdr.DataReader(stock_code, start_date_str, end_date_str)
                
                if df.empty:
                    st.info("해당 기간의 주가 데이터가 없습니다.")
                    st.session_state['price_df'] = None
                    st.session_state['search_triggered'] = False
                else:
                    # 컬럼명 한글로 변경
                    df = df.rename(columns={
                        'Open': '시가', 'High': '고가', 'Low': '저가', 
                        'Close': '종가', 'Volume': '거래량', 'Change': '등락률',
                        'Comp': '회사', 'Code': '코드'
                    })
                    
                    # [수정] 인덱스 이름을 'Date' 또는 'None'에서 '날짜'로 변경
                    df.index.name = '날짜'
                    
                    st.session_state['price_df'] = df
                    st.session_state['company_name_saved'] = company_name
                    st.session_state['search_triggered'] = True

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
                st.session_state['price_df'] = None
                st.session_state['search_triggered'] = False

# -----------------------------------------------------------------------------
# 5. 메인 화면 그리기
# -----------------------------------------------------------------------------
display_subject = st.session_state['company_name_saved'] if st.session_state['company_name_saved'] else ""
st.title(f"'{display_subject}' 주가 데이터 조회" if display_subject else "주가 데이터 조회")
st.divider()

col1, col2 = st.columns([1, 1])

if st.session_state.get('search_triggered') and st.session_state['price_df'] is not None:
    
    price_df = st.session_state['price_df']
    target_company = st.session_state['company_name_saved']

    # 왼쪽 컬럼: 표
    with col1:
        st.subheader(f"📊 [{target_company}] 데이터")
        
        display_df = price_df.copy().sort_index(ascending=False)
        # 인덱스를 문자열로 변환하여 시간 제거 (YYYY-MM-DD)
        display_df.index = display_df.index.strftime("%Y-%m-%d")
        # [수정] 인덱스 이름 명시 (표 상단에 '날짜'라고 표시됨)
        display_df.index.name = "날짜"
        
        st.dataframe(display_df, use_container_width=True)

        # [수정] 현재 시간이 아닌, 데이터의 가장 최신 날짜를 기준으로 표시
        if not price_df.empty:
            last_date = price_df.index.max()
            st.caption(f"KST {last_date.strftime('%Y-%m-%d')} 기준 (일별 데이터)")

    # 오른쪽 컬럼: 그래프 + 슬라이더
    with col2:
        st.subheader(f"📈 [{target_company}] 차트")
        
        chart_placeholder = st.empty()

        min_date = price_df.index.min().date()
        max_date = price_df.index.max().date()

        st.write("▼ 차트 상세 구간 조절")
        slider_range = st.slider(
            "기간 선택",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY.MM.DD"
        )

        with st.spinner('차트 갱신 중...'):
            filtered_df = price_df.loc[str(slider_range[0]):str(slider_range[1])]

            with chart_placeholder:
                fig, ax = plt.subplots(figsize=(10, 5))
                if '종가' in filtered_df.columns:
                    filtered_df['종가'].plot(ax=ax, color='red', linewidth=2)
                    ax.set_title(f"{target_company} 종가 ({slider_range[0]} ~ {slider_range[1]})")
                    ax.set_xlabel("날짜")
                    ax.set_ylabel("가격 (원)")
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.error("종가 데이터를 찾을 수 없습니다.")

            # 엑셀 다운로드
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                excel_df = filtered_df.copy()
                excel_df.index = excel_df.index.strftime("%Y-%m-%d")
                excel_df.index.name = "날짜"  # 엑셀 저장 시에도 A1 셀에 '날짜' 표시
                excel_df.to_excel(writer, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 현재 구간 엑셀 다운로드",
                data=output.getvalue(),
                file_name=f"{target_company}_주가.xlsx",
                mime="application/vnd.ms-excel"
            )