# 🤖 MAIAChat Desktop - Multi-Agent AI Assistant

<div align="center">

![MAIAChat Logo](https://img.shields.io/badge/MAIAChat-Desktop-blue?style=for-the-badge&logo=robot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?style=for-the-badge)](https://www.riverbankcomputing.com/software/pyqt/)
[![YouTube](https://img.shields.io/badge/YouTube-AIex%20The%20AI%20Workbench-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@AIexTheAIWorkbench)

**Created by [Aleksander Celewicz](https://MAIAChat.com)**

*A sophisticated multi-agent conversational AI desktop application with advanced RAG capabilities, cross-platform compatibility, and support for 15+ AI providers.*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🎯 Features](#-key-features) • [🛠️ Setup](#-installation--setup) • [💡 Examples](#-usage-examples)

</div>

---

## 🌟 Overview

MAIAChat Desktop is a powerful Python-based desktop application that brings together multiple AI agents in a unified conversational interface. Whether you're a developer, researcher, or AI enthusiast, MAIAChat provides an intuitive platform for complex AI interactions with advanced features like Retrieval-Augmented Generation (RAG), multi-provider support, and intelligent conversation management.

### ✨ What Makes MAIAChat Special?

- **🤝 Multi-Agent Collaboration**: Configure up to 5 AI agents working together on complex tasks
- **🧠 Advanced RAG System**: Integrate your own knowledge base with FAISS vector search
- **🌐 15+ AI Providers**: OpenAI, Anthropic, Google, Ollama, OpenRouter, and more
- **💻 Cross-Platform**: Native support for Windows, macOS, and Linux
- **🎨 Intuitive GUI**: Beautiful PyQt6 interface with real-time streaming responses
- **💰 Cost Tracking**: Built-in token counting and cost estimation
- **🔒 Secure**: Local API key management with no data sent to external servers

## 🚀 Quick Start

Get MAIAChat running in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/maiachat-desktop.git
cd maiachat-desktop

# 2. Install dependencies
python install_dependencies.py

# 3. Set up configuration
cp config.json.example config.json
# Edit config.json with your API keys

# 4. Run the application
python start_app.py
```

> 📋 **First time?** Check out our [detailed setup guide](#-installation--setup) below.

## 🎯 Key Features

### 🤖 Multi-Agent System
- **Collaborative AI**: Configure 1-5 agents with different roles and personalities
- **Agent Profiles**: Pre-built profiles for software development, research, creative writing
- **Individual Control**: Each agent can use different AI providers and models
- **Smart Coordination**: Agents build upon each other's responses for complex tasks

### 🧠 Advanced RAG (Retrieval-Augmented Generation)
- **Knowledge Base Integration**: Upload documents (PDF, TXT, DOCX) to create a searchable knowledge base
- **FAISS Vector Search**: Lightning-fast semantic search through your documents
- **Per-Agent RAG Control**: Enable/disable knowledge base access for individual agents
- **Contextual Retrieval**: Dynamic content retrieval based on conversation context

### 🌐 Extensive AI Provider Support
- **OpenAI**: GPT-4, GPT-3.5, with latest models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku/Opus
- **Google**: Gemini Pro, Gemini Flash
- **Ollama**: Local models (Llama, Mistral, CodeLlama, etc.)
- **OpenRouter**: Access to 100+ models through one API
- **Groq**: Ultra-fast inference
- **DeepSeek**: Advanced reasoning models
- **And more**: Cohere, Together AI, Perplexity, Requesty

### 💻 User Interface & Experience
- **Real-time Streaming**: Watch AI responses appear in real-time
- **Color-coded Agents**: Visual distinction between different agents
- **Conversation History**: Save, load, and manage conversation sessions
- **Token Tracking**: Real-time cost estimation and usage monitoring
- **Responsive Design**: Optimized for different screen sizes and resolutions

### 🔒 Security & Privacy
- **Local Processing**: All conversations and data stay on your machine
- **Secure API Management**: Encrypted storage of API keys
- **No Telemetry**: Zero data collection or external tracking
- **Open Source**: Full transparency with MIT license

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM minimum (8GB+ recommended for RAG features)
- **Storage**: 2GB free space for dependencies and knowledge base

### Method 1: Automated Installation (Recommended)

The easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/your-username/maiachat-desktop.git
cd maiachat-desktop

# Run the automated installer
python install_dependencies.py

# Copy configuration template
cp config.json.example config.json

# Start the application
python start_app.py
```

### Method 2: Manual Installation

For advanced users who prefer manual control:

```bash
# Clone and navigate
git clone https://github.com/your-username/maiachat-desktop.git
cd maiachat-desktop

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration files
cp config.json.example config.json
cp mcp_config/servers.json.example mcp_config/servers.json
cp mcp_config/folder_permissions.json.example mcp_config/folder_permissions.json

# Run the application
python start_app.py
```

### 🔑 API Key Configuration

MAIAChat requires API keys for AI providers. Here's how to set them up:

1. **Edit `config.json`** with your API keys:
```json
{
  "openai_api_key": "sk-your-openai-key-here",
  "anthropic_api_key": "sk-ant-your-anthropic-key-here",
  "google_api_key": "your-google-api-key-here",
  "groq_api_key": "gsk_your-groq-key-here"
}
```

2. **Get API Keys** from these providers:
   - [OpenAI](https://platform.openai.com/api-keys) - For GPT models
   - [Anthropic](https://console.anthropic.com/) - For Claude models
   - [Google AI Studio](https://makersuite.google.com/app/apikey) - For Gemini models
   - [Groq](https://console.groq.com/keys) - For fast inference
   - [OpenRouter](https://openrouter.ai/keys) - For access to 100+ models

3. **Optional: Set up search capabilities** by editing `mcp_config/servers.json`:
```json
{
  "brave_search": {
    "api_key": "your-brave-search-api-key"
  }
}
```

> 💡 **Tip**: You only need API keys for the providers you plan to use. Start with one provider and add others as needed.

## 💡 Usage Examples

### Basic Single Agent Chat

Perfect for simple AI conversations:

```python
# 1. Start the application
python start_app.py

# 2. Configure one agent:
#    - Provider: OpenAI
#    - Model: gpt-4
#    - Instructions: "You are a helpful assistant"

# 3. Type your question and press Enter
```

### Multi-Agent Software Development

Set up a development team:

```python
# Agent 1 - Software Architect (Claude 3.5 Sonnet)
Instructions: "You are a senior software architect. Design system architecture and provide technical guidance."

# Agent 2 - Implementation Expert (GPT-4)
Instructions: "You are a coding expert. Implement solutions based on architectural guidance."

# Agent 3 - Quality Assurance (Gemini Pro)
Instructions: "You are a QA specialist. Review code for bugs, security issues, and best practices."
```

### Research with RAG

Enhance AI responses with your documents:

```python
# 1. Upload documents to knowledge base:
#    - Click "Knowledge Base" → "Add Documents"
#    - Select PDFs, Word docs, or text files

# 2. Enable RAG for agents:
#    - Check "Enable RAG" for each agent

# 3. Ask questions about your documents:
#    "Based on the uploaded research papers, what are the key findings about..."
```

### Creative Writing Team

Collaborative storytelling:

```python
# Agent 1 - Story Planner (Claude 3.5 Sonnet)
Instructions: "You create detailed story outlines and character development."

# Agent 2 - Creative Writer (GPT-4)
Instructions: "You write engaging prose based on story plans."

# Agent 3 - Editor (Gemini Pro)
Instructions: "You review and improve writing for clarity, flow, and style."
```

## 📖 Documentation

### 🚀 Getting Started
- **[SETUP.md](SETUP.md)** - Detailed installation and configuration guide
- **[Quick Start](#-quick-start)** - Get running in 5 minutes
- **[API Key Setup](#-api-key-configuration)** - Configure your AI providers

### 🔧 Advanced Features
- **[Thinking Feature](docs/THINKING_FEATURE.md)** - Enable AI reasoning visualization
- **[RAG System](docs/RAG_GUIDE.md)** - Knowledge base integration guide
- **[Multi-Agent Profiles](example_profiles/)** - Pre-built agent configurations

### 🛠️ Development
- **[Project Structure](#-project-structure)** - Codebase organization
- **[Contributing Guidelines](#-contributing)** - How to contribute
- **[Cross-Platform Guide](CROSS_PLATFORM_README.md)** - Platform-specific instructions

### 🐛 Troubleshooting
- **[Common Issues](#-troubleshooting)** - Solutions to frequent problems
- **[Performance Optimization](OPTIMIZATIONS.md)** - Speed up your experience
- **[Log Files](#log-files)** - Debugging information

## 🏗️ Project Structure

```
maiachat-desktop/
├── 🚀 Core Application
│   ├── start_app.py              # Main entry point (use this!)
│   ├── main_window.py            # GUI main window
│   ├── agent_config.py           # Agent configuration UI
│   ├── conversation_manager.py   # Conversation handling
│   └── worker.py                 # AI processing engine
│
├── 🧠 AI & RAG System
│   ├── rag_handler.py            # RAG processing
│   ├── knowledge_base.py         # Document management
│   ├── internet_search.py        # Web search integration
│   └── token_counter.py          # Usage tracking
│
├── ⚙️ Configuration
│   ├── config.json.example       # Configuration template
│   ├── config_manager.py         # Settings management
│   ├── api_key_manager.py        # API key handling
│   └── instruction_templates.py  # Agent instructions
│
├── 🎨 User Interface
│   ├── ui/                       # PyQt6 UI components
│   ├── icons/                    # Application icons
│   └── example_profiles/         # Pre-built agent setups
│
├── 📊 Data & Storage
│   ├── knowledge_base/           # RAG vector database
│   ├── conversation_history/     # Chat history
│   ├── cache/                    # Model cache
│   └── mcp_config/              # MCP server config
│
└── 🔧 Utilities
    ├── install_dependencies.py   # Automated installer
    ├── safe_rag.py              # Safe RAG processing
    └── pricing.json             # API cost configuration
```

## 🔧 Advanced Configuration

### Environment Variables

You can also configure API keys using environment variables:

```bash
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GOOGLE_API_KEY="your-google-key-here"
```

### Custom Model Settings

Edit `config.json` to customize model parameters:

```json
{
  "model_settings": {
    "temperature": 0.7,
    "max_tokens": 4000,
    "top_p": 0.9
  }
}
```

### RAG Configuration

Customize knowledge base settings:

```json
{
  "rag_settings": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "max_results": 5,
    "similarity_threshold": 0.7
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### ❌ "No module named 'PyQt6'"
```bash
# Solution: Install PyQt6
pip install PyQt6
# Or run the installer again
python install_dependencies.py
```

#### ❌ "API key not found"
```bash
# Solution: Check your config.json file
cp config.json.example config.json
# Edit config.json with your actual API keys
```

#### ❌ RAG/Knowledge Base Issues
```bash
# Solution: Clear and rebuild knowledge base
rm -rf knowledge_base/
# Restart app and re-upload documents
```

#### ❌ Application Won't Start
```bash
# Solution: Check Python version and dependencies
python --version  # Should be 3.8+
pip install -r requirements.txt
python start_app.py  # Use start_app.py, not main.py
```

### Log Files

Check these files for detailed error information:
- `start_app.log` - Application startup and general errors
- `rag_handler.log` - Knowledge base and RAG issues
- `conversation_manager.log` - Chat and agent coordination
- `worker.log` - AI provider API calls and responses

### Performance Issues

If the application is slow:
1. **Reduce agent count** - Start with 1-2 agents
2. **Disable RAG** - Turn off knowledge base for faster responses
3. **Use faster models** - Try Groq or smaller models
4. **Check internet connection** - Slow API calls affect performance

### Getting Help

1. **Check existing issues** on GitHub
2. **Search the documentation** in the `docs/` folder
3. **Review log files** for specific error messages
4. **Create a new issue** with:
   - Your operating system
   - Python version
   - Error message and log files
   - Steps to reproduce the problem

## 🎯 Roadmap & Development Status

### ✅ Recently Completed (2025-01-27)
- **🔒 Security Cleanup**: Prepared for open source release with secure API key handling
- **📝 Documentation**: Comprehensive setup guides and user documentation
- **🎨 UI Improvements**: Enhanced agent configuration with color coding and collapsible sections
- **🧠 RAG Enhancements**: Per-agent knowledge base control and improved document processing
- **🔧 Stability**: Fixed critical bugs and improved error handling across all platforms

### 🔄 Current Focus
- **📖 Documentation**: Expanding user guides and API documentation
- **🧪 Testing**: Comprehensive testing across different platforms and configurations
- **🎨 UI Polish**: Further interface improvements and user experience enhancements

### 🚀 Upcoming Features
- **🔌 Plugin System**: Extensible architecture for custom integrations
- **📊 Analytics Dashboard**: Advanced usage statistics and conversation insights
- **🌐 Web Interface**: Optional web-based interface for remote access
- **🤖 Custom Models**: Support for fine-tuned and custom AI models
- **📱 Mobile Companion**: Mobile app for conversation management

### 📈 Progress Tracking
- **Completed**: 6/20 major milestones (30%)
- **In Progress**: 3/20 milestones (15%)
- **Planned**: 11/20 milestones (55%)

See [`TODO.md`](TODO.md) for detailed task status and [`tasks_completed.md`](tasks_completed.md) for implementation history.

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### 🐛 Bug Reports
- **Search existing issues** before creating new ones
- **Include detailed information**: OS, Python version, error messages
- **Provide reproduction steps** and relevant log files
- **Use issue templates** when available

### 💡 Feature Requests
- **Check the roadmap** to see if it's already planned
- **Describe the use case** and expected behavior
- **Consider implementation complexity** and maintenance burden
- **Discuss in issues** before starting major features

### 🔧 Code Contributions
1. **Fork the repository** and create a feature branch
2. **Follow coding standards**: PEP 8, type hints, docstrings
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with clear description

### 📝 Documentation
- **Improve existing docs** with clarifications and examples
- **Add new guides** for advanced features
- **Fix typos and formatting** issues
- **Translate documentation** to other languages

### 🧪 Testing
- **Test on different platforms** (Windows, macOS, Linux)
- **Try various AI providers** and model combinations
- **Report compatibility issues** with specific configurations
- **Help with performance testing** and optimization

## 📄 License & Attribution

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Created by [Aleksander Celewicz](https://MAIAChat.com)**

</div>

### 📋 Usage Terms

- ✅ **FREE** for personal, educational, and non-commercial use
- ✅ **Open source** under MIT License - modify and distribute freely
- ⚠️ **Commercial use** requires attribution: *"Powered by MAIAChat.com Desktop by Aleksander Celewicz"*
- 💼 **Commercial licensing** without attribution available - contact creator

### 🏢 Commercial Use Requirements

**For ANY commercial use** (including internal business use), you must include the following attribution prominently in your application, documentation, or marketing materials:

```
"Powered by MAIAChat.com Desktop by Aleksander Celewicz"
```

**Placement Options** (choose one):
- Application About dialog or Help menu
- README.md or main documentation
- Product website or marketing materials

**Need attribution-free licensing?** Contact for enterprise licensing options.

📖 **Full Details**: See [LICENSE_COMPLIANCE.md](LICENSE_COMPLIANCE.md) and [COMMERCIAL_USE.md](COMMERCIAL_USE.md)

### 🏆 Recognition

If MAIAChat helps your project:
- ⭐ **Star this repository** to show support
- 🐦 **Share on social media** with #MAIAChat
- 📝 **Write a blog post** about your experience
- 💬 **Join the community** and help others

### 📺 Learning & Tutorials

**Subscribe to [AIex The AI Workbench](https://www.youtube.com/@AIexTheAIWorkbench) for:**
- 🎬 **MAIAChat tutorials** and advanced usage tips
- 🔧 **AI workflow demonstrations** and best practices
- 📢 **Latest updates** and feature announcements
- 💬 **Community Q&A** sessions and troubleshooting
- 🚀 **AI automation** techniques and integrations

### 📞 Support & Contact

- 🌐 **Website**: [MAIAChat.com](https://MAIAChat.com)
- 📺 **YouTube**: [AIex The AI Workbench](https://www.youtube.com/@AIexTheAIWorkbench) - Tutorials, demos, and updates
- 📧 **Commercial inquiries**: Contact Aleksander Celewicz
- 🐛 **Bug reports**: Use GitHub Issues
- 💬 **Community**: GitHub Discussions
- 📖 **Documentation**: Check the `docs/` folder

---

<div align="center">

**Made with ❤️ by [Aleksander Celewicz](https://MAIAChat.com)**

*Empowering conversations with AI • Building the future of human-AI collaboration*

[![GitHub stars](https://img.shields.io/github/stars/your-username/maiachat-desktop?style=social)](https://github.com/your-username/maiachat-desktop)
[![Follow](https://img.shields.io/twitter/follow/your-twitter?style=social)](https://twitter.com/your-twitter)

</div>
