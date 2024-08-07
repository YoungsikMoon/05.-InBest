from utils import start_streamlit, make_session, print_messages, input_output

# 스트림릿 시작
start_streamlit("문영식")

# 세션이 없으면 만들어라
make_session()

# 이전 대화기록 출력해주는 코드
print_messages()

# 챗봇 활성화
input_output()