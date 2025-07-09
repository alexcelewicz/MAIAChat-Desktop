"""
Profile manager for handling agent profiles.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass, field, asdict

@dataclass
class AgentProfile:
    """Class for storing agent profile information."""
    provider: str
    model: str
    instructions: str
    agent_number: int
    thinking_enabled: bool = False
    internet_enabled: bool = False
    rag_enabled: bool = False
    mcp_enabled: bool = False

@dataclass
class Profile:
    """Class for storing a complete profile with multiple agents."""
    name: str
    description: str
    general_instructions: str
    agents: List[AgentProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "general_instructions": self.general_instructions,
            "agents": [asdict(agent) for agent in self.agents]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create profile from dictionary."""
        agents = [AgentProfile(**agent_data) for agent_data in data.get("agents", [])]
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            general_instructions=data.get("general_instructions", ""),
            agents=agents
        )


class ProfileManager:
    """Manager class for handling agent profiles."""

    def __init__(self):
        self.profiles_dir = "profiles"
        self.example_profiles_dir = "example_profiles"
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.example_profiles_dir, exist_ok=True)
        self.create_example_profiles()

    def get_profile_list(self) -> List[Tuple[str, str, bool]]:
        """Get list of available profiles.

        Returns:
            List of tuples (profile_name, description, is_example)
        """
        profiles = []

        # Get user profiles
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(self.profiles_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Check if the profile has the required fields
                    name = data.get("name", "")
                    description = data.get("description", "")

                    # If name is missing, try to generate one from the filename
                    if not name:
                        name = os.path.splitext(filename)[0].replace("_", " ").title()
                        logging.warning(f"Profile {filename} missing name field, using '{name}' instead")

                    # Add to profiles list
                    profiles.append((name, description, False))

                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in profile {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error loading profile {filename}: {e}")

        # Get example profiles
        for filename in os.listdir(self.example_profiles_dir):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(self.example_profiles_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Check if the profile has the required fields
                    name = data.get("name", "")
                    description = data.get("description", "")

                    # If name is missing, try to generate one from the filename
                    if not name:
                        name = os.path.splitext(filename)[0].replace("_", " ").title()
                        logging.warning(f"Example profile {filename} missing name field, using '{name}' instead")

                    # Add to profiles list
                    profiles.append((name, description, True))

                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in example profile {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error loading example profile {filename}: {e}")

        return profiles

    def load_profile(self, name: str, is_example: bool = False) -> Optional[Profile]:
        """Load a profile by name."""
        directory = self.example_profiles_dir if is_example else self.profiles_dir
        profile_type = "example profile" if is_example else "profile"

        # Find the profile file
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(directory, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Check if this is the profile we're looking for
                    if data.get("name") == name:
                        try:
                            # Try to create a Profile object from the data
                            profile = Profile.from_dict(data)

                            # Validate that the profile has the required fields
                            if not profile.name:
                                logging.warning(f"{profile_type.capitalize()} {filename} has empty name field")
                                profile.name = name

                            if not profile.description:
                                logging.warning(f"{profile_type.capitalize()} {filename} has empty description field")
                                profile.description = f"A {profile_type} with {len(profile.agents)} agents"

                            # Validate that each agent has the required fields
                            for i, agent in enumerate(profile.agents):
                                if not hasattr(agent, 'agent_number') or agent.agent_number == 0:
                                    logging.warning(f"Agent {i+1} in {profile_type} {filename} missing agent_number, setting to {i+1}")
                                    agent.agent_number = i + 1

                            return profile
                        except Exception as e:
                            logging.error(f"Error creating Profile object from {profile_type} {filename}: {e}")
                            return None
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in {profile_type} {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error loading {profile_type} {filename}: {e}")

        logging.warning(f"Could not find {profile_type} with name '{name}'")
        return None

    def save_profile(self, profile: Profile) -> bool:
        """Save a profile."""
        try:
            filename = f"{profile.name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.profiles_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)

            return True
        except Exception as e:
            logging.error(f"Error saving profile {profile.name}: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name."""
        try:
            # Find the profile file
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.profiles_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    if data.get("name") == name:
                        os.remove(filepath)
                        return True

            return False
        except Exception as e:
            logging.error(f"Error deleting profile {name}: {e}")
            return False

    def create_example_profiles(self):
        """Create example profiles if they don't exist."""
        # Check if example profiles already exist
        if os.listdir(self.example_profiles_dir):
            return

        # Create example profiles
        self._create_single_agent_profiles()
        self._create_two_agent_profiles()
        self._create_three_agent_profiles()
        self._create_four_agent_profiles()
        self._create_five_agent_profiles()
        self._create_mcp_profiles()

    def _create_single_agent_profiles(self):
        """Create example profiles with a single agent."""
        # Research Assistant
        research_assistant = Profile(
            name="Research Assistant",
            description="A single agent that helps with research tasks, summarizing information, and answering questions.",
            general_instructions="""You are a helpful research assistant. Your goal is to provide accurate, well-researched information on any topic.
Use the internet when available to find the most up-to-date information.
Cite your sources and provide balanced perspectives on controversial topics.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""As a research assistant, your task is to:
1. Understand the user's research question or information need
2. Search for relevant information using available tools
3. Synthesize information from multiple sources
4. Present findings in a clear, organized manner
5. Cite sources appropriately
6. Identify gaps in information or areas for further research
7. Maintain objectivity and present multiple perspectives when relevant""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Code Assistant
        code_assistant = Profile(
            name="Code Assistant",
            description="A single agent specialized in programming assistance, code review, and debugging.",
            general_instructions="""You are a programming assistant. Your goal is to help with coding tasks, debugging, and explaining programming concepts.
Focus on providing clean, efficient, and well-documented code examples.
Explain your reasoning and include comments in code to aid understanding.""",
            agents=[
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""As a code assistant, your task is to:
1. Help write clean, efficient, and well-documented code
2. Debug existing code and identify potential issues
3. Explain programming concepts clearly with examples
4. Suggest best practices and optimizations
5. Provide step-by-step explanations for complex algorithms
6. Adapt to different programming languages and frameworks
7. Consider security, performance, and maintainability in your suggestions""",
                    agent_number=1,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(research_assistant)
        self._save_example_profile(code_assistant)

    def _create_two_agent_profiles(self):
        """Create example profiles with two agents."""
        # Debate System
        debate_system = Profile(
            name="Debate System",
            description="Two agents that present opposing viewpoints on a topic to provide balanced perspectives.",
            general_instructions="""This is a debate system with two agents presenting different perspectives on a topic.
The goal is to provide balanced, well-reasoned arguments from multiple viewpoints.
Each agent should present strong arguments for their assigned position while maintaining respect and intellectual honesty.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the first debater. Your role is to:
1. Present the strongest case for the first perspective on the topic
2. Use evidence, logic, and reasoning to support your arguments
3. Acknowledge valid points from the opposing perspective
4. Maintain a respectful, academic tone
5. Focus on the strongest arguments for your position
6. Avoid logical fallacies and misrepresentations""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the second debater. Your role is to:
1. Present the strongest case for the alternative perspective on the topic
2. Use evidence, logic, and reasoning to support your arguments
3. Acknowledge valid points from the opposing perspective
4. Maintain a respectful, academic tone
5. Focus on the strongest arguments for your position
6. Avoid logical fallacies and misrepresentations""",
                    agent_number=2,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Code Review System
        code_review = Profile(
            name="Code Review System",
            description="A two-agent system where one agent writes code and another reviews it for improvements.",
            general_instructions="""This is a code review system with two agents collaborating on code quality.
The first agent will write or improve code based on the user's requirements.
The second agent will review the code, suggesting improvements for readability, efficiency, and best practices.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the code writer. Your role is to:
1. Write clean, efficient code that meets the user's requirements
2. Follow best practices for the programming language being used
3. Include appropriate comments and documentation
4. Consider edge cases and error handling
5. Optimize for readability and maintainability
6. Implement appropriate testing strategies when relevant""",
                    agent_number=1,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the code reviewer. Your role is to:
1. Review the code written by the first agent
2. Identify potential bugs, edge cases, or performance issues
3. Suggest improvements for readability and maintainability
4. Recommend better patterns or approaches where applicable
5. Check for security vulnerabilities
6. Ensure the code follows language-specific best practices
7. Be constructive and specific in your feedback""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(debate_system)
        self._save_example_profile(code_review)

    def _create_three_agent_profiles(self):
        """Create example profiles with three agents."""
        # Product Development Team
        product_team = Profile(
            name="Product Development Team",
            description="A three-agent team simulating a product manager, designer, and developer collaborating on product features.",
            general_instructions="""This is a product development team with three specialists collaborating on product features.
The team will work together to understand requirements, design solutions, and plan implementation.
Each agent brings a different perspective to create a comprehensive approach to product development.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Product Manager. Your role is to:
1. Understand and clarify the user's requirements and business goals
2. Define the problem and success criteria
3. Prioritize features based on user needs and business impact
4. Consider market trends and competitive analysis
5. Ensure the solution balances user needs, technical feasibility, and business goals
6. Create clear user stories and acceptance criteria""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the UX Designer. Your role is to:
1. Design user-centered solutions based on the requirements
2. Consider user flows, information architecture, and interaction patterns
3. Suggest appropriate UI components and layouts
4. Ensure accessibility and usability best practices
5. Balance aesthetics with functionality
6. Provide design rationale and explain your decisions""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Developer. Your role is to:
1. Assess technical feasibility of proposed solutions
2. Identify potential technical challenges and dependencies
3. Suggest appropriate technologies and implementation approaches
4. Consider scalability, performance, and maintainability
5. Estimate development effort and potential technical debt
6. Provide high-level implementation plans or architecture diagrams when helpful""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Research Analysis Team
        research_team = Profile(
            name="Research Analysis Team",
            description="A three-agent team that researches, analyzes, and synthesizes information on complex topics.",
            general_instructions="""This is a research analysis team with three specialists collaborating on complex research questions.
The team will work together to gather information, analyze findings, and synthesize insights.
Each agent brings a different perspective to create a comprehensive research output.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Research Gatherer. Your role is to:
1. Find relevant information from multiple sources on the research topic
2. Ensure information is from credible, reliable sources
3. Gather a diverse range of perspectives and data points
4. Organize information in a structured way
5. Identify key facts, statistics, and quotes
6. Note any contradictions or gaps in available information""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Critical Analyst. Your role is to:
1. Evaluate the quality and reliability of gathered information
2. Identify potential biases or limitations in the research
3. Compare and contrast different perspectives
4. Question assumptions and identify logical fallacies
5. Assess the strength of evidence for different claims
6. Highlight areas where more information is needed""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Synthesizer. Your role is to:
1. Integrate information and analysis into a coherent narrative
2. Highlight key insights and their implications
3. Present balanced perspectives on controversial aspects
4. Create a clear structure that guides the reader through complex information
5. Summarize findings at appropriate levels of detail
6. Suggest areas for further research or consideration""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(product_team)
        self._save_example_profile(research_team)

    def _create_four_agent_profiles(self):
        """Create example profiles with four agents."""
        # Business Strategy Team
        business_team = Profile(
            name="Business Strategy Team",
            description="A four-agent team that analyzes business problems from market, financial, operational, and innovation perspectives.",
            general_instructions="""This is a business strategy team with four specialists collaborating on business challenges.
The team will work together to analyze problems and develop comprehensive strategic recommendations.
Each agent brings a different business perspective to create well-rounded strategic advice.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Market Analyst. Your role is to:
1. Analyze market trends, customer segments, and competitive landscape
2. Identify market opportunities and threats
3. Evaluate customer needs and preferences
4. Assess competitive positioning and differentiation
5. Consider market entry strategies and barriers
6. Provide insights on branding and marketing approaches""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Financial Analyst. Your role is to:
1. Assess financial implications and feasibility of strategies
2. Consider revenue models, pricing strategies, and cost structures
3. Evaluate investment requirements and potential returns
4. Analyze financial risks and mitigation strategies
5. Consider funding options and capital allocation
6. Provide perspective on financial metrics and KPIs""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Operations Specialist. Your role is to:
1. Evaluate operational feasibility and implementation challenges
2. Consider supply chain, logistics, and resource requirements
3. Assess organizational capabilities and constraints
4. Identify process improvements and efficiency opportunities
5. Consider scaling challenges and solutions
6. Provide perspective on operational risks and mitigation""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Groq",
                    model="llama-3.3-70b-versatile",
                    instructions="""You are the Innovation Strategist. Your role is to:
1. Identify disruptive trends and technologies in the industry
2. Suggest innovative approaches and business models
3. Consider long-term strategic positioning and vision
4. Evaluate potential for differentiation through innovation
5. Assess innovation capabilities and development needs
6. Provide perspective on future scenarios and adaptability""",
                    agent_number=4,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Content Creation Team
        content_team = Profile(
            name="Content Creation Team",
            description="A four-agent team that collaborates on creating high-quality content from ideation to final editing.",
            general_instructions="""This is a content creation team with four specialists collaborating on content projects.
The team will work together to develop engaging, accurate, and effective content.
Each agent brings a different perspective to create high-quality content outputs.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Content Strategist. Your role is to:
1. Understand the content goals, target audience, and key messages
2. Define the content strategy and approach
3. Identify key topics and themes to address
4. Consider SEO and distribution channels
5. Align content with broader marketing or communication objectives
6. Provide guidance on content structure and format""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Subject Matter Expert. Your role is to:
1. Provide accurate, in-depth information on the subject
2. Ensure factual correctness and technical accuracy
3. Identify key concepts and principles to include
4. Suggest relevant examples, case studies, or data points
5. Highlight nuances and complexities in the subject matter
6. Address common misconceptions or questions""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Creative Writer. Your role is to:
1. Craft engaging, clear, and compelling content
2. Develop an appropriate voice and tone for the audience
3. Create attention-grabbing headlines and introductions
4. Use storytelling techniques to make content memorable
5. Incorporate analogies and examples to explain complex concepts
6. Balance creativity with clarity and purpose""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Groq",
                    model="llama-3.3-70b-versatile",
                    instructions="""You are the Editor. Your role is to:
1. Review and refine the content for clarity, coherence, and impact
2. Ensure consistent style, tone, and formatting
3. Check for grammatical errors and improve readability
4. Verify that the content meets the original objectives
5. Suggest improvements for structure, flow, and transitions
6. Ensure the content is accessible and engaging for the target audience""",
                    agent_number=4,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(business_team)
        self._save_example_profile(content_team)

    def _create_five_agent_profiles(self):
        """Create example profiles with five agents."""
        # Academic Research Team
        academic_team = Profile(
            name="Academic Research Team",
            description="A five-agent team that simulates a comprehensive academic research process.",
            general_instructions="""This is an academic research team with five specialists collaborating on scholarly research.
The team will work together to investigate research questions with academic rigor.
Each agent brings a different perspective to create comprehensive, well-supported research outputs.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Literature Reviewer. Your role is to:
1. Identify relevant prior research and theoretical frameworks
2. Summarize key findings and methodologies from existing literature
3. Identify gaps and contradictions in current research
4. Place the current research question in context
5. Evaluate the quality and relevance of existing studies
6. Suggest how the current research extends or challenges existing knowledge""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Methodology Expert. Your role is to:
1. Design appropriate research methods to address the research question
2. Consider sampling strategies, data collection, and analysis approaches
3. Identify potential methodological limitations and biases
4. Suggest controls and validity measures
5. Evaluate ethical considerations in the research design
6. Recommend appropriate statistical or analytical techniques""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Data Analyst. Your role is to:
1. Interpret research data and findings
2. Identify patterns, trends, and relationships in the data
3. Consider alternative explanations for results
4. Evaluate statistical significance and effect sizes
5. Suggest appropriate data visualizations
6. Identify limitations in the data and analysis""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Groq",
                    model="llama-3.3-70b-versatile",
                    instructions="""You are the Theoretical Framework Specialist. Your role is to:
1. Connect findings to relevant theoretical frameworks
2. Consider how results support or challenge existing theories
3. Suggest new theoretical insights or extensions
4. Place findings in broader conceptual context
5. Identify implications for theory development
6. Consider interdisciplinary theoretical perspectives""",
                    agent_number=4,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="DeepSeek",
                    model="deepseek-chat",
                    instructions="""You are the Research Implications Specialist. Your role is to:
1. Identify practical implications of the research findings
2. Consider applications in relevant fields or industries
3. Suggest directions for future research
4. Evaluate limitations and generalizability of findings
5. Consider policy implications when relevant
6. Identify stakeholders who might benefit from the research""",
                    agent_number=5,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Software Development Team
        software_team = Profile(
            name="Software Development Team",
            description="A five-agent team that simulates a complete software development lifecycle.",
            general_instructions="""This is a software development team with five specialists collaborating on software projects.
The team will work together to design, develop, and deliver high-quality software solutions.
Each agent brings a different perspective to create comprehensive, well-engineered software.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Product Owner. Your role is to:
1. Clarify business requirements and user needs
2. Define and prioritize features and user stories
3. Ensure the solution delivers business value
4. Make trade-off decisions based on constraints
5. Represent user and stakeholder perspectives
6. Define acceptance criteria and success metrics""",
                    agent_number=1,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Software Architect. Your role is to:
1. Design the overall system architecture
2. Make technology stack recommendations
3. Consider scalability, performance, and security requirements
4. Design data models and system interfaces
5. Identify technical risks and mitigation strategies
6. Ensure the architecture supports business requirements""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Developer. Your role is to:
1. Write clean, efficient, and maintainable code
2. Implement features according to requirements and architecture
3. Consider edge cases and error handling
4. Follow coding best practices and patterns
5. Integrate with existing systems and APIs
6. Document code and implementation details""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="Groq",
                    model="llama-3.3-70b-versatile",
                    instructions="""You are the QA Engineer. Your role is to:
1. Design and implement testing strategies
2. Identify potential bugs and edge cases
3. Ensure the software meets requirements and quality standards
4. Consider performance, security, and usability testing
5. Develop test cases and scenarios
6. Verify bug fixes and regression testing""",
                    agent_number=4,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                ),
                AgentProfile(
                    provider="DeepSeek",
                    model="deepseek-chat",
                    instructions="""You are the DevOps Engineer. Your role is to:
1. Design deployment and infrastructure strategies
2. Consider containerization, CI/CD, and cloud services
3. Plan for monitoring, logging, and observability
4. Ensure security best practices in infrastructure
5. Design for scalability and reliability
6. Consider operational aspects like backups and disaster recovery""",
                    agent_number=5,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=False
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(academic_team)
        self._save_example_profile(software_team)

    def _create_mcp_profiles(self):
        """Create example profiles with MCP integration."""
        # Web Research Assistant with MCP
        web_research_assistant = Profile(
            name="Web Research Assistant with MCP",
            description="A single agent that uses MCP servers to access web search and other external data sources.",
            general_instructions="""You are a research assistant with access to external data sources through MCP servers.
Use the available MCP servers to find information, search the web, and access other data sources.
Cite your sources and provide balanced perspectives on topics.""",
            agents=[
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""As a research assistant with MCP access, your task is to:
1. Understand the user's research question or information need
2. Use MCP servers to search for relevant information
3. Access web search results through Brave Search or DuckDuckGo MCP servers
4. Synthesize information from multiple sources
5. Present findings in a clear, organized manner
6. Cite sources appropriately
7. Identify gaps in information or areas for further research
8. Maintain objectivity and present multiple perspectives when relevant""",
                    agent_number=1,
                    internet_enabled=True,
                    rag_enabled=True,
                    mcp_enabled=True
                )
            ]
        )

        # Software Development Team with MCP
        dev_team_mcp = Profile(
            name="Software Development Team with MCP",
            description="A three-agent team that uses MCP servers to access GitHub, documentation, and other development resources.",
            general_instructions="""This is a software development team with access to external tools through MCP servers.
The team will collaborate on software development tasks using GitHub, documentation, and other resources.
Each agent brings a different perspective and can access different MCP servers.""",
            agents=[
                AgentProfile(
                    provider="OpenAI",
                    model="gpt-4o",
                    instructions="""You are the Technical Lead. Your role is to:
1. Understand the technical requirements and architecture
2. Use GitHub MCP server to access repositories and code
3. Provide high-level technical direction and architecture decisions
4. Consider scalability, performance, and maintainability
5. Evaluate technical trade-offs and make recommendations
6. Ensure code quality and adherence to best practices""",
                    agent_number=1,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=True
                ),
                AgentProfile(
                    provider="Anthropic",
                    model="claude-3-7-sonnet-20250219",
                    instructions="""You are the Developer. Your role is to:
1. Implement features and fix bugs based on requirements
2. Use GitHub MCP server to access code repositories
3. Use Docker MCP server to test code in isolated environments
4. Write clean, efficient, and well-documented code
5. Consider edge cases and error handling
6. Implement appropriate testing strategies""",
                    agent_number=2,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=True
                ),
                AgentProfile(
                    provider="Google GenAI",
                    model="gemini-2.0-pro-exp-02-05",
                    instructions="""You are the Documentation Specialist. Your role is to:
1. Create and maintain technical documentation
2. Use Vectorize MCP server to search existing documentation
3. Ensure documentation is clear, accurate, and comprehensive
4. Create user guides, API documentation, and developer guides
5. Document architecture, design decisions, and implementation details
6. Make documentation accessible to different audiences""",
                    agent_number=3,
                    internet_enabled=False,
                    rag_enabled=True,
                    mcp_enabled=True
                )
            ]
        )

        # Save the profiles
        self._save_example_profile(web_research_assistant)
        self._save_example_profile(dev_team_mcp)

    def _save_example_profile(self, profile: Profile):
        """Save an example profile."""
        try:
            filename = f"{profile.name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.example_profiles_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception as e:
            logging.error(f"Error saving example profile {profile.name}: {e}")


# Create a global instance of the profile manager
profile_manager = ProfileManager()
