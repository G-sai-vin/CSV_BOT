import os
import requests
import base64
import json
import openai
import streamlit as st
from streamlit_chat import message
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import ConversationChain
from langchain.document_loaders.csv_loader import CSVLoader
import tempfile

# Cisco Authentication
client_id = 'cG9jLXRyaWFsMjAyNEF1Z3VzdDA3_cfdaf9d6cd4d4cb59646de55bf18a4'
client_secret = 'vmxOYAuwO7rmkKnIKYu9tqMb7sKcmbekQ39cBFbg2k57RbziifppC3Ez7xoqtOaL'
url = "https://id.cisco.com/oauth2/default/v1/token"

payload = "grant_type=client_credentials"
value = base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')
headers = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {value}"
}

token_response = requests.request("POST", url, headers=headers, data=payload)
api_token = token_response.json()["access_token"]

# Azure OpenAI Chat Model
CISCO_OPENAI_APP_KEY = 'egai-prd-ntd-fw-ai-automate-unit-test-case-gen-1'
CISCO_BRAIN_USER_ID = ''
print(CISCO_OPENAI_APP_KEY)
llm = AzureChatOpenAI(
    deployment_name="gpt-4o-mini", 
    azure_endpoint='https://chat-ai.cisco.com', 
    api_key=api_token,  
    api_version="2023-08-01-preview",
    model_kwargs={
        "user": json.dumps({"appkey": CISCO_OPENAI_APP_KEY})
    }
)

# Streamlit App
st.title("CSV Chatbot with Azure OpenAI")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()
    
    # Convert CSV data into context for LLM
    csv_content = "\n".join([doc.page_content for doc in data])

    # Conversation Memory
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    conversation = ConversationChain(llm=llm)

    def chatbot_response(query):
        response = conversation.run(f"Based on this CSV data: {csv_content}, answer the following: {query}")
        st.session_state['history'].append((query, response))
        return response

    user_input = st.text_input("Ask a question about your CSV data:")
    if user_input:
        output = chatbot_response(user_input)
        st.write(output)

    # Display chat history
    if st.session_state['history']:
        for q, r in st.session_state['history']:
            message(q, is_user=True)
            message(r)
