# 🤝 Contributing to MAIAChat Desktop

**Created by Aleksander Celewicz**

Thank you for your interest in contributing to MAIAChat Desktop! This guide will help you get started with contributing to our open source multi-agent AI desktop application.

## 🌟 Welcome Contributors!

We welcome contributions from developers of all skill levels. Whether you're fixing a typo, adding a feature, or improving documentation, your contribution matters!

### 🎯 Ways to Contribute

- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new functionality
- 🔧 **Code Contributions**: Implement features and fixes
- 📝 **Documentation**: Improve guides and examples
- 🧪 **Testing**: Test on different platforms and configurations
- 🌍 **Translation**: Help make MAIAChat accessible worldwide
- 💬 **Community Support**: Help other users in discussions

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/maiachat-desktop.git
cd maiachat-desktop

# Add the original repository as upstream
git remote add upstream https://github.com/ORIGINAL-OWNER/maiachat-desktop.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python install_dependencies.py

# Set up configuration
cp config.json.example config.json
# Add your API keys to config.json

# Run the application to test
python start_app.py
```

### 3. Create a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure the bug still exists
3. **Check documentation** to verify expected behavior
4. **Try minimal reproduction** to isolate the issue

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11, macOS 13, Ubuntu 22.04]
- Python Version: [e.g., 3.9.7]
- MAIAChat Version: [e.g., 1.0.0]
- AI Providers Used: [e.g., OpenAI, Anthropic]

**Additional Context**
- Log files (start_app.log, rag_handler.log)
- Configuration details (without API keys)
- Any other relevant information
```

## 💡 Feature Requests

### Before Requesting

1. **Check the roadmap** in README.md
2. **Search existing issues** for similar requests
3. **Consider the scope** - is it aligned with MAIAChat's goals?
4. **Think about implementation** - how complex would it be?

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How do you envision this feature working?

**Alternatives Considered**
Other approaches you've considered.

**Use Cases**
Specific scenarios where this would be useful.

**Implementation Notes**
Any technical considerations or suggestions.
```

## 🔧 Code Contributions

### Development Guidelines

#### Code Style

- **Python**: Follow PEP 8 style guidelines
- **Line Length**: Maximum 88 characters (Black formatter standard)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Type Hints**: Add type hints for function parameters and returns
- **Docstrings**: Use Google-style docstrings for functions and classes

```python
def process_message(message: str, agent_id: int) -> Dict[str, Any]:
    """Process a message through the specified agent.
    
    Args:
        message: The user message to process
        agent_id: ID of the agent to use for processing
        
    Returns:
        Dictionary containing the processed response and metadata
        
    Raises:
        ValueError: If agent_id is invalid
        APIError: If the AI provider request fails
    """
    # Implementation here
    pass
```

#### Code Organization

- **Single Responsibility**: Each function/class should have one clear purpose
- **Error Handling**: Use appropriate exception handling with specific error types
- **Logging**: Use the existing logging system for debug information
- **Configuration**: Use the config_manager for all settings
- **Security**: Never hardcode API keys or sensitive information

#### Testing

```bash
# Run existing tests (when available)
python -m pytest tests/

# Test your changes manually
python start_app.py

# Test on different platforms if possible
# Test with different AI providers
# Test with and without RAG enabled
```

### Pull Request Process

#### 1. Prepare Your Changes

```bash
# Make sure you're on your feature branch
git checkout feature/your-feature-name

# Make your changes
# Test thoroughly
# Commit with clear messages

git add .
git commit -m "feat: add support for custom agent instructions

- Add UI for custom instruction templates
- Implement instruction validation
- Update agent configuration system
- Add tests for instruction handling"
```

#### 2. Update Documentation

- Update README.md if adding new features
- Add/update docstrings for new functions
- Update SETUP.md if changing installation process
- Add examples for new functionality

#### 3. Submit Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Use the pull request template
# Link to related issues
```

### Pull Request Template

```markdown
**Description**
Brief description of changes made.

**Type of Change**
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

**Related Issues**
Fixes #(issue number)

**Testing**
- [ ] Tested on Windows
- [ ] Tested on macOS  
- [ ] Tested on Linux
- [ ] Tested with multiple AI providers
- [ ] Tested with RAG enabled/disabled

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Attribution maintained for Aleksander Celewicz
```

## 📝 Documentation Contributions

### Types of Documentation

- **User Guides**: Help users accomplish specific tasks
- **API Documentation**: Document functions and classes
- **Setup Guides**: Installation and configuration instructions
- **Examples**: Real-world usage scenarios
- **Troubleshooting**: Solutions to common problems

### Documentation Standards

- **Clear Language**: Write for users of all technical levels
- **Step-by-Step**: Break complex processes into simple steps
- **Examples**: Include practical, working examples
- **Screenshots**: Add visuals where helpful
- **Testing**: Verify all instructions work as written

## 🧪 Testing Contributions

### Testing Areas

- **Platform Testing**: Windows, macOS, Linux
- **Provider Testing**: Different AI providers and models
- **Feature Testing**: RAG, multi-agent, conversation management
- **Performance Testing**: Large knowledge bases, long conversations
- **Security Testing**: API key handling, data privacy

### Testing Guidelines

```bash
# Test installation from scratch
rm -rf venv/
python -m venv venv
source venv/bin/activate
python install_dependencies.py

# Test with minimal configuration
cp config.json.example config.json
# Add only one API key
python start_app.py

# Test edge cases
# - Very long messages
# - Large knowledge base documents
# - Network interruptions
# - Invalid API keys
```

## 🌍 Translation Contributions

We welcome translations to make MAIAChat accessible worldwide!

### Translation Process

1. **Check existing translations** in the `translations/` folder
2. **Create language folder** (e.g., `translations/es/` for Spanish)
3. **Translate UI strings** in JSON format
4. **Test with your language** settings
5. **Submit pull request** with translation files

## 🏆 Recognition

### Contributor Recognition

- **Contributors file**: All contributors listed in CONTRIBUTORS.md
- **Release notes**: Significant contributions mentioned in releases
- **GitHub recognition**: Contributor badge and statistics
- **Community thanks**: Recognition in discussions and social media

### Attribution Requirements

All contributions must maintain:
- **Original attribution** to Aleksander Celewicz as creator
- **MIT license** compatibility
- **Commercial use** attribution requirements
- **Creator contact** information for licensing

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community support
- **Documentation**: Check existing guides first
- **Direct Contact**: Aleksander Celewicz for complex issues

### Response Times

- **Bug reports**: 1-3 business days
- **Feature requests**: 1-7 days for initial response
- **Pull requests**: 1-5 days for review
- **Security issues**: 24-48 hours

## ✅ Contributor Checklist

Before submitting any contribution:

- [ ] Read and understand this contributing guide
- [ ] Check existing issues and pull requests
- [ ] Test your changes thoroughly
- [ ] Follow code style guidelines
- [ ] Update relevant documentation
- [ ] Maintain original attribution
- [ ] Use clear, descriptive commit messages
- [ ] Be respectful and constructive in all interactions

## 🎯 Priority Areas

We especially welcome contributions in these areas:

1. **Cross-platform testing** - Ensuring compatibility across OS
2. **Performance optimization** - Making MAIAChat faster and more efficient
3. **Documentation improvements** - Better guides and examples
4. **Accessibility features** - Making MAIAChat usable for everyone
5. **Security enhancements** - Improving data protection and privacy
6. **UI/UX improvements** - Better user experience and interface design

---

**Thank you for contributing to MAIAChat Desktop! Your efforts help make AI more accessible and powerful for everyone.**

*This contributing guide is part of MAIAChat Desktop by Aleksander Celewicz*
