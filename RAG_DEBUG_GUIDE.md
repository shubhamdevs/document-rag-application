# RAG Debugging Guide - Troubleshooting "No Results" Issue

## Problem
User uploaded a PDF but RAG queries don't return information from the document.

## Root Causes Identified

### 1. Only 1 Vector Created
- Pinecone shows only 1 vector in the namespace
- This indicates the document wasn't properly chunked
- Could mean the PDF is very small or chunking failed

### 2. Possible Issues
- Document might be empty or have very little text
- PDF might contain images but no extractable text
- Chunking might not be working correctly
- Retriever might not be configured properly

---

## Fixes Applied

### Fix #1: Enhanced Logging
Added detailed logging to track the entire pipeline:

```python
# In _split_and_load_docs()
print(f"Processing {len(docs)} document(s)")
print(f"Total characters: {total_chars:,}")
print(f"✅ Created {len(document_chunks)} chunks from {len(docs)} documents")
```

### Fix #2: Improved Retriever Configuration
Changed retriever to explicitly request 5 results:

```python
retriever = vector_db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}  # Return top 5 chunks
)
```

### Fix #3: Debug Retrieval in Query
Added real-time debugging to see what's being retrieved:

```python
retriever = st.session_state.vector_db.as_retriever(search_kwargs={"k": 5})
docs_retrieved = retriever.get_relevant_documents(messages[-1].content)
print(f"📄 Retrieved {len(docs_retrieved)} documents")
```

---

## How to Test & Debug

### Step 1: Restart the App with Console Visible

```bash
cd "/Users/shubham/Code Block⚙️/AI_Apps/DOCUMENT_RAG_APP"
streamlit run app.py
```

### Step 2: Upload a PDF and Watch Console

You should see output like:

```
============================================================
Processing 1 document(s)
Total characters: 15,234
============================================================

✅ Created 4 chunks from 1 documents
   Average chunk size: 3,808 characters

Initializing Pinecone vector DB with 4 documents
Index: document-rag-vectors, Namespace: session-abc123...
Successfully initialized Pinecone vector store
```

**What to check:**
- ✅ **Total characters** should be > 0 (if 0, PDF has no text)
- ✅ **Number of chunks** should match document size
- ✅ **Vectors created** should equal number of chunks

### Step 3: Ask a Question and Watch Console

When you ask "What is my name?", you should see:

```
============================================================
🤖 RAG Query: What is my name?
============================================================

🔍 Retriever configured: search_type=similarity, k=5
📄 Retrieved 4 documents:
   1. This document belongs to John Smith. He is...
   2. John Smith's information can be found...
   3. The owner of this document, John Smith...
   4. Contact information for John Smith...
```

**What to check:**
- ✅ **Retrieved X documents** should show the chunks found
- ✅ **Content preview** should show relevant text
- ❌ **If 0 documents retrieved**, the search isn't working

---

## Common Issues & Solutions

### Issue 1: "Total characters: 0"
**Problem:** PDF contains only images, no extractable text

**Solution:**
- Use a PDF with actual text content
- Or add OCR capability (tesseract)
- Try a simple text file first to verify the system works

**Test:**
```bash
# Create a test document
echo "My name is Shubham Kumar. I work as a software engineer." > test.txt

# Upload test.txt and ask: "What is my name?"
# Should get: "Your name is Shubham Kumar"
```

### Issue 2: "Created 1 chunks"
**Problem:** Document is very small (< 5000 characters)

**This is OK!** Even 1 chunk can work if it contains the information.

**Check:**
- Does the console show the content when querying?
- Is the relevant information in that 1 chunk?

### Issue 3: "Retrieved 0 documents"
**Problem:** Search isn't finding relevant chunks

**Possible causes:**
1. Query embedding dimension mismatch (we fixed this)
2. Namespace mismatch
3. No vectors actually stored in Pinecone

**Debug:**
```python
# Check Pinecone directly
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('document-rag-vectors')
stats = index.describe_index_stats()

print(f"Total vectors: {stats['total_vector_count']}")
print(f"Namespaces: {stats['namespaces']}")
```

### Issue 4: Session Namespace Mismatch
**Problem:** Vectors uploaded to one namespace, searching in another

**Solution:** Make sure you're using the same session

**Check in console:**
```
# When uploading:
Namespace: session-abc123-def456-...

# When querying:
Namespace: session-abc123-def456-...  # Must match!
```

---

## Diagnostic Checklist

Run through this checklist with the console open:

### ✅ Document Upload
- [ ] Upload a PDF
- [ ] Check console: "Processing X document(s)"
- [ ] Check console: "Total characters: X,XXX"
- [ ] Verify total characters > 0
- [ ] Check console: "Created X chunks"
- [ ] Verify chunks >= 1
- [ ] Check console: "Successfully initialized Pinecone"
- [ ] Check "Documents in DB" shows your file

### ✅ Pinecone Verification
Run this in terminal:
```python
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('document-rag-vectors')
stats = index.describe_index_stats()

print(f"Total vectors: {stats['total_vector_count']}")
for ns, data in stats['namespaces'].items():
    print(f"  {ns}: {data['vector_count']} vectors")
```

- [ ] Total vectors > 0
- [ ] Your session namespace exists
- [ ] Vector count matches chunks created

### ✅ Query Test
- [ ] Toggle "Use RAG" ON
- [ ] Ask a question from your document
- [ ] Check console: "🤖 RAG Query: your question"
- [ ] Check console: "📄 Retrieved X documents"
- [ ] Verify X > 0
- [ ] Check console shows content previews
- [ ] Verify content is relevant to your question

### ✅ Response Check
- [ ] Response starts with "*(RAG Response)*"
- [ ] Response includes information from your document
- [ ] Response answers your question correctly

---

## Testing with Known Document

Create a test document to verify everything works:

### Create test.txt:
```
My name is Shubham Kumar.
I am a software engineer working on AI applications.
I live in India and use Python for development.
My favorite framework is Streamlit.
I work with Azure OpenAI and Pinecone for RAG applications.
```

### Test Steps:
1. Upload test.txt
2. Console should show: "Total characters: 200+" (or similar)
3. Console should show: "Created 1 chunks" (small file)
4. Ask: "What is my name?"
5. Console should show: "Retrieved 1 documents"
6. Console should show preview: "My name is Shubham Kumar..."
7. Response should say: "Your name is Shubham Kumar"

If this works → Your system is fine, the PDF might be the issue
If this fails → There's a system issue to debug further

---

## Advanced Debugging

### Check Vector Store Connection:
```python
# In Python console
import streamlit as st
from rag_methods import get_pinecone_client

# Get Pinecone client
pc = get_pinecone_client()
index = pc.Index('document-rag-vectors')

# Query directly
from langchain_openai import AzureOpenAIEmbeddings
import os

embedding = AzureOpenAIEmbeddings(
    api_key=os.getenv('AZ_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZ_OPENAI_ENDPOINT'),
    azure_deployment='text-embedding-3-large',
    openai_api_version='2024-02-15-preview',
    dimensions=1024,
)

# Create query vector
query = "What is my name?"
query_vector = embedding.embed_query(query)

# Search in Pinecone
results = index.query(
    vector=query_vector,
    top_k=5,
    namespace="session-YOUR-SESSION-ID",  # Replace with actual session ID
    include_metadata=True
)

print(f"Found {len(results['matches'])} matches")
for match in results['matches']:
    print(f"Score: {match['score']}, Text: {match['metadata'].get('text', 'N/A')[:100]}")
```

---

## Next Steps

1. **Start the app with console visible**
   ```bash
   streamlit run app.py
   ```

2. **Upload your PDF again** and watch the console output

3. **Share the console output** with:
   - Total characters
   - Number of chunks created
   - Number of documents retrieved when querying
   - Content previews (if any)

4. **If still no results**, try the test.txt file to isolate if it's a PDF issue or system issue

---

## Expected Console Output (Working System)

```
=============================================================
Processing 1 document(s)
Total characters: 15,234
=============================================================

✅ Created 4 chunks from 1 documents
   Average chunk size: 3,808 characters

Initializing Pinecone vector DB with 4 documents
Index: document-rag-vectors, Namespace: session-abc123-def456
Successfully initialized Pinecone vector store

[User asks question]

=============================================================
🤖 RAG Query: What is my name?
=============================================================

🔍 Retriever configured: search_type=similarity, k=5
📄 Retrieved 4 documents:
   1. This document contains information about Shubham Kumar. He is...
   2. Shubham Kumar's details are as follows...
   3. The name mentioned in this document is Shubham Kumar...
   4. Contact: Shubham Kumar, Email: shubham@example.com...
```

If you see this, RAG is working correctly!

---

## Quick Fix Summary

All the fixes are already applied in the code:
- ✅ Dimension fix (1024 dimensions)
- ✅ Enhanced logging
- ✅ Retriever configuration (k=5)
- ✅ Debug output for retrieved docs
- ✅ Better error handling

**Just restart the app and try uploading again!**
