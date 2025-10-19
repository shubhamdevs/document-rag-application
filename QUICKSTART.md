# Quick Start Guide

## Run the Application Locally (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Environment Variables

Check that your `.env` file contains:
```env
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=document-rag-vectors
PINECONE_ENVIRONMENT=us-east-1
AZ_OPENAI_API_KEY=...
AZ_OPENAI_ENDPOINT=https://...
```

### Step 3: Run the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Testing the Application

### 1. Upload a Document
- Click "Browse files" in the sidebar
- Select a PDF, DOCX, or TXT file
- Wait for "Document loaded successfully" message

### 2. Ask Questions
- Type a question about the uploaded document
- Toggle "Use RAG" in the sidebar (should be ON)
- Press Enter
- See the AI response with document context

### 3. View Documents in DB
- Expand "Documents in DB" in sidebar
- See list of uploaded files/URLs

---

## Deploy to Azure (30 Minutes)

Follow the comprehensive guide in `AZURE_DEPLOYMENT_GUIDE.md`

Quick overview:
1. Create Azure Key Vault
2. Store secrets
3. Create Azure Web App
4. Enable Managed Identity
5. Configure Key Vault access
6. Deploy via GitHub Actions

---

## What's New?

**Migrated from ChromaDB to Pinecone:**
- ✅ Cloud-hosted vector database
- ✅ Automatic session cleanup
- ✅ Production-ready architecture
- ✅ Azure-optimized deployment

**See `MIGRATION_SUMMARY.md` for full details.**

---

## Need Help?

- **Deployment Guide:** `AZURE_DEPLOYMENT_GUIDE.md`
- **Migration Details:** `MIGRATION_SUMMARY.md`
- **Pinecone Docs:** https://docs.pinecone.io
- **Azure Docs:** https://docs.microsoft.com/azure
