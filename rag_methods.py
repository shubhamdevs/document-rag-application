import os
import dotenv
from time import time
import streamlit as st
from pinecone import Pinecone, ServerlessSpec

from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
# pip install docx2txt, pypdf
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

dotenv.load_dotenv()

# os.environ["USER_AGENT"] = "myagent"
DB_DOCS_LIMIT = 10

# Function to cleanup current session namespace
def cleanup_current_session():
    """Delete vectors from current session namespace in Pinecone"""
    try:
        if "session_id" in st.session_state and st.session_state.session_id:
            pc = get_pinecone_client()
            index_name = os.getenv("PINECONE_INDEX_NAME", "document-rag-vectors")
            index = pc.Index(index_name)

            current_namespace = f"session-{st.session_state.session_id}"

            # Delete all vectors in the current namespace
            index.delete(delete_all=True, namespace=current_namespace)
            print(f"Cleaned up current session namespace: {current_namespace}")

            # Clear session state
            if "vector_db" in st.session_state:
                del st.session_state.vector_db
            if "rag_sources" in st.session_state:
                st.session_state.rag_sources = []

    except Exception as e:
        print(f"Error during session cleanup: {e}")
        # Don't raise - cleanup is optional


# Function to stream the response of the LLM
def stream_llm_response(llm_stream, messages):
    response_message = ""

    for chunk in llm_stream.stream(messages):
        response_message += chunk.content
        yield chunk

    st.session_state.messages.append({"role": "assistant", "content": response_message})


# --- Indexing Phase ---

def load_doc_to_db():
    # Use loader according to doc type
    if "rag_docs" in st.session_state and st.session_state.rag_docs:
        docs = []
        loaded_files = []
        for doc_file in st.session_state.rag_docs:
            if doc_file.name not in st.session_state.rag_sources:
                if len(st.session_state.rag_sources) < DB_DOCS_LIMIT:
                    os.makedirs("source_files", exist_ok=True)
                    file_path = f"./source_files/{doc_file.name}"
                    with open(file_path, "wb") as file:
                        file.write(doc_file.read())

                    try:
                        if doc_file.type == "application/pdf":
                            loader = PyPDFLoader(file_path)
                        elif doc_file.name.endswith(".docx"):
                            loader = Docx2txtLoader(file_path)
                        elif doc_file.type in ["text/plain", "text/markdown"]:
                            loader = TextLoader(file_path)
                        else:
                            st.warning(f"Document type {doc_file.type} not supported.")
                            continue

                        docs.extend(loader.load())
                        st.session_state.rag_sources.append(doc_file.name)
                        loaded_files.append(doc_file.name)

                    except Exception as e:
                        st.toast(f"Error loading document {doc_file.name}: {e}", icon="⚠️")
                        print(f"Error loading document {doc_file.name}: {e}")
                    
                    finally:
                        os.remove(file_path)

                else:
                    st.error(F"Maximum number of documents reached ({DB_DOCS_LIMIT}).")

        if docs and loaded_files:
            _split_and_load_docs(docs)
            st.toast(f"Document *{', '.join(loaded_files)}* loaded successfully.", icon="✅")

def load_url_to_db():
    if "rag_url" in st.session_state and st.session_state.rag_url:
        url = st.session_state.rag_url
        docs = []
        if url not in st.session_state.rag_sources:
            if len(st.session_state.rag_sources) < 10:
                try:
                    with st.spinner(f"Loading content from {url}..."):
                        print(f"Loading URL: {url}")  # Debug log
                        loader = WebBaseLoader(url)
                        docs.extend(loader.load())
                        print(f"Loaded {len(docs)} documents from URL")  # Debug log

                    if docs and len(docs) > 0:
                        # Check if documents have content
                        total_content = sum(len(doc.page_content.strip()) for doc in docs)
                        print(f"Total content length: {total_content} characters")  # Debug log

                        if total_content > 0:
                            print("Processing documents...")  # Debug log
                            _split_and_load_docs(docs)
                            st.session_state.rag_sources.append(url)
                            st.toast(f"Document from URL *{url}* loaded successfully. ({len(docs)} pages, {total_content} chars)", icon="✅")
                        else:
                            st.warning(f"No content found at URL: {url}")
                    else:
                        st.warning(f"No documents loaded from URL: {url}")

                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"Error loading document from {url}: {str(e)}")
                    print(f"Full error details for URL {url}:")
                    print(error_details)  # Full traceback for debugging

            else:
                st.error("Maximum number of documents reached (10).")
        else:
            st.info(f"URL already loaded: {url}")

# Helper function to get Pinecone client
def get_pinecone_client():
    """Initialize and return Pinecone client"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    return Pinecone(api_key=api_key)

# Helper function to get embedding model
def get_embedding_model():
    """Initialize and return the appropriate embedding model"""
    try:
        if "AZ_OPENAI_API_KEY" not in os.environ:
            # Check if API key exists in session state
            if "openai_api_key" not in st.session_state or not st.session_state.openai_api_key:
                raise ValueError("OpenAI API key not found in session state")

            api_key = st.session_state.openai_api_key
            print(f"Using OpenAI API key: {api_key[:7]}...")  # Debug log
            embedding = OpenAIEmbeddings(api_key=api_key)
        else:
            print("Using Azure OpenAI embeddings")  # Debug log
            print(f"Azure endpoint: {os.getenv('AZ_OPENAI_ENDPOINT')}")
            print(f"API version: 2024-02-15-preview")
            try:
                embedding = AzureOpenAIEmbeddings(
                    api_key=os.getenv("AZ_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
                    azure_deployment="text-embedding-3-large",
                    openai_api_version="2024-02-15-preview",
                    dimensions=1024,  # Match Pinecone index dimension
                )
                print("Azure OpenAI embeddings initialized successfully (1024 dimensions)")
            except Exception as embed_error:
                print(f"Failed to initialize Azure embeddings: {embed_error}")
                print("Trying alternative deployment names...")
                # Try common alternative names
                for deployment_name in ["text-embedding-3-large", "embedding", "embeddings", "text-embedding-ada-002"]:
                    try:
                        print(f"Trying deployment name: {deployment_name}")
                        # Set dimensions based on model
                        dims = 1024 if "3-large" in deployment_name else 1536
                        embedding = AzureOpenAIEmbeddings(
                            api_key=os.getenv("AZ_OPENAI_API_KEY"),
                            azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
                            azure_deployment=deployment_name,
                            openai_api_version="2024-02-15-preview",
                            dimensions=dims,
                        )
                        print(f"Success with deployment name: {deployment_name} ({dims} dimensions)")
                        break
                    except Exception as e:
                        print(f"Failed with {deployment_name}: {str(e)[:100]}")
                        continue
                else:
                    raise embed_error

        return embedding
    except Exception as e:
        print(f"Error in embedding initialization: {e}")
        raise e

# Embedding - Initialize Pinecone Vector Store
def initialize_vector_db(docs):
    """Initialize Pinecone vector store with documents"""
    try:
        # Get embedding model
        embedding = get_embedding_model()

        # Get Pinecone configuration
        index_name = os.getenv("PINECONE_INDEX_NAME", "document-rag-vectors")
        namespace = f"session-{st.session_state['session_id']}"

        print(f"Initializing Pinecone vector DB with {len(docs)} documents")
        print(f"Index: {index_name}, Namespace: {namespace}")

        # Initialize Pinecone vector store
        vector_db = PineconeVectorStore.from_documents(
            documents=docs,
            embedding=embedding,
            index_name=index_name,
            namespace=namespace,
        )

        print(f"Successfully initialized Pinecone vector store")
        return vector_db

    except Exception as e:
        print(f"Error initializing Pinecone vector DB: {e}")
        raise e


def _split_and_load_docs(docs):
    """Split documents and load them into Pinecone"""
    # Log original document stats
    total_chars = sum(len(doc.page_content) for doc in docs)
    print(f"\n{'='*60}")
    print(f"Processing {len(docs)} document(s)")
    print(f"Total characters: {total_chars:,}")
    print(f"{'='*60}\n")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=1000,
    )

    document_chunks = text_splitter.split_documents(docs)

    print(f"✅ Created {len(document_chunks)} chunks from {len(docs)} documents")
    print(f"   Average chunk size: {total_chars // max(len(document_chunks), 1):,} characters")

    if "vector_db" not in st.session_state:
        st.session_state.vector_db = initialize_vector_db(document_chunks)
    else:
        # Add documents to existing Pinecone namespace
        index_name = os.getenv("PINECONE_INDEX_NAME", "document-rag-vectors")
        namespace = f"session-{st.session_state['session_id']}"

        # Use the existing vector store to add new documents
        st.session_state.vector_db.add_documents(document_chunks)
        print(f"✅ Added {len(document_chunks)} chunks to Pinecone namespace: {namespace}")


# Retrival Phase

def _get_context_retriever_chain(vector_db, llm):
    # Configure retriever to return more results
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # Return top 5 most relevant chunks
    )

    print(f"🔍 Retriever configured: search_type=similarity, k=5")

    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="messages"),
        ("user", "{input}"),
        ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation, focusing on the most recent messages."),
    ])
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)

    return retriever_chain


def get_conversational_rag_chain(llm):
    retriever_chain = _get_context_retriever_chain(st.session_state.vector_db, llm)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
        """You are a helpful assistant. You will have to answer to user's queries.
        You will have some context to help with your answers, but now always would be completely related or helpful.
        You can also use your knowledge to assist answering the user's queries.\n
        {context}"""),
        MessagesPlaceholder(variable_name="messages"),
        ("user", "{input}"),
    ])
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)

    return create_retrieval_chain(retriever_chain, stuff_documents_chain)


def stream_llm_rag_response(llm_stream, messages):
    print(f"\n{'='*60}")
    print(f"🤖 RAG Query: {messages[-1].content}")
    print(f"{'='*60}\n")

    conversation_rag_chain = get_conversational_rag_chain(llm_stream)
    response_message = "*(RAG Response)*\n"

    # Debug: Try to see what's being retrieved
    try:
        # Get the retriever for debugging
        retriever = st.session_state.vector_db.as_retriever(search_kwargs={"k": 5})
        docs_retrieved = retriever.get_relevant_documents(messages[-1].content)
        print(f"📄 Retrieved {len(docs_retrieved)} documents:")
        for i, doc in enumerate(docs_retrieved, 1):
            preview = doc.page_content[:200].replace('\n', ' ')
            print(f"   {i}. {preview}...")
    except Exception as e:
        print(f"⚠️  Debug retrieval failed: {e}")

    for chunk in conversation_rag_chain.pick("answer").stream({"messages": messages[:-1], "input": messages[-1].content}):
        response_message += chunk
        yield chunk

    st.session_state.messages.append({"role": "assistant", "content": response_message})



