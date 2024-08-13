import utils as ut
import importlib
importlib.reload(ut)

# 스트림릿 시작 [제목+사이드바생성]
ut.start_streamlit("InBest")

# 세션 초기 설정
ut.session_init()

# 사이드바
ut.side_bar()

# 이전 대화기록 출력해주는 코드
ut.print_messages()

# 챗봇
ut.chatbot()