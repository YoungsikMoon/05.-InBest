import utils as ut
# import importlib
# importlib.reload(ut)

# 스트림릿 시작
ut.start_streamlit("문영식")

# 세션이 없으면 만들어라
ut.make_session()

# 이전 대화기록 출력해주는 코드
ut.print_messages()

# 챗봇 활성화
ut.input_output()