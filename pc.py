import streamlit as st
import PyPDF2
import time
from anthropic import Anthropic

@st.cache_resource
def load_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "".join(page.extract_text() for page in pdf_reader.pages)
    return text

def chat_with_claude(client, pdf_content, user_input, chat_history):
    system_message = "당신은 HR 인사팀 전문가입니다. 주어진 PDF 내용을 바탕으로 사용자의 질문에 답변해주세요."
    messages = [
        {"role": "user", "content": f"다음은 PDF의 내용입니다: {pdf_content[:2000]}... [PDF 내용 중략]"}
    ] + chat_history + [{"role": "user", "content": user_input}]
    
    start_time = time.time()
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            system=system_message,
            max_tokens=1000
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 응답 객체의 구조를 확인하고 적절한 속성을 사용합니다
        if hasattr(response.usage, 'input_tokens'):
            input_tokens = response.usage.input_tokens
        elif hasattr(response.usage, 'prompt_tokens'):
            input_tokens = response.usage.prompt_tokens
        else:
            input_tokens = "정보 없음"
        
        return response.content[0].text, execution_time, input_tokens
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None, None, None


def main():
    st.title("[Philosophy AI Edu 인사팀] 인사에 관해 무엇이든 물어보세요 (휴가, 승진, 복지 등)")
    api_key = st.text_input("Claude API 키를 입력하세요", type="password")
    file_path = "HR.pdf"

    if api_key:
        client = Anthropic(api_key=api_key)
        pdf_content = load_pdf(file_path)

        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "metadata" not in st.session_state:
            st.session_state.metadata = []

        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
            if i < len(st.session_state.metadata):
                metadata = st.session_state.metadata[i]
                st.text(f"실행 시간: {metadata['execution_time']:.2f}초")
                st.text(f"입력 토큰: {metadata['input_tokens']}")

        if prompt := st.chat_input("회사에 관해 궁금한 점을 질문해주세요"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response, execution_time, input_tokens = chat_with_claude(client, pdf_content, prompt, st.session_state.messages)
                if response is not None:
                    st.markdown(response)
                    st.text(f"실행 시간: {execution_time:.2f}초")
                    st.text(f"입력 토큰: {input_tokens}")
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.metadata.append({
                        "execution_time": execution_time,
                        "input_tokens": input_tokens
                    })
                else:
                    st.error("응답을 받지 못했습니다. 다시 시도해 주세요.")

if __name__ == "__main__":
    main()
