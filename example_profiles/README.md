# Example Agent Profiles

This directory contains pre-configured agent profiles that demonstrate different multi-agent workflows and use cases. Each profile is ready to use and showcases specific collaboration patterns and capabilities.

## 📋 Available Profiles

### 🔧 Software Development Profiles

#### **Elite Solo Software Developer**
- **Agents**: 1
- **Focus**: Single elite developer for complex programming tasks
- **Best For**: Individual development projects, code reviews, architecture design
- **Features**: Comprehensive analysis, design patterns, production-ready code

#### **Dynamic Duo Code Review**
- **Agents**: 2 (Developer + Senior Reviewer)
- **Focus**: Draft-and-review development workflow
- **Best For**: Code quality improvement, collaborative development
- **Features**: Initial implementation + expert optimization

#### **Triple Threat Development**
- **Agents**: 3 (Architect + Implementation Expert + QA Specialist)
- **Focus**: Complete development lifecycle with testing
- **Best For**: Enterprise-grade solutions, comprehensive quality assurance
- **Features**: Architecture design, implementation, testing validation

#### **Quad Force Engineering**
- **Agents**: 4 (Product Strategist + System Architect + Senior Developer + DevOps Engineer)
- **Focus**: Full-stack engineering with operations
- **Best For**: Scalable applications, production deployment
- **Features**: Strategy, architecture, development, deployment

#### **Pentagon Elite Development**
- **Agents**: 5 (Product Visionary + Chief Architect + Master Developer + Quality Guardian + Executive Reviewer)
- **Focus**: World-class software development with executive oversight
- **Best For**: Mission-critical applications, enterprise solutions
- **Features**: Complete development lifecycle with strategic guidance

#### **Software Development Team**
- **Agents**: 5 (Product Owner + Architect & Developer + Senior Reviewer + Refactoring Developer + Quality Analyst)
- **Focus**: Plan-Draft-Review-Refine cycle with comprehensive analysis
- **Best For**: Complex software projects, iterative development
- **Features**: Requirements analysis, implementation, review, refinement

### 🧩 Problem Solving Profiles

#### **Logic Masters Duo**
- **Agents**: 2 (Logic Analyst + Verification Specialist)
- **Focus**: Complex puzzles and logical reasoning
- **Best For**: Mathematical problems, logical puzzles, analytical challenges
- **Features**: Systematic analysis + rigorous verification

#### **Puzzle Solving Trinity**
- **Agents**: 3 (Creative Problem Solver + Systematic Analyst + Critical Validator)
- **Focus**: Advanced puzzle-solving with multiple approaches
- **Best For**: Complex brain teasers, multi-faceted problems
- **Features**: Creative thinking + systematic analysis + validation

#### **Collaborative Analysis Team**
- **Agents**: 5 (Initial Analyst + Critical Reviewer + Solution Synthesizer + Quality Validator + Final Decision Maker)
- **Focus**: Thorough analysis with multiple verification stages
- **Best For**: Complex research, critical analysis, decision making
- **Features**: Multi-stage verification, error detection, collaborative refinement

### 🔄 Workflow Profiles

#### **Architect-Engineer Workflow**
- **Agents**: 2 (Lead Architect + Principal Engineer)
- **Focus**: Specification-driven development with quality control
- **Best For**: Structured development, precise requirements implementation
- **Features**: Detailed specifications + rigorous execution

#### **Five-Agent Collaborative Analysis**
- **Agents**: 5 (Mixed local Ollama + cloud models)
- **Focus**: Hybrid local/cloud analysis with comprehensive verification
- **Best For**: Resource-conscious analysis, local model testing
- **Features**: Local Ollama models + cloud AI verification

### 💼 Professional Profiles

#### **Professional Work Assistant**
- **Agents**: 1
- **Focus**: Business communication and document assistance
- **Best For**: Professional writing, document drafting, communication
- **Features**: Business-focused, professional tone, document creation

### 🔧 Technical Testing Profiles

#### **MCP File Operations Test**
- **Agents**: 2 (File Reader + File Writer)
- **Focus**: Model Context Protocol (MCP) file operations testing
- **Best For**: Testing MCP functionality, file operations
- **Features**: File reading, analysis, writing with MCP

## 🚀 How to Use

1. **Select a Profile**: Choose a profile that matches your use case
2. **Load in Application**: Import the JSON file through the profile management interface
3. **Customize if Needed**: Modify agent instructions, models, or settings as required
4. **Start Conversation**: Begin your multi-agent conversation with your chosen team

## 📝 Profile Structure

Each profile contains:
- **name**: Display name for the profile
- **description**: Brief explanation of the profile's purpose
- **agent_count**: Number of agents in the team
- **general_instructions**: Overall workflow guidance
- **agents**: Array of agent configurations with:
  - **provider**: AI service provider (OpenAI, Anthropic, Google GenAI, etc.)
  - **model**: Specific model to use
  - **instructions**: Detailed role-specific instructions
  - **agent_number**: Position in the workflow
  - **thinking_enabled**: Whether to show reasoning process
  - **rag_enabled**: Whether to use knowledge base
  - **mcp_enabled**: Whether to enable MCP operations

## 🎯 Choosing the Right Profile

- **Single Complex Task**: Elite Solo Software Developer
- **Code Quality Focus**: Dynamic Duo Code Review
- **Complete Development**: Triple Threat Development or higher
- **Problem Solving**: Logic Masters Duo or Puzzle Solving Trinity
- **Research & Analysis**: Collaborative Analysis Team
- **Business Documents**: Professional Work Assistant
- **Testing MCP**: MCP File Operations Test

## 🔧 Customization Tips

- **Model Selection**: Choose models based on your API access and performance needs
- **Temperature Settings**: Lower for analytical tasks, higher for creative work
- **Instructions**: Modify agent instructions to match your specific domain or requirements
- **Knowledge Base**: Set appropriate knowledge_base_path for domain-specific information

---

*Created by Aleksander Celewicz | MAIAChat.com*
*Part of the MAIAChat Desktop Application - Open Source Multi-Agent AI Platform*
