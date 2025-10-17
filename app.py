import streamlit as st
import os
import dotenv
import uuid


# check if it's linux so it works on Streamlit Cloud
if os.name == 'posix':
    try:
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        # pysqlite3 not available, use default sqlite3
        pass



from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage

from rag_methods import (
    load_doc_to_db, 
    load_url_to_db,
    stream_llm_response,
    stream_llm_rag_response,
)



dotenv.load_dotenv()

if "AZ_OPENAI_API_KEY" not in os.environ:
    MODELS = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ]
else:
    MODELS = [
        "azure_openai/gpt-4o",
    ]


st.set_page_config(
    page_title="RAG LLM aap?",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="expanded"
)


# --- Header ---
st.html("""<h2 style="text-align: center;"><i> Document RAG Application </i></h2>""")


# --- Initial Setup ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "rag_sources" not in st.session_state:
    st.session_state.rag_sources = []

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I assist you today?"}
]
    
with st.sidebar:
    if "AZ_OPENAI_API_KEY" not in os.environ:
        default_openai_api_key = os.getenv("OPENAI_API_KEY") if os.getenv("OPENAI_API_KEY") is not None else ""  # only for development environment, otherwise it should return None
        with st.popover("🔐 OpenAI"):
            openai_api_key = st.text_input(
                "Introduce your OpenAI API Key (https://platform.openai.com/)",
                value=default_openai_api_key,
                type="password",
                key="openai_api_key",
            )
            st.session_state.openai_api_key = openai_api_key
    else:
        
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        az_openai_api_key = os.getenv("AZ_OPENAI_API_KEY")
        st.session_state.az_openai_api_key = az_openai_api_key


# Checking if the user has introduced the OpenAI API key, if not, a warning is shown
missing_openai = openai_api_key == "" or openai_api_key is None or "sk-" not in openai_api_key

if missing_openai and ("AZ_OPENAI_API_KEY" not in os.environ):
    st.write("#")
    st.warning("⬅Please introduce an API Key to continue...")

else:
    # Sidebar
    with st.sidebar:
        st.divider()
        models = []
        for model in MODELS:
            if "openai" in model and not missing_openai:
                models.append(model)
            elif "azure_openai" in model:
                models.append(model)
        
        st.selectbox(
            "🤖 Select a Model", 
            options=models,
            key="model",
        )

        cols0 = st.columns(2)
        with cols0[0]:
            is_vector_db_loaded = ("vector_db" in st.session_state and st.session_state.vector_db is not None)
            st.toggle(
                "Use RAG", 
                value=is_vector_db_loaded, 
                key="use_rag", 
                disabled=not is_vector_db_loaded,
            )
        
        with cols0[1]:
            st.button("Clear Chat", on_click=lambda: st.session_state.messages.clear(), type="primary")

        st.header("RAG Sources:")
            
        # File upload input for RAG with documents
        st.file_uploader(
            "📄 Upload a document", 
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            on_change=load_doc_to_db,
            key="rag_docs",
        )

        # URL input for RAG with websites
        st.text_input(
            "🌐 Introduce a URL", 
            placeholder="https://example.com",
            on_change=load_url_to_db,
            key="rag_url",
        )

        with st.expander(f"📚 Documents in DB ({0 if not is_vector_db_loaded else len(st.session_state.rag_sources)})"):
            st.write([] if not is_vector_db_loaded else [source for source in st.session_state.rag_sources])

    # Main Chat application
    if "model" not in st.session_state or not st.session_state.model:
        st.error("Please select a model to continue.")
        st.stop()

    model_provider = st.session_state.model.split("/")[0]
    if model_provider == "openai":
        llm_stream = ChatOpenAI(
            api_key=openai_api_key,
            model_name=st.session_state.model.split("/")[-1],
            temperature=0.3,
            streaming=True,
        )
    elif model_provider == "azure_openai":
        llm_stream = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
            openai_api_version="2024-02-15-preview",
            model_name=st.session_state.model.split("/")[-1],
            openai_api_key=os.getenv("AZ_OPENAI_API_KEY"),
            openai_api_type="azure",
            temperature=0.3,
            streaming=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Your message"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            messages = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in st.session_state.messages]

            if not st.session_state.use_rag:
                st.write_stream(stream_llm_response(llm_stream, messages))
            else:
                st.write_stream(stream_llm_rag_response(llm_stream, messages))
            