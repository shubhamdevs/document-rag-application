# Azure Deployment Guide for Document RAG Application

This guide walks you through deploying your Pinecone-based RAG application to Azure Cloud.

## Prerequisites

- Azure subscription
- Azure CLI installed locally
- Pinecone account with index created
- GitHub repository with the application code

---

## Part 1: Azure Key Vault Setup

### Step 1: Create Azure Key Vault

1. Log in to Azure Portal: https://portal.azure.com
2. Click **"Create a resource"** → Search for **"Key Vault"**
3. Click **"Create"**

**Configuration:**
```
Subscription: Your Azure subscription
Resource Group: Create new → "document-rag-rg"
Key Vault Name: "document-rag-kv" (must be globally unique)
Region: East US 2 (same as your Azure OpenAI)
Pricing Tier: Standard
```

4. Click **"Review + Create"** → **"Create"**

### Step 2: Add Secrets to Key Vault

1. Go to your Key Vault → **"Secrets"** (left sidebar)
2. Click **"+ Generate/Import"**

Add the following secrets one by one:

| Secret Name | Value |
|-------------|-------|
| `OPENAI-API-KEY` | Your OpenAI API key (starts with `sk-proj-...`) |
| `AZ-OPENAI-API-KEY` | Your Azure OpenAI API key |
| `AZ-OPENAI-ENDPOINT` | Your Azure OpenAI endpoint URL |
| `PINECONE-API-KEY` | Your Pinecone API key (starts with `pcsk_...`) |
| `PINECONE-INDEX-NAME` | `document-rag-vectors` |
| `PINECONE-ENVIRONMENT` | `us-east-1` |

**Important:** Use hyphens (`-`) instead of underscores in secret names as Azure converts them.

---

## Part 2: Create Azure Web App

### Step 1: Create App Service

1. In Azure Portal, click **"Create a resource"** → **"Web App"**
2. Configure the web app:

```
Subscription: Your Azure subscription
Resource Group: document-rag-rg (use existing)
Name: document-rag-application (must be globally unique)
Publish: Code
Runtime stack: Python 3.12
Operating System: Linux
Region: East US 2
```

3. **App Service Plan:**
   - Click "Create new"
   - Name: `document-rag-plan`
   - Pricing tier: **B1 (Basic)** or higher (F1 Free tier may have memory issues)

4. Click **"Review + Create"** → **"Create"**

### Step 2: Configure Web App Settings

1. Go to your Web App → **"Configuration"** (left sidebar under Settings)
2. Click **"+ New application setting"** and add:

| Name | Value |
|------|-------|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | `7` |

3. Click **"Save"** at the top

---

## Part 3: Enable Key Vault Integration

### Step 1: Enable Managed Identity

1. Go to your Web App → **"Identity"** (left sidebar)
2. Under **"System assigned"** tab:
   - Toggle **"Status"** to **"On"**
   - Click **"Save"**
   - Click **"Yes"** to confirm

3. Copy the **Object (principal) ID** (you'll need this next)

### Step 2: Grant Web App Access to Key Vault

1. Go to your Key Vault → **"Access policies"** (left sidebar)
2. Click **"+ Create"**
3. **Permissions:**
   - Secret permissions: Check **"Get"** and **"List"**
   - Click **"Next"**

4. **Principal:**
   - Search for your Web App name: `document-rag-application`
   - Select it
   - Click **"Next"** → **"Next"** → **"Create"**

### Step 3: Reference Secrets in Web App Configuration

1. Go back to Web App → **"Configuration"**
2. Click **"+ New application setting"** for each secret:

```
Format: @Microsoft.KeyVault(SecretUri=https://<key-vault-name>.vault.azure.net/secrets/<secret-name>/)
```

Add these application settings:

| Name | Value |
|------|-------|
| `OPENAI_API_KEY` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/OPENAI-API-KEY/)` |
| `AZ_OPENAI_API_KEY` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/AZ-OPENAI-API-KEY/)` |
| `AZ_OPENAI_ENDPOINT` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/AZ-OPENAI-ENDPOINT/)` |
| `PINECONE_API_KEY` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/PINECONE-API-KEY/)` |
| `PINECONE_INDEX_NAME` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/PINECONE-INDEX-NAME/)` |
| `PINECONE_ENVIRONMENT` | `@Microsoft.KeyVault(SecretUri=https://document-rag-kv.vault.azure.net/secrets/PINECONE-ENVIRONMENT/)` |

**Replace `document-rag-kv` with your actual Key Vault name if different.**

3. Click **"Save"** → **"Continue"**

---

## Part 4: GitHub Actions Deployment

### Step 1: Get Publish Profile

1. Go to your Web App → **"Overview"**
2. Click **"Get publish profile"** (top toolbar)
3. Save the downloaded `.PublishSettings` file
4. Open it in a text editor and copy the entire contents

### Step 2: Add GitHub Secret

1. Go to your GitHub repository
2. Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Value: Paste the publish profile contents
6. Click **"Add secret"**

### Step 3: Update GitHub Actions Workflow

The workflow file `.github/workflows/main_document-rag-application.yml` needs to be updated:

```yaml
name: Build and deploy Python app to Azure Web App

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python version
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Create and start virtual environment
        run: |
          python -m venv venv
          source venv/bin/activate

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Zip artifact for deployment
        run: zip release.zip ./* -r

      - name: Upload artifact for deployment jobs
        uses: actions/upload-artifact@v4
        with:
          name: python-app
          path: |
            release.zip
            !venv/

  deploy:
    permissions:
      contents: none
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: 'Production'
      url: ${{ steps.deploy-to-webapp.outputs.webapp-url }}

    steps:
      - name: Download artifact from build job
        uses: actions/download-artifact@v4
        with:
          name: python-app

      - name: Unzip artifact for deployment
        run: unzip release.zip

      - name: 'Deploy to Azure Web App'
        uses: azure/webapps-deploy@v3
        id: deploy-to-webapp
        with:
          app-name: 'document-rag-application'
          slot-name: 'Production'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

### Step 4: Add Startup Command

Streamlit apps require a custom startup command:

1. Go to Web App → **"Configuration"** → **"General settings"**
2. **Startup Command:**
```bash
python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0
```
3. Click **"Save"**

---

## Part 5: Deploy Application

### Method 1: Via GitHub Actions (Recommended)

1. Commit and push your changes to the `main` branch:
```bash
git add .
git commit -m "Migrate to Pinecone vector database"
git push origin main
```

2. Go to GitHub repository → **"Actions"** tab
3. Watch the deployment progress
4. Once completed, your app will be live!

### Method 2: Manual Deployment via Azure CLI

```bash
# Login to Azure
az login

# Deploy from local directory
az webapp up --name document-rag-application --resource-group document-rag-rg --runtime "PYTHON:3.12"
```

---

## Part 6: Verify Deployment

### Check Application Logs

1. Go to Web App → **"Log stream"** (left sidebar under Monitoring)
2. Wait for logs to appear
3. Look for:
   - `Starting Streamlit...`
   - `You can now view your Streamlit app in your browser.`
   - No error messages

### Access Your Application

Your app URL: `https://document-rag-application.azurewebsites.net`

---

## Part 7: Configure Pinecone for Production

### Important: Update Session Cleanup Logic

Since Pinecone Free tier has limitations, ensure your cleanup function works properly:

1. Monitor namespace usage in Pinecone console
2. Consider implementing a scheduled cleanup job for old sessions
3. For production, upgrade to Pinecone paid tier for unlimited namespaces

---

## Troubleshooting

### Issue: App not starting

**Solution:**
1. Check Web App logs: **"Log stream"**
2. Verify all environment variables are set correctly
3. Check Key Vault access policy is configured
4. Ensure Managed Identity is enabled

### Issue: Key Vault secrets not loading

**Solution:**
1. Verify application settings use correct format:
   ```
   @Microsoft.KeyVault(SecretUri=https://KEY-VAULT-NAME.vault.azure.net/secrets/SECRET-NAME/)
   ```
2. Check Key Vault access policy includes Web App's Managed Identity
3. Ensure secret names in Key Vault match (use hyphens, not underscores)

### Issue: Pinecone connection fails

**Solution:**
1. Verify `PINECONE_API_KEY` is correctly stored in Key Vault
2. Check Pinecone index exists: `document-rag-vectors`
3. Ensure index region matches your configuration
4. Test connection from Azure Cloud Shell:
```python
from pinecone import Pinecone
pc = Pinecone(api_key="YOUR_API_KEY")
print(pc.list_indexes())
```

### Issue: Out of memory errors

**Solution:**
1. Upgrade App Service Plan to B2 or S1
2. Go to Web App → **"Scale up (App Service plan)"**
3. Select a plan with more memory

### Issue: Slow performance

**Solution:**
1. Enable Application Insights for monitoring
2. Consider using Azure CDN for static assets
3. Optimize Pinecone queries with proper indexing
4. Cache frequently accessed data

---

## Security Best Practices

1. **Never commit secrets to GitHub**
   - Add `.env` to `.gitignore`
   - Use Key Vault for all sensitive data

2. **Enable HTTPS only**
   - Go to Web App → **"TLS/SSL settings"**
   - Set **"HTTPS Only"** to **"On"**

3. **Restrict Key Vault access**
   - Use **"Least privilege"** principle
   - Only grant "Get" and "List" permissions
   - Enable Key Vault firewall if needed

4. **Monitor application**
   - Enable Application Insights
   - Set up alerts for failures
   - Review logs regularly

5. **Use deployment slots**
   - Create a staging slot for testing
   - Swap to production after verification

---

## Cost Estimation

### Monthly costs (USD):

- **App Service (B1):** ~$13/month
- **Key Vault:** ~$0.03/10,000 operations (minimal)
- **Azure OpenAI:** Pay-per-use (depends on usage)
- **Pinecone Free:** $0 (limited features)
- **Pinecone Serverless:** ~$0.10/million queries

**Total estimated:** $15-30/month (excluding OpenAI usage)

---

## Next Steps

1. Set up custom domain (optional)
2. Configure Application Insights for monitoring
3. Implement authentication (Azure AD B2C)
4. Set up CI/CD pipeline with staging environment
5. Configure auto-scaling rules
6. Implement rate limiting

---

## Support

- Azure Documentation: https://docs.microsoft.com/azure
- Pinecone Documentation: https://docs.pinecone.io
- Streamlit on Azure: https://docs.streamlit.io/deploy/streamlit-community-cloud

---

**Deployment Complete!** 🎉

Your Document RAG application is now running on Azure Cloud with:
- ✅ Pinecone vector database
- ✅ Azure OpenAI integration
- ✅ Secure Key Vault storage
- ✅ Auto-deployment via GitHub Actions
