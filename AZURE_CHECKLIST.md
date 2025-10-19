# Azure Deployment Checklist

## ✅ Things You've Already Done
- [x] Added environment variables to Azure Web App

---

## 🔑 Critical Items to Verify

### 1. Environment Variables in Azure Web App

Go to: **Azure Portal** → **Your Web App** → **Configuration** → **Application settings**

Verify these variables exist:

| Variable Name | Example Value | Status |
|---------------|---------------|--------|
| `PINECONE_API_KEY` | `pcsk_...` | ✅ Added |
| `PINECONE_INDEX_NAME` | `document-rag-vectors` | ✅ Added |
| `PINECONE_ENVIRONMENT` | `us-east-1` | ✅ Added |
| `AZ_OPENAI_API_KEY` | `5eUwlkqs...` | ✅ Added |
| `AZ_OPENAI_ENDPOINT` | `https://...openai.azure.com/` | ✅ Added |
| `OPENAI_API_KEY` | `sk-proj-...` (optional) | ⚠️ Optional |

**Important:** Click **"Save"** at the top after adding variables!

---

### 2. Startup Command

**Location:** Azure Portal → Your Web App → **Configuration** → **General settings** → **Startup Command**

**Set to:**
```bash
python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true
```

**Why this is important:**
- Azure assigns port dynamically
- `--server.port=8000` is standard for Azure
- `--server.address=0.0.0.0` allows external connections
- `--server.headless=true` runs without browser

**Screenshot of where to add:**
```
Configuration → General settings
├── Stack: Python 3.12
├── Major version: Python 3.12
├── Minor version: (Latest)
└── Startup Command: [Enter command above]
```

Click **"Save"**!

---

### 3. Python Version

**Location:** Azure Portal → Your Web App → **Configuration** → **General settings**

**Verify:**
- **Stack:** Python
- **Python version:** 3.12

**If different:**
1. Change to Python 3.12
2. Click **"Save"**
3. Wait for restart

---

### 4. App Service Plan

**Location:** Azure Portal → Your Web App → **Scale up (App Service plan)**

**Recommended minimum:**
- **Tier:** B1 (Basic) or higher
- **Why:** F1 (Free) has memory limitations that may cause crashes

**Current recommended tiers:**
- **Development/Testing:** B1 ($13/month)
- **Production:** S1 ($70/month) - Better performance
- **High traffic:** P1V2 ($146/month) - Premium

**To check:**
1. Go to your Web App
2. Click **"Scale up (App Service plan)"** in left menu
3. Verify you're on B1 or higher

---

### 5. HTTPS Only (Security)

**Location:** Azure Portal → Your Web App → **TLS/SSL settings**

**Set:**
- **HTTPS Only:** ON ✅

This redirects all HTTP traffic to HTTPS.

---

### 6. Always On (Recommended)

**Location:** Azure Portal → Your Web App → **Configuration** → **General settings**

**Set:**
- **Always On:** ON ✅

**Why:**
- Prevents app from sleeping after 20 minutes of inactivity
- Faster response times
- Better user experience

**Note:** Not available on F1 (Free) tier

---

### 7. Health Check (Optional but Recommended)

**Location:** Azure Portal → Your Web App → **Health check**

**Set:**
- **Enable health check:** ON
- **Path:** `/healthz` (Streamlit's default health endpoint)

**Why:**
- Azure monitors your app
- Auto-restarts if app crashes
- Better reliability

---

### 8. Application Insights (Monitoring)

**Location:** Azure Portal → Your Web App → **Application Insights**

**Setup:**
1. Click **"Turn on Application Insights"**
2. Create new resource or use existing
3. Click **"Apply"**

**Benefits:**
- Monitor performance
- Track errors
- See usage analytics
- Debug issues in production

**After enabling:**
- Go to Application Insights → **Live Metrics** to see real-time data
- Go to **Failures** to see errors
- Go to **Performance** to see response times

---

### 9. Deployment Settings

**Location:** Azure Portal → Your Web App → **Deployment Center**

**Verify:**
- **Source:** GitHub
- **Repository:** Your repo
- **Branch:** main
- **Workflow file:** `.github/workflows/main_document-rag-application.yml`

**Check GitHub Actions:**
1. Go to your GitHub repository
2. Click **"Actions"** tab
3. Verify latest workflow run succeeded

---

### 10. CORS Settings (If Needed)

**Location:** Azure Portal → Your Web App → **CORS**

**For Streamlit, you usually don't need to change CORS.**

But if you get CORS errors:
- **Allowed Origins:** Add your domain or `*` (not recommended for production)

---

## 🚀 Deployment Steps

### Step 1: Verify Local Changes Committed
```bash
git status
git add .
git commit -m "Added Pinecone integration and UI improvements"
git push origin main
```

### Step 2: Trigger Deployment

**Option A: Automatic (GitHub Actions)**
- Push to main branch
- GitHub Actions automatically deploys
- Check: GitHub → Actions tab

**Option B: Manual Deploy**
```bash
# Login to Azure
az login

# Deploy
az webapp up --name document-rag-application --resource-group document-rag-rg
```

### Step 3: Monitor Deployment

1. Go to GitHub → **Actions** tab
2. Click on the latest workflow run
3. Watch the deployment progress
4. Wait for ✅ green checkmark

**Typical deployment time:** 5-10 minutes

---

## 🔍 Post-Deployment Verification

### 1. Check App is Running

**Visit:** `https://document-rag-application.azurewebsites.net`

**Expected:**
- ✅ Page loads (may take 10-20 seconds on first load)
- ✅ You see "📚 Document RAG Application" header
- ✅ Sidebar shows upload options

### 2. Check Logs

**Location:** Azure Portal → Your Web App → **Log stream**

**Expected output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://0.0.0.0:8000
```

**If you see errors:**
- Check environment variables are set correctly
- Check startup command is correct
- Check Python version is 3.12

### 3. Test Upload

1. Upload a PDF or text file
2. Check logs for processing messages
3. Verify "Document loaded successfully" appears

### 4. Test RAG Query

1. Toggle "📚 Use RAG" ON
2. Ask a question about your document
3. Verify you get a response with "*(RAG Response)*" prefix

### 5. Check Pinecone

```bash
# From your local machine
python -c "
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('document-rag-vectors')
stats = index.describe_index_stats()

print(f'Total vectors: {stats[\"total_vector_count\"]}')
print(f'Namespaces: {list(stats[\"namespaces\"].keys())}')
"
```

You should see vectors from your production app.

---

## ⚠️ Common Issues & Solutions

### Issue 1: App Won't Start

**Symptoms:**
- "Application Error" page
- 503 errors

**Solutions:**
1. Check **Log stream** for errors
2. Verify **Startup Command** is correct
3. Check **Python version** is 3.12
4. Verify **environment variables** are set
5. Check **App Service Plan** is not F1 (Free)

### Issue 2: Environment Variables Not Loading

**Symptoms:**
- "PINECONE_API_KEY not found" errors
- "AZ_OPENAI_API_KEY not found" errors

**Solutions:**
1. Go to Configuration → Application settings
2. Verify all variables exist
3. Click **"Save"** at the top
4. Click **"Restart"** your app
5. Wait 1-2 minutes for restart

### Issue 3: Slow Performance

**Symptoms:**
- App takes > 5 seconds to respond
- Uploads timeout

**Solutions:**
1. Upgrade to **B2** or **S1** tier
2. Enable **"Always On"**
3. Enable **Application Insights** to identify bottlenecks

### Issue 4: App Sleeps/Stops

**Symptoms:**
- First load after inactivity is very slow
- App seems offline

**Solutions:**
1. Enable **"Always On"** in Configuration
2. Upgrade from F1 to B1 tier (F1 doesn't support Always On)

### Issue 5: File Upload Fails

**Symptoms:**
- "Maximum upload size exceeded"
- Upload hangs

**Solutions:**
1. Check file size < 200MB
2. Increase timeout in Streamlit config (add `.streamlit/config.toml`):
```toml
[server]
maxUploadSize = 200

[browser]
serverAddress = "0.0.0.0"
serverPort = 8000
```

### Issue 6: Pinecone Connection Fails

**Symptoms:**
- "Connection timeout"
- "API key invalid"

**Solutions:**
1. Verify `PINECONE_API_KEY` is correct
2. Check Pinecone index exists: `document-rag-vectors`
3. Verify Azure can reach Pinecone (check firewall)
4. Test from Azure Cloud Shell:
```bash
curl https://api.pinecone.io/
```

---

## 🔐 Security Best Practices

### 1. Use Azure Key Vault (Recommended)

Instead of storing secrets in environment variables:

**Setup:**
1. Create Azure Key Vault
2. Store secrets there
3. Use Managed Identity to access
4. Reference secrets with: `@Microsoft.KeyVault(SecretUri=https://...)`

See `AZURE_DEPLOYMENT_GUIDE.md` for detailed steps.

### 2. Enable Authentication (Optional)

**For internal use:**
1. Go to **Authentication** in Azure Portal
2. Add Identity Provider (Azure AD)
3. Restrict access to your organization

### 3. Custom Domain (Optional)

Instead of `*.azurewebsites.net`:
1. Buy a domain
2. Go to **Custom domains** in Azure Portal
3. Add your domain
4. Configure DNS
5. Enable SSL certificate

---

## 📊 Monitoring & Maintenance

### Daily Checks
- [ ] App is accessible
- [ ] No errors in Application Insights
- [ ] Pinecone usage within limits

### Weekly Checks
- [ ] Review Application Insights for performance
- [ ] Check Azure costs
- [ ] Review logs for errors

### Monthly Checks
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Review and cleanup old Pinecone namespaces (if needed)
- [ ] Check for security updates

---

## 💰 Cost Management

### Current Setup Estimated Costs:

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Azure Web App (B1) | Basic | $13 |
| Application Insights | Basic | $0-5 |
| Pinecone | Free/Serverless | $0-10 |
| Azure OpenAI | Pay-per-use | Variable |
| **Total** | | **$15-30** |

### To Reduce Costs:
1. Use F1 (Free) tier for development (upgrade to B1 for production)
2. Disable Application Insights if not needed
3. Monitor Azure OpenAI usage
4. Set spending limits in Azure

### To Monitor Costs:
1. Go to Azure Portal → **Cost Management + Billing**
2. Set up **Budget alerts**
3. Review **Cost analysis** monthly

---

## 🎯 Production Readiness Checklist

Before going live:

### Security ✅
- [ ] HTTPS Only enabled
- [ ] Environment variables set (not hardcoded)
- [ ] Consider Azure Key Vault for secrets
- [ ] Add authentication if needed

### Performance ✅
- [ ] App Service Plan: B1 or higher
- [ ] Always On enabled
- [ ] Application Insights configured

### Reliability ✅
- [ ] Health check enabled
- [ ] Deployment successful
- [ ] App tested end-to-end
- [ ] Error handling works

### Monitoring ✅
- [ ] Application Insights enabled
- [ ] Budget alerts set
- [ ] Log streaming tested

### Backup/Recovery ✅
- [ ] Code in Git (✅ Already done)
- [ ] Environment variables documented
- [ ] Deployment process documented

---

## 🚀 You're Ready!

Your app should now be running on Azure!

**Your Production URL:**
`https://document-rag-application.azurewebsites.net`

**Quick Test:**
1. Visit the URL
2. Upload a document
3. Ask a question
4. Verify RAG works

If everything works → **You're live! 🎉**

If issues → Check the **Common Issues** section above or review logs.

---

## 📞 Need Help?

1. **Check Logs First:** Azure Portal → Log stream
2. **Application Insights:** Look for errors and performance issues
3. **Pinecone Dashboard:** Verify vectors are being created
4. **GitHub Actions:** Check if deployment succeeded

**Most issues are:**
- Missing/incorrect environment variables (90%)
- Wrong startup command (5%)
- Insufficient app service tier (3%)
- Other (2%)
