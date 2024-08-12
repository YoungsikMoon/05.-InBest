import utils as ut
# import importlib
# importlib.reload(ut)

# 스트림릿 시작 [제목+사이드바생성]
ut.start_streamlit("InBest")

# 세션이 없으면 만들어라
ut.service_init()

# 이전 대화기록 출력해주는 코드
ut.print_messages()

# 챗봇 활성화
ut.input_output()