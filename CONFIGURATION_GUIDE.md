# MAIAChat Desktop - Configuration Guide

Created by Aleksander Celewicz  
Website: [MAIAChat.com](https://maiachat.com)

This guide will help you configure MAIAChat Desktop for first-time use.

## 🚀 Quick Start Configuration

### Step 1: Copy Configuration Templates

Copy the example configuration files to create your personal configuration:

```bash
# Main configuration
cp config.json.example config.json

# API key definitions
cp api_keys.json.example api_keys.json

# MCP server configuration
cp mcp_config/servers.json.example mcp_config/servers.json

# Folder permissions (if using file operations)
cp mcp_config/folder_permissions.json.example mcp_config/folder_permissions.json

# Quick dashboard (optional)
cp quickdash_config.json.example quickdash_config.json
```

### Step 2: Configure API Keys

Edit `config.json` and add your API keys. You only need the keys for services you plan to use:

```json
{
    "OPENAI_API_KEY": "sk-your-openai-key-here",
    "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key-here",
    "GEMINI_API_KEY": "your-gemini-key-here",
    "GROQ_API_KEY": "gsk_your-groq-key-here",
    "OPENROUTER_API_KEY": "sk-or-your-openrouter-key-here"
}
```

## 🔑 Getting API Keys

### AI Providers

| Provider | URL | Free Tier | Notes |
|----------|-----|-----------|-------|
| **OpenAI** | [platform.openai.com](https://platform.openai.com/api-keys) | $5 credit | GPT-4, GPT-3.5-turbo |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com/) | $5 credit | Claude models |
| **Google Gemini** | [makersuite.google.com](https://makersuite.google.com/app/apikey) | Free tier | Gemini Pro, Flash |
| **Groq** | [console.groq.com](https://console.groq.com/keys) | Free tier | Fast inference |
| **OpenRouter** | [openrouter.ai](https://openrouter.ai/keys) | Free tier | Access to multiple models |
| **xAI Grok** | [console.x.ai](https://console.x.ai/) | Paid | Grok models |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com/api_keys) | Free tier | DeepSeek models |

### Search Providers (Optional)

| Provider | URL | Free Tier | Notes |
|----------|-----|-----------|-------|
| **Google Search** | [console.developers.google.com](https://console.developers.google.com/) | 100 queries/day | Requires Search Engine ID |
| **Serper** | [serper.dev](https://serper.dev/) | 2,500 queries free | Easy setup |
| **Brave Search** | [api.search.brave.com](https://api.search.brave.com/) | 2,000 queries/month | Privacy-focused |

## 🛠️ Advanced Configuration

### MCP Server Configuration

Edit `mcp_config/servers.json` to configure external services:

```json
[
  {
    "name": "Local Files",
    "url": "filesystem://local",
    "description": "Access local files",
    "enabled": true,
    "capabilities": ["read_file", "write_file", "list_directory"]
  }
]
```

### Folder Permissions

Edit `mcp_config/folder_permissions.json` to control file access:

```json
{
  "/path/to/your/project": {
    "read_file": true,
    "write_file": true,
    "create_directory": true,
    "list_directory": true
  }
}
```

### RAG (Knowledge Base) Settings

Configure RAG settings in `config.json`:

```json
{
    "RAG_DISABLED": false,
    "RAG_N_RESULTS": 30,
    "RAG_TOKEN_LIMIT": 8000,
    "RAG_RERANKING": true,
    "EMBEDDING_DEVICE": "auto"
}
```

## 🔒 Security Best Practices

1. **Never commit API keys** - They're excluded by `.gitignore`
2. **Use environment variables** - Alternative to config files
3. **Rotate keys regularly** - Replace keys periodically
4. **Monitor usage** - Check API usage dashboards
5. **Limit permissions** - Only grant necessary file access

## 🚨 Troubleshooting

### Common Issues

**"API key not found" errors:**
- Verify your API key is correctly set in `config.json`
- Check for extra spaces or quotes around the key
- Ensure the key has the correct permissions

**File access denied:**
- Check `mcp_config/folder_permissions.json`
- Verify folder paths exist and are accessible
- On Windows, use forward slashes: `C:/Users/...`

**Models not loading:**
- Verify your API keys are valid and active
- Check your internet connection
- Some models require payment setup even with free tiers

### Getting Help

- **Documentation**: Check the README.md file
- **Issues**: Report bugs on GitHub
- **Community**: Join discussions on GitHub
- **Contact**: Visit [MAIAChat.com](https://maiachat.com) for support

## 🎯 Next Steps

1. **Start the application**: Run `python start_app.py`
2. **Load a profile**: Try the example profiles first
3. **Test API connections**: Send a simple message
4. **Add knowledge**: Upload documents to the knowledge base
5. **Customize agents**: Create your own agent configurations

---

**Created by Aleksander Celewicz**  
**Website**: [MAIAChat.com](https://maiachat.com)  
**License**: MIT (see LICENSE file)
