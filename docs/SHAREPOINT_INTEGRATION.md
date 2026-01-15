# SharePoint Integration Options

This document outlines options for integrating Microsoft SharePoint/OneDrive with the Registry Review application, based on Regen Network's use of Office 365 for document storage.

## Current State

The application currently supports:
- **Manual file upload** - Users can upload PDFs and other files directly through the browser
- **Google Drive import** - Integration with Google Drive for importing project documents

## SharePoint Integration Approaches

### Option 1: Microsoft Graph API (Recommended)

Use the Microsoft Graph API to access SharePoint/OneDrive files directly.

**Pros:**
- Native Microsoft integration
- Supports both SharePoint sites and OneDrive personal storage
- Fine-grained permissions control
- Real-time file access without duplication

**Cons:**
- Requires Azure AD app registration
- More complex OAuth flow than Google
- Requires admin consent for organization-wide access

**Implementation:**
```python
# Example Microsoft Graph API usage
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    client_credential="YOUR_CLIENT_SECRET",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

# Get access token
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

# List files in SharePoint site
response = requests.get(
    "https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root/children",
    headers={"Authorization": f"Bearer {result['access_token']}"}
)
```

### Option 2: SharePoint REST API

Direct SharePoint REST API access for SharePoint-specific operations.

**Pros:**
- More SharePoint-specific features
- Can access lists, metadata, custom columns

**Cons:**
- Limited to SharePoint only (not OneDrive)
- Older API, less well-documented

### Option 3: Manual Download + Upload

Users download files from SharePoint and upload via the existing manual upload feature.

**Pros:**
- No additional integration needed
- Works immediately
- Simple workflow

**Cons:**
- Manual process for each project
- Files not automatically synced
- Potential for version mismatches

## Recommended Implementation Path

### Phase 1: Immediate (Current State)
Users can use the manual upload feature to upload files downloaded from SharePoint. This requires no additional development and works today.

### Phase 2: Browser Extension (Optional)
A simple browser bookmarklet or extension that can grab files from SharePoint and send them to the Registry Review app.

### Phase 3: Full Integration
Implement Microsoft Graph API integration with:
1. Azure AD app registration
2. OAuth flow for user authentication
3. SharePoint site browser in the UI
4. Automatic file import from specified folders

## Configuration Requirements

For full SharePoint integration, the following would be needed:

```env
# Azure AD Application
AZURE_CLIENT_ID=your-azure-app-id
AZURE_CLIENT_SECRET=your-azure-app-secret
AZURE_TENANT_ID=your-tenant-id

# SharePoint Site
SHAREPOINT_SITE_ID=regen-network.sharepoint.com,site-guid
SHAREPOINT_PROJECTS_FOLDER=/Projects/Registry Reviews
```

## File Naming Convention

Based on team feedback, the following naming convention is used:

```
{ProjectID}_{ProjectName}_{DocumentType}_{Year}.pdf

Examples:
- 4997Botany22_Public_Project_Plan.pdf
- 4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf
- 4998Botany23_GHG_Emissions_30_Sep_2023.pdf
```

The application should:
1. Parse the ProjectID from filenames to auto-group documents
2. Detect document type from filename patterns
3. Associate with the correct monitoring period

## Next Steps

1. **Confirm SharePoint site structure** with the Regen team
2. **Get Azure AD admin consent** for app registration
3. **Implement Microsoft Graph API** client in the backend
4. **Add SharePoint browser** dialog similar to Google Drive import

## References

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [SharePoint REST API](https://docs.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints)
- [MSAL Python Library](https://github.com/AzureAD/microsoft-authentication-library-for-python)
