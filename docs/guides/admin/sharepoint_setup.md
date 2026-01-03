# SharePoint App Registration & Setup Guide

To use Arcore SyncBridge with SharePoint, you must register an application in Azure Active Directory (Microsoft Entra ID) and grant it the necessary permissions.

## 1. Register the Application

1. Go to the [Azure Portal](https://portal.azure.com).
2. Navigate to **Microsoft Entra ID** > **App registrations**.
3. Click **New registration**.
4. Enter a name (e.g., `Arcore SyncBridge`).
5. Supported account types: **Accounts in this organizational directory only (Single tenant)**.
6. Click **Register**.

## 2. Generate a Client Secret

1. In your new app registration, go to **Certificates & secrets**.
2. Click **New client secret**.
3. Add a description (e.g., `SyncBridge Backend`) and choose an expiry.
4. Click **Add**.
5. **Copy the Value** immediately. This is your `CLIENT_SECRET`.

## 3. Configure API Permissions

Arcore SyncBridge requires **Application permissions** to run as a background service without a signed-in user.

1. Go to **API permissions**.
2. Click **Add a permission** > **Microsoft Graph** > **Application permissions**.
3. Select the following permissions to ensure full provisioning and sync capabilities:

| Permission | Type | Justification |
| :--- | :--- | :--- |
| **Sites.FullControl.All** | Application | Required for complete site collection management and list provisioning. Prevents 403 errors on strict sites. |
| **Sites.ReadWrite.All** | Application | Core permission for reading and writing list items and documents. |
| **Group.ReadWrite.All** | Application | Allows discovery and writing to Group-connected SharePoint sites (Microsoft 365 Groups). |
| **Files.ReadWrite.All** | Application | Required for handling document libraries and drive items. |
| **User.Read.All** | Application | Used for resolving user principals (Created By / Modified By fields). |

4. Click **Add permissions**.
5. **IMPORTANT:** Click **Grant admin consent for [Your Tenant]** to activate the permissions. Without this step, the app will fail to authenticate.

## 4. Configuration

Update your Arcore SyncBridge connection settings or environment variables with:
- **Tenant ID**: Found on the *Overview* page.
- **Client ID**: Found on the *Overview* page (Application (client) ID).
- **Client Secret**: The value you copied in Step 2.

## Troubleshooting

### Provisioning failed [403] Access denied
If you see an error like `Provisioning failed: Graph POST ... failed [403]`, it means the application lacks the `Sites.ReadWrite.All` permission or **Admin Consent** has not been granted.

1. Check **API permissions** in Azure Portal.
2. Ensure `Sites.ReadWrite.All` is listed with type `Application`.
3. Ensure the **Status** column shows a green checkmark for "Granted for [Tenant]".
