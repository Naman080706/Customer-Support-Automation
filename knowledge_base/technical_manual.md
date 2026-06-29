# ABC Technologies — Technical Manual

## 1. Installation
### Desktop App (Windows / macOS)
1. Download the installer from **https://app.abctech.com/download**.
2. Run the installer and follow the prompts.
3. On first launch, sign in with your ABC Technologies account.
- **Minimum requirements:** 4 GB RAM, 2 GB free disk space, Windows 10+ or macOS 11+.

### Web App
- No installation required. Use a modern browser (Chrome, Edge, Firefox, Safari) at **https://app.abctech.com**.

## 2. Login Problems
- **Forgot password:** click "Forgot password" on the login screen to receive a reset link by email.
- **Account locked:** after 5 failed attempts the account locks for 15 minutes.
- **Two-factor (2FA) issues:** ensure your device clock is synced; use a backup code if you lost your device.
- **"Invalid credentials":** confirm Caps Lock is off and that you are using the correct workspace URL.

## 3. Common Application Errors
### Application crashes when uploading a file
- **Cause:** uploading files larger than the 50 MB limit, or an unsupported file type, can crash older app versions.
- **Fix:**
  1. Update to the latest app version (Help → Check for Updates).
  2. Ensure the file is under 50 MB and of a supported type (PDF, PNG, JPG, DOCX, XLSX, CSV).
  3. Clear the local cache: Settings → Advanced → Clear Cache.
  4. If the crash persists, collect logs from Help → Export Diagnostics and contact Technical Support.

### "Sync failed" error
- Check your internet connection and firewall; the app needs outbound HTTPS (port 443) to `*.abctech.com`.
- Sign out and sign back in to force a re-sync.

### Installation fails / "Setup error 0x80070005"
- Run the installer as Administrator.
- Temporarily disable antivirus during installation.
- Ensure you have write permission to the install directory.

## 4. Configuration
- API keys are managed under **Settings → Developer → API Keys**.
- Single Sign-On (SSO/SAML) is configured under **Settings → Security** (Enterprise plan).
- Default data region can be set under **Settings → Organization → Data Residency**.

## 5. Performance Tips
- Keep the app updated; updates include performance and stability fixes.
- For large datasets, enable pagination in **Settings → Display**.
