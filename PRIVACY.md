# 🔒 Privacy Policy for MAIAChat Desktop

**Created by Aleksander Celewicz**  
**Effective Date**: January 27, 2025  
**Last Updated**: January 27, 2025

## 🌟 Privacy-First Design

MAIAChat Desktop is built with privacy as a fundamental principle. This document explains how your data is handled, what information is processed, and your rights regarding your data.

## 📋 Quick Privacy Summary

- ✅ **100% Local Processing**: All your data stays on your device
- ✅ **No Data Collection**: We don't collect, store, or transmit your personal data
- ✅ **No Tracking**: Zero analytics, telemetry, or usage monitoring
- ✅ **No Accounts**: No registration, login, or user profiles required
- ✅ **Open Source**: Full transparency with auditable code

## 🏠 What Data Stays Local

### Your Conversations
- **Storage**: All conversations saved locally in `conversation_history/`
- **Access**: Only you have access to your conversation files
- **Retention**: You control how long conversations are kept
- **Deletion**: You can delete conversations at any time

### Knowledge Base Documents
- **Processing**: Documents processed locally using FAISS
- **Storage**: Embeddings and indexes stored in `knowledge_base/`
- **Privacy**: Documents never transmitted to external servers
- **Control**: You can add, remove, or clear documents anytime

### Configuration & Settings
- **Location**: Stored in `config.json` and related files
- **Content**: API keys, preferences, agent configurations
- **Security**: Protected by file system permissions
- **Portability**: Easy to backup, transfer, or delete

### Application Data
- **Logs**: Debug information stored locally for troubleshooting
- **Cache**: Temporary files for performance optimization
- **Preferences**: UI settings and user customizations

## 🌐 External Data Transmission

### AI Provider Communication

When you use MAIAChat, the following data is sent to your chosen AI providers:

**What is Sent**:
- Your message content (necessary for AI responses)
- System prompts and agent instructions
- Conversation context (for coherent responses)

**What is NOT Sent**:
- Your API keys (used for authentication only)
- Other conversations or personal files
- Your identity or personal information
- Usage analytics or metadata

**Provider Privacy Policies**:
- [OpenAI Privacy Policy](https://openai.com/privacy/)
- [Anthropic Privacy Policy](https://www.anthropic.com/privacy)
- [Google AI Privacy Policy](https://policies.google.com/privacy)

### Search Integration (Optional)

If you enable internet search features:
- Search queries sent to configured search providers
- Results retrieved and processed locally
- No personal information included in search requests

### No Other External Communication

MAIAChat does NOT communicate with:
- Analytics services
- Crash reporting services
- Update servers
- Telemetry endpoints
- Social media platforms
- Advertising networks

## 🔐 Data Protection Measures

### Local Security
- **File Encryption**: Sensitive data protected by OS-level security
- **Access Control**: Only MAIAChat process can access its data
- **Memory Protection**: Data cleared from memory on exit
- **No Persistence**: API keys not stored in plain text logs

### Network Security
- **Minimal Connections**: Only necessary API calls made
- **Encrypted Transport**: All external communication uses HTTPS/TLS
- **No Tracking**: No cookies, fingerprinting, or session tracking
- **Direct Communication**: No proxy servers or intermediaries

## 👤 Your Privacy Rights

### Data Access
- **Full Access**: You have complete access to all your data
- **File Locations**: All data stored in clearly labeled directories
- **Export**: Easy to backup or transfer your data
- **Transparency**: Open source code allows full inspection

### Data Control
- **Modification**: Change or update any stored information
- **Deletion**: Remove conversations, documents, or all data
- **Portability**: Move your data to other systems
- **Retention**: Decide how long to keep information

### Privacy Settings
- **Provider Choice**: Select which AI providers to use
- **Feature Control**: Enable/disable search, RAG, or other features
- **Local Processing**: All privacy-sensitive operations done locally
- **Offline Mode**: Use local models for complete privacy

## 🚫 What We Don't Do

### No Data Collection
- We don't collect usage statistics
- We don't track feature usage
- We don't monitor conversations
- We don't store user profiles

### No Sharing
- We don't share data with third parties
- We don't sell user information
- We don't provide data to advertisers
- We don't participate in data broking

### No Tracking
- We don't use cookies or tracking pixels
- We don't fingerprint devices
- We don't track across sessions
- We don't build user profiles

## 🔍 Third-Party Services

### AI Providers
When you configure API keys for AI providers, you establish a direct relationship with them:
- **Your Choice**: You decide which providers to use
- **Direct Communication**: Your device communicates directly with providers
- **Their Policies**: Each provider has their own privacy policy
- **Your Control**: You can change or remove providers anytime

### Local Models (Ollama)
- **Completely Local**: No external communication required
- **Maximum Privacy**: All processing on your device
- **No API Keys**: No external accounts needed
- **Full Control**: You manage the models and data

## 📱 Children's Privacy

MAIAChat Desktop is not specifically designed for children under 13. However:
- No personal information is collected from any users
- No age verification is required
- Parents have full control over local data
- All privacy protections apply equally to all users

## 🌍 International Privacy

### GDPR Compliance (EU)
- **No Personal Data Processing**: We don't process personal data
- **Local Storage**: All data remains in your jurisdiction
- **Right to Deletion**: You can delete all data anytime
- **Data Portability**: Easy export of your information

### CCPA Compliance (California)
- **No Sale of Data**: We don't sell personal information
- **No Collection**: We don't collect personal information
- **Full Transparency**: Open source code provides complete visibility

### Other Jurisdictions
- Privacy-by-design approach meets most international standards
- Local processing ensures compliance with data residency requirements
- No cross-border data transfers by MAIAChat itself

## 🔄 Privacy Policy Updates

### How We Update This Policy
- **GitHub Repository**: All changes tracked in version control
- **Clear Documentation**: Updates documented in commit messages
- **Community Review**: Open source allows community oversight
- **Backwards Compatibility**: Changes won't reduce existing privacy protections

### Notification of Changes
- **Repository Watching**: Watch the GitHub repository for updates
- **Version Tags**: Major changes tagged with version numbers
- **Documentation**: Changes explained in release notes

## 📞 Privacy Questions

### Getting Help
- **Documentation**: Check SECURITY.md and SETUP.md
- **GitHub Issues**: For general privacy questions
- **Direct Contact**: Aleksander Celewicz for specific concerns

### Reporting Privacy Issues
If you discover a privacy concern:
1. Review this document and the source code
2. Check if it's a configuration issue
3. Contact us through appropriate channels
4. Provide specific details about the concern

## ✅ Privacy Checklist

To maximize your privacy when using MAIAChat:

- [ ] Review which AI providers you really need
- [ ] Understand each provider's privacy policy
- [ ] Consider using local models (Ollama) for sensitive content
- [ ] Regularly review and clean up conversation history
- [ ] Keep your API keys secure and rotate them regularly
- [ ] Monitor network traffic if you have specific concerns
- [ ] Use appropriate system-level security measures

## 🎯 Contact Information

- **Creator**: Aleksander Celewicz
- **Website**: [MAIAChat.com](https://MAIAChat.com)
- **Repository**: GitHub Issues for general questions
- **Privacy Concerns**: Direct contact for sensitive privacy matters

---

**Your privacy is not just a policy for us—it's a core design principle. MAIAChat Desktop is built to keep your data private, secure, and under your complete control.**

*This privacy policy is part of MAIAChat Desktop by Aleksander Celewicz*
