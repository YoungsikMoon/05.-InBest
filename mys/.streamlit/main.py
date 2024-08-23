import utils as ut
import importlib
# 모듈 새로 고침
# importlib.reload(ut)
# 스트림릿 시작 (제목 + 사이드바 생성)
ut.start_streamlit("InBest")

# 세션 초기 설정 및 사이드바 생성
ut.session_init()
ut.side_bar()

# 이전 대화기록 출력 및 챗봇 생성
ut.print_messages()
ut.chatbot()
