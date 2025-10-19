# Document RAG Application

A production-ready Retrieval-Augmented Generation (RAG) application built with Streamlit, Pinecone, and Azure OpenAI.

## Features

- **Multiple Document Formats:** Upload PDF, DOCX, TXT, and Markdown files
- **Web Content:** Load documents from URLs
- **Cloud Vector Database:** Pinecone for scalable, persistent vector storage
- **Session Isolation:** Each user session gets isolated namespace
- **Azure OpenAI Integration:** Powered by GPT-4o and text-embedding-3-large
- **Real-time Streaming:** Responses stream in real-time
- **Easy Reset:** Clear all documents and vectors with one click

---

## Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create/verify `.env` file:
```env
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=document-rag-vectors
PINECONE_ENVIRONMENT=us-east-1
AZ_OPENAI_API_KEY=your_azure_key
AZ_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
```

### 3. Run the App
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## How to Use

### Upload Documents
1. Click "Browse files" in the sidebar
2. Select PDF, DOCX, TXT, or MD files
3. Wait for "Document loaded successfully" notification

### Ask Questions
1. Ensure "Use RAG" toggle is ON
2. Type your question in the chat input
3. Get AI-powered answers based on your documents

### Reset Session
- Click "🗑️ Reset" to clear all documents and vectors
- Start fresh with new documents

---

## Architecture

```
┌──────────────────────────────────────────────┐
│         STREAMLIT UI (Browser)               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│         APP.PY (Main Application)            │
│  - Session Management                        │
│  - File Upload Handling                      │
│  - Chat Interface                            │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│       RAG_METHODS.PY (Core Logic)            │
│  - Document Processing                       │
│  - Vector Store Management                   │
│  - RAG Pipeline                              │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐ ┌─────────────────────┐
│  PINECONE CLOUD │ │  AZURE OPENAI       │
│  - Vector Store │ │  - GPT-4o           │
│  - Embeddings   │ │  - Embeddings       │
│  - Search       │ │  - Generation       │
└─────────────────┘ └─────────────────────┘
```

---

## Project Structure

```
DOCUMENT_RAG_APP/
├── app.py                      # Main Streamlit application
├── rag_methods.py              # RAG logic and vector operations
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (gitignored)
├── .gitignore                  # Git ignore rules
│
├── docs/
│   └── rag.pdf                 # Sample document
│
├── source_files/               # Temporary upload directory
│
├── .github/workflows/
│   └── main_document-rag-application.yml  # Azure deployment
│
└── Documentation/
    ├── README.md               # This file
    ├── QUICKSTART.md           # Quick start guide
    ├── MIGRATION_SUMMARY.md    # ChromaDB → Pinecone migration
    ├── AZURE_DEPLOYMENT_GUIDE.md  # Azure deployment steps
    └── FIXES_AND_IMPROVEMENTS.md  # Recent fixes and improvements
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit 1.50.0 | Web UI and chat interface |
| **LLM** | Azure OpenAI GPT-4o | Answer generation |
| **Embeddings** | text-embedding-3-large | Vector generation (1024 dims) |
| **Vector DB** | Pinecone (Serverless) | Cloud vector storage and search |
| **Framework** | LangChain 0.3.27 | RAG orchestration |
| **Deployment** | Azure Web Apps | Cloud hosting |
| **CI/CD** | GitHub Actions | Automated deployment |

---

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PINECONE_API_KEY` | Pinecone API key | `pcsk_...` |
| `PINECONE_INDEX_NAME` | Pinecone index name | `document-rag-vectors` |
| `PINECONE_ENVIRONMENT` | Pinecone region | `us-east-1` |
| `AZ_OPENAI_API_KEY` | Azure OpenAI API key | `5eUwlkqs...` |
| `AZ_OPENAI_ENDPOINT` | Azure OpenAI endpoint | `https://...` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `sk-proj-...` |

### Application Settings

In `rag_methods.py`:
```python
DB_DOCS_LIMIT = 10  # Max documents per session

# Text splitting
chunk_size = 5000      # Characters per chunk
chunk_overlap = 1000   # Overlap between chunks
```

---

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Azure Cloud
Follow the comprehensive guide in `AZURE_DEPLOYMENT_GUIDE.md`:
1. Create Azure Key Vault
2. Store secrets
3. Create Azure Web App (Python 3.12)
4. Configure Managed Identity
5. Deploy via GitHub Actions

**Estimated deployment time:** 30-45 minutes

---

## Features in Detail

### Document Processing
- **Supported Formats:** PDF, DOCX, TXT, Markdown, Web URLs
- **Text Splitting:** 5000-character chunks with 1000-character overlap
- **Deduplication:** Prevents duplicate document uploads
- **Limit:** Maximum 10 documents per session

### Vector Storage
- **Provider:** Pinecone Serverless (AWS us-east-1)
- **Dimensions:** 1024 (text-embedding-3-large)
- **Metric:** Cosine similarity
- **Isolation:** Namespace per session (`session-{uuid}`)

### RAG Pipeline
1. **Query Vectorization:** Convert user question to embedding
2. **Semantic Search:** Find relevant chunks in Pinecone
3. **Context Retrieval:** Get top-K most relevant chunks
4. **Answer Generation:** GPT-4o generates answer with context
5. **Streaming:** Response streams in real-time

### Session Management
- **UUID-based:** Each browser session gets unique ID
- **Namespace Isolation:** Vectors stored in session-specific namespace
- **Reset Capability:** Clear all vectors with one click
- **Automatic Cleanup:** Handled through Reset button

---

## API Usage

### Costs (Approximate)

**Pinecone:**
- Free tier: 1M vectors (sufficient for this use case)
- Serverless pricing: ~$0.10/million queries

**Azure OpenAI:**
- GPT-4o: ~$5 per 1M input tokens
- text-embedding-3-large: ~$0.13 per 1M tokens

**Azure Web App:**
- B1 tier: ~$13/month
- Includes 100 GB bandwidth

**Estimated monthly cost:** $15-30 (excluding heavy usage)

---

## Troubleshooting

### App won't start
```bash
# Verify Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Pinecone connection fails
```bash
# Test connection
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='YOUR_KEY'); print(pc.list_indexes())"
```

### Azure OpenAI errors
- Verify endpoint URL (should end with `.openai.azure.com/`)
- Check API key is valid
- Ensure deployment names match (text-embedding-3-large, gpt-4o)

### Document upload fails
- Check file size (should be < 200MB)
- Verify file format is supported
- Look at console logs for specific errors

---

## Development

### Running Tests
```bash
# Test imports
python -c "import app; import rag_methods; print('✅ Imports OK')"

# Test Pinecone connection
python -c "from rag_methods import get_pinecone_client; pc = get_pinecone_client(); print('✅ Pinecone OK')"

# Test app startup
streamlit run app.py
```

### Code Structure
- **app.py:** Streamlit UI, session management, user interaction
- **rag_methods.py:** Document processing, vector operations, RAG pipeline
- **Clean separation:** UI logic separate from business logic

---

## Security

### Best Practices
- ✅ API keys in `.env` (gitignored)
- ✅ Azure Key Vault for production secrets
- ✅ Managed Identity for Azure resources
- ✅ No hardcoded credentials
- ✅ HTTPS only in production

### Session Isolation
- Each session has unique UUID
- Vectors stored in session-specific namespace
- No cross-session data access
- Clean reset capability

---

## Performance

### Optimizations
- **Streaming Responses:** Real-time token delivery
- **Efficient Chunking:** 5000/1000 split for context preservation
- **Pinecone Serverless:** Auto-scaling, low latency
- **Session Caching:** Vector DB cached in session state

### Limits
- Max 10 documents per session
- Max file size: 200MB (configurable)
- Concurrent users: Limited by Azure tier

---

## Contributing

### Development Workflow
1. Create feature branch
2. Make changes
3. Test locally
4. Update documentation
5. Create pull request

### Code Style
- Follow PEP 8
- Add docstrings to functions
- Comment complex logic
- Use type hints where helpful

---

## Support

### Documentation
- **Quick Start:** `QUICKSTART.md`
- **Azure Deployment:** `AZURE_DEPLOYMENT_GUIDE.md`
- **Migration Notes:** `MIGRATION_SUMMARY.md`
- **Recent Fixes:** `FIXES_AND_IMPROVEMENTS.md`

### Resources
- **Pinecone Docs:** https://docs.pinecone.io
- **LangChain Docs:** https://python.langchain.com
- **Streamlit Docs:** https://docs.streamlit.io
- **Azure Docs:** https://docs.microsoft.com/azure

---

## License

This project is for educational and internal use.

---

## Changelog

### v2.0.0 (Current) - Pinecone Migration
- ✅ Migrated from ChromaDB to Pinecone
- ✅ Added session-based namespace isolation
- ✅ Implemented Reset functionality
- ✅ Removed SQLite dependencies
- ✅ Added comprehensive documentation
- ✅ Azure deployment ready

### v1.0.0 - Initial Release
- Basic RAG functionality with ChromaDB
- Local vector storage
- OpenAI/Azure OpenAI support

---

## Status

**✅ Production Ready**

- All features working
- Tested and verified
- Documentation complete
- Azure deployment configured
- Ready for local testing and cloud deployment

---

**Built with ❤️ using Streamlit, Pinecone, and Azure OpenAI**
