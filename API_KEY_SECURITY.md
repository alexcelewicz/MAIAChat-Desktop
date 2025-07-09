# API Key Security Guide

This guide explains how API keys are stored in the application and provides best practices for keeping them secure on both macOS and Windows systems.

## How API Keys Are Stored

When you add API keys through the UI, they are stored in the following ways:

1. **Primary Storage: `config.json`**
   - This file is created in the root directory of the application
   - It stores API keys in plain text JSON format

2. **Alternative Storage: Environment Variables**
   - The application can also read API keys from environment variables
   - A `.env` file in the root directory can be used to set these variables

3. **Secure Storage (Optional Enhancement)**
   - The application now includes a secure key manager that can store API keys in:
     - macOS Keychain on macOS systems
     - Windows Credential Manager on Windows systems
     - Secret Service API on Linux systems

## Security Measures Implemented

The following security measures have been implemented to protect your API keys:

1. **Git Exclusion**
   - Both `config.json` and `.env` are listed in the `.gitignore` file
   - This prevents these files from being committed to the repository

2. **Restrictive File Permissions**
   - File permissions for `config.json` and `.env` are set to 600 (rw-------)
   - This means only your user can read and write these files

3. **Template File**
   - A `.env.example` file is provided as a template
   - This can be committed to git to help other users know which environment variables to set

4. **Pre-commit Hook**
   - A git pre-commit hook checks for accidental inclusion of API keys
   - It also prevents committing sensitive files like `config.json` and `.env`

5. **OS-native Secure Storage**
   - The `secure_key_manager.py` module provides integration with OS-native secure storage
   - This is a more secure alternative to file-based storage

## How to Use These Security Measures

### Basic Security (File-based Storage)

1. **Add API keys through the UI**
   - Go to the Settings tab in the application
   - Enter your API keys in the appropriate fields
   - Click "Save API Keys"

2. **Verify git exclusion**
   ```bash
   git check-ignore config.json .env
   ```
   This should output `config.json` and `.env`, confirming they are ignored by git.

3. **Set restrictive file permissions**
   ```bash
   chmod 600 config.json .env
   ```
   This makes the files readable and writable only by your user.

### Enhanced Security (OS-native Secure Storage)

1. **Import existing keys to secure storage**
   ```bash
   python secure_key_integration.py import
   ```
   This imports API keys from `config.json` and `.env` into your OS keychain.

2. **List keys in secure storage**
   ```bash
   python secure_key_integration.py list
   ```
   This shows which API keys are stored in the secure storage.

3. **Export keys from secure storage**
   ```bash
   python secure_key_integration.py export
   ```
   This exports API keys from secure storage back to `config.json` and `.env`.

4. **Direct command-line usage**
   ```bash
   # Store a key
   python secure_key_manager.py store OPENAI_API_KEY your_api_key_here
   
   # Get a key
   python secure_key_manager.py get OPENAI_API_KEY
   
   # Delete a key
   python secure_key_manager.py delete OPENAI_API_KEY
   
   # List all keys
   python secure_key_manager.py list
   ```

## Platform-Specific Recommendations

### For macOS

1. **Use macOS Keychain**
   - The secure key manager automatically uses macOS Keychain
   - This is more secure than file-based storage

2. **FileVault Encryption**
   - Enable FileVault disk encryption for additional security
   - This protects your API keys even if your device is lost or stolen

### For Windows

1. **Use Windows Credential Manager**
   - The secure key manager automatically uses Windows Credential Manager
   - This is more secure than file-based storage

2. **BitLocker Encryption**
   - Enable BitLocker disk encryption for additional security
   - This protects your API keys even if your device is lost or stolen

## Best Practices

1. **Never commit API keys to git**
   - Always use the `.gitignore` file to exclude sensitive files
   - Use the pre-commit hook to catch accidental inclusion

2. **Regularly rotate your API keys**
   - Periodically generate new API keys and update them in your application
   - This limits the damage if keys are accidentally exposed

3. **Use the most secure storage option available**
   - OS-native secure storage is more secure than file-based storage
   - Use the secure key manager whenever possible

4. **Limit API key permissions**
   - When generating API keys, give them only the permissions they need
   - This limits the damage if keys are compromised

5. **Monitor API key usage**
   - Regularly check your API provider's dashboard for unusual activity
   - Set up alerts for unexpected usage spikes

## Troubleshooting

### Pre-commit Hook Issues

If the pre-commit hook is too restrictive or has false positives:

1. **Bypass the hook for a specific commit**
   ```bash
   git commit --no-verify
   ```
   Use this with caution and only when you're sure no sensitive data is being committed.

2. **Modify the hook**
   Edit `.git/hooks/pre-commit` to adjust the patterns it looks for.

### Secure Storage Issues

If you encounter issues with the secure key manager:

1. **Check if secure storage is available**
   ```bash
   python secure_key_manager.py list
   ```
   If this fails, your system might not support the keyring backend.

2. **Fall back to file-based storage**
   The application will automatically fall back to file-based storage if secure storage is unavailable.

3. **Install additional dependencies**
   On Linux, you might need to install additional packages:
   ```bash
   pip install secretstorage dbus-python
   ```
