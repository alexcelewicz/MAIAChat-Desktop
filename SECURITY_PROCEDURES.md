# Security Procedures for Contributors

## 🔒 Critical Security Guidelines

This document outlines essential security procedures for contributors to maintain the security and integrity of the MAIAChat project.

## 🚨 Never Commit Sensitive Data

### Prohibited Content
**NEVER commit any of the following to the repository:**

- **API Keys**: OpenAI, Anthropic, Google, Groq, DeepSeek, OpenRouter, etc.
- **Authentication Tokens**: GitHub PATs, Brave Search tokens, etc.
- **Personal File Paths**: Local directory paths, user-specific configurations
- **Credentials**: Passwords, access tokens, session keys
- **Personal Data**: Email addresses, phone numbers, personal information

### Protected Files
The following files are automatically excluded by `.gitignore`:

```
config.json
api_keys.json
.env
mcp_config/servers.json
mcp_config/folder_permissions.json
token_usage_history.json
conversation_history/
knowledge_base/
*.log
```

## ✅ Safe Practices

### 1. Use Template Files
- Always use `.example` template files for configuration
- Replace sensitive values with placeholders like `your_api_key_here`
- Keep actual configurations in local files that are git-ignored

### 2. Before Committing
Run these checks before every commit:

```bash
# Check for accidentally staged sensitive files
git status

# Verify sensitive files are ignored
git check-ignore config.json api_keys.json .env mcp_config/servers.json

# Search for potential API keys in staged changes
git diff --cached | grep -i "api.*key\|token\|secret"
```

### 3. Configuration Setup
When setting up the project:

1. Copy template files:
   ```bash
   cp config.json.example config.json
   cp api_keys.json.example api_keys.json
   cp mcp_config/servers.json.example mcp_config/servers.json
   ```

2. Add your actual API keys to the copied files (NOT the .example files)

3. Verify the files are ignored:
   ```bash
   git status  # Should not show your config files
   ```

## 🔍 Security Review Process

### For Pull Requests
1. **Automated Checks**: All PRs are automatically scanned for sensitive data
2. **Manual Review**: Maintainers review all configuration changes
3. **Template Verification**: Ensure all .example files use safe placeholders

### For Maintainers
1. **Regular Audits**: Periodic security audits of the repository
2. **History Scanning**: Check git history for accidentally committed secrets
3. **Access Control**: Limit repository access and review permissions

## 🚨 If You Accidentally Commit Sensitive Data

### Immediate Actions
1. **DO NOT PANIC** - but act quickly
2. **Contact maintainers** immediately via private channels
3. **Do not push** if the commit is still local

### Remediation Steps
1. **Remove from staging** (if not yet committed):
   ```bash
   git reset HEAD <sensitive-file>
   git checkout -- <sensitive-file>
   ```

2. **Remove from last commit** (if not yet pushed):
   ```bash
   git reset --soft HEAD~1
   # Edit files to remove sensitive data
   git add .
   git commit -m "Fixed commit message"
   ```

3. **If already pushed**: Contact maintainers immediately for history rewriting

## 🛡️ Security Architecture

### Multi-Layer Protection
1. **File-based**: Local configuration files (git-ignored)
2. **Environment**: Environment variables for CI/CD
3. **OS-native**: Keychain/Credential Manager integration
4. **Encryption**: Optional encryption for stored keys

### Secure Development
- Use the secure key manager for production deployments
- Test with dummy/test API keys when possible
- Implement proper error handling that doesn't expose secrets
- Log operations without logging sensitive values

## 📞 Reporting Security Issues

### Contact Information
- **Security Email**: [Create security contact]
- **Private Issues**: Use GitHub security advisories
- **Urgent Issues**: Contact maintainers directly

### What to Report
- Accidentally committed secrets
- Security vulnerabilities in code
- Potential data exposure risks
- Authentication/authorization issues

## 🔄 Regular Security Maintenance

### Monthly Tasks
- [ ] Review .gitignore effectiveness
- [ ] Audit recent commits for sensitive data
- [ ] Update security documentation
- [ ] Review access permissions

### Before Each Release
- [ ] Complete security audit
- [ ] Verify no sensitive data in repository
- [ ] Test security features
- [ ] Update security documentation

## 📚 Additional Resources

- [SECURITY.md](SECURITY.md) - Main security documentation
- [PRIVACY.md](PRIVACY.md) - Privacy policy and data handling
- [API_KEY_SECURITY.md](API_KEY_SECURITY.md) - Detailed API key management
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Safe configuration setup

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for help rather than risk exposing sensitive information.
