# MAIAChat Desktop - Setup Guide

**Created by Aleksander Celewicz**

This guide will help you set up MAIAChat Desktop for development or personal use.

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)
- At least 4GB of RAM (8GB recommended for RAG features)
- Internet connection for downloading dependencies and AI model access

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/maiachat-desktop.git
cd maiachat-desktop
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

**📖 For detailed configuration instructions, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)**

#### Quick Setup:

1. Copy the configuration templates:
   ```bash
   cp config.json.example config.json
   cp api_keys.json.example api_keys.json
   cp mcp_config/servers.json.example mcp_config/servers.json
   cp mcp_config/folder_permissions.json.example mcp_config/folder_permissions.json
   ```

2. Add your API keys to `config.json`:
   ```json
   {
     "OPENAI_API_KEY": "sk-your-openai-key-here",
     "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key-here",
     "GEMINI_API_KEY": "your-gemini-key-here"
   }
   ```

**Alternative: Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

**📋 See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for:**
- Complete API key setup instructions
- Links to get API keys from each provider
- Advanced configuration options
- Troubleshooting guide

### 5. Configure MCP Servers (Optional)

Edit `mcp_config/servers.json` to configure external services:

- **Brave Search**: Add your Brave Search API key for web search functionality
- **GitHub**: Add your GitHub Personal Access Token for repository access
- **Local Files**: Update file paths to match your system

### 6. Set Up Folder Permissions (Optional)

Edit `mcp_config/folder_permissions.json` to configure which directories the application can access for file operations.

## Getting API Keys

### Required for Basic Functionality

- **OpenAI**: https://platform.openai.com/account/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys

### Optional for Extended Features

- **Google Gemini**: https://ai.google.dev/
- **Groq**: https://console.groq.com/keys
- **Grok (xAI)**: https://grok.x.ai/
- **DeepSeek**: https://platform.deepseek.com/
- **OpenRouter**: https://openrouter.ai/keys
- **Brave Search**: https://api.search.brave.com/app/keys

## Running the Application

### Development Mode

```bash
python main.py
```

### Building Executable

For creating a standalone executable:

```bash
python build_exe.py
```

The executable will be created in the `dist/MAIAChat/` directory.

## First Run Setup

1. **Launch the application**
2. **Go to Settings tab** to configure your preferences
3. **Test API connections** by sending a simple message
4. **Configure RAG** (optional) by adding documents to the knowledge base
5. **Set up profiles** for different use cases

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all required API keys are properly configured
2. **Import Errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
3. **Permission Errors**: Check folder permissions in `mcp_config/folder_permissions.json`
4. **Memory Issues**: Reduce RAG settings or disable RAG if you have limited RAM

### Getting Help

- Check the main README.md for detailed feature documentation
- Review the logs in the application's terminal output
- Ensure your API keys have sufficient credits/quota

## Security Notes

- Never commit your actual API keys to version control
- Keep your `config.json` and `.env` files secure
- The application supports secure key storage using your OS keychain
- All sensitive files are excluded from git by default

## License

This project is licensed under the MIT License with commercial attribution requirements.

- **FREE** for personal, educational, and non-commercial use
- **Commercial use** requires attribution: "Powered by MAIAChat.com Desktop by Aleksander Celewicz"
- For commercial licensing without attribution, contact Aleksander Celewicz

---

**Created by Aleksander Celewicz** | Visit [MAIAChat.com](https://maiachat.com) for more information
