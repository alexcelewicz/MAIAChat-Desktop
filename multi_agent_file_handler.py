#!/usr/bin/env python3
"""
Multi-Agent File Handler for Collaborative Development
Supports multiple agents working together on files with version control and backup
"""

import os
import shutil
import datetime
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class MultiAgentFileHandler:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.backup_path = self.base_path / "code_backup"
        self.agent_logs_path = self.base_path / "agent_logs"
        self.collaboration_log = self.base_path / "collaboration_log.json"
        
        # Create necessary directories
        self.backup_path.mkdir(exist_ok=True)
        self.agent_logs_path.mkdir(exist_ok=True)
        
        # Initialize collaboration log
        if not self.collaboration_log.exists():
            self._init_collaboration_log()
    
    def _init_collaboration_log(self):
        """Initialize the collaboration log file"""
        initial_log = {
            "sessions": [],
            "file_versions": {},
            "agent_activities": {}
        }
        with open(self.collaboration_log, 'w') as f:
            json.dump(initial_log, f, indent=2)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content"""
        if not file_path.exists():
            return ""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def backup_file(self, file_path: str, agent_name: str, operation: str) -> str:
        """Create a backup of the file before modification"""
        source_file = Path(file_path)
        if not source_file.exists():
            return ""
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_file.stem}_{agent_name}_{operation}_{timestamp}{source_file.suffix}"
        backup_file_path = self.backup_path / backup_name
        
        shutil.copy2(source_file, backup_file_path)
        
        # Log the backup
        self._log_activity(agent_name, "backup", file_path, str(backup_file_path))
        
        return str(backup_file_path)
    
    def read_file_for_agent(self, file_path: str, agent_name: str) -> Tuple[str, str]:
        """Read file content and log the access"""
        file_obj = Path(file_path)
        if not file_obj.exists():
            return "", ""
        
        with open(file_obj, 'r') as f:
            content = f.read()
        
        file_hash = self._get_file_hash(file_obj)
        self._log_activity(agent_name, "read", file_path, f"hash:{file_hash}")
        
        return content, file_hash
    
    def write_file_for_agent(self, file_path: str, content: str, agent_name: str, 
                           backup: bool = True) -> bool:
        """Write file content with agent tracking"""
        file_obj = Path(file_path)
        
        # Create backup if requested and file exists
        backup_path = ""
        if backup and file_obj.exists():
            backup_path = self.backup_file(file_path, agent_name, "pre_write")
        
        try:
            # Write the content
            with open(file_obj, 'w') as f:
                f.write(content)
            
            # Log the write operation
            file_hash = self._get_file_hash(file_obj)
            self._log_activity(agent_name, "write", file_path, 
                             f"hash:{file_hash}, backup:{backup_path}")
            
            return True
        except Exception as e:
            self._log_activity(agent_name, "write_failed", file_path, str(e))
            return False
    
    def agent_can_modify(self, file_path: str, agent_name: str) -> Tuple[bool, str]:
        """Check if agent can modify file based on current locks/activity"""
        # Simple implementation - can be extended for more complex locking
        collaboration_data = self._load_collaboration_log()
        
        # Check if another agent is currently working on this file
        recent_activities = self._get_recent_activities(file_path, minutes=5)
        active_agents = set()
        
        for activity in recent_activities:
            if activity['operation'] in ['write', 'modify']:
                active_agents.add(activity['agent_name'])
        
        if active_agents and agent_name not in active_agents:
            return False, f"File is being modified by: {', '.join(active_agents)}"
        
        return True, "OK"
    
    def suggest_collaboration(self, file_path: str, agent_name: str, 
                            requested_operation: str) -> Dict:
        """Suggest how agents should collaborate on this file"""
        collaboration_data = self._load_collaboration_log()
        recent_activities = self._get_recent_activities(file_path, minutes=30)
        
        # Analyze recent activity patterns
        agent_activities = {}
        for activity in recent_activities:
            agent = activity['agent_name']
            if agent not in agent_activities:
                agent_activities[agent] = []
            agent_activities[agent].append(activity)
        
        suggestions = {
            "current_request": {
                "agent": agent_name,
                "operation": requested_operation,
                "file": file_path
            },
            "recent_agents": list(agent_activities.keys()),
            "collaboration_strategy": self._determine_strategy(agent_activities, requested_operation),
            "recommended_workflow": []
        }
        
        # Generate workflow recommendations
        if requested_operation == "improve":
            suggestions["recommended_workflow"] = [
                f"1. {agent_name} should read current file and analyze code",
                "2. Create backup before modifications",
                "3. Implement improvements incrementally",
                "4. If multiple agents involved, coordinate through collaboration log"
            ]
        elif requested_operation == "qa":
            suggestions["recommended_workflow"] = [
                f"1. {agent_name} should review recent changes",
                "2. Run tests and analysis",
                "3. Document findings in agent logs",
                "4. Provide feedback for improvement"
            ]
        
        return suggestions
    
    def _determine_strategy(self, agent_activities: Dict, operation: str) -> str:
        """Determine the best collaboration strategy"""
        if len(agent_activities) <= 1:
            return "single_agent"
        elif operation in ["qa", "review"]:
            return "sequential_review"
        elif operation in ["improve", "modify"]:
            return "collaborative_development"
        else:
            return "coordinated_access"
    
    def _get_recent_activities(self, file_path: str, minutes: int = 30) -> List[Dict]:
        """Get recent activities for a specific file"""
        collaboration_data = self._load_collaboration_log()
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        
        recent = []
        for session in collaboration_data.get("sessions", []):
            for activity in session.get("activities", []):
                activity_time = datetime.datetime.fromisoformat(activity["timestamp"])
                if (activity_time > cutoff_time and 
                    activity["file_path"] == file_path):
                    recent.append(activity)
        
        return recent
    
    def _log_activity(self, agent_name: str, operation: str, file_path: str, details: str):
        """Log agent activity"""
        collaboration_data = self._load_collaboration_log()
        
        # Create new session if needed
        if not collaboration_data["sessions"]:
            collaboration_data["sessions"].append({
                "session_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                "start_time": datetime.datetime.now().isoformat(),
                "activities": []
            })
        
        # Add activity to current session
        activity = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent_name": agent_name,
            "operation": operation,
            "file_path": file_path,
            "details": details
        }
        
        collaboration_data["sessions"][-1]["activities"].append(activity)
        
        # Update agent activity tracking
        if agent_name not in collaboration_data["agent_activities"]:
            collaboration_data["agent_activities"][agent_name] = []
        collaboration_data["agent_activities"][agent_name].append(activity)
        
        # Save updated log
        with open(self.collaboration_log, 'w') as f:
            json.dump(collaboration_data, f, indent=2)
    
    def _load_collaboration_log(self) -> Dict:
        """Load the collaboration log"""
        with open(self.collaboration_log, 'r') as f:
            return json.load(f)
    
    def get_file_history(self, file_path: str) -> List[Dict]:
        """Get modification history for a file"""
        collaboration_data = self._load_collaboration_log()
        history = []
        
        for session in collaboration_data.get("sessions", []):
            for activity in session.get("activities", []):
                if activity["file_path"] == file_path:
                    history.append(activity)
        
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    
    def list_backups(self, file_path: str) -> List[str]:
        """List all backups for a specific file"""
        file_obj = Path(file_path)
        file_stem = file_obj.stem
        
        backups = []
        for backup_file in self.backup_path.glob(f"{file_stem}_*{file_obj.suffix}"):
            backups.append(str(backup_file))
        
        return sorted(backups, reverse=True)
    
    def restore_from_backup(self, backup_path: str, target_path: str, agent_name: str) -> bool:
        """Restore a file from backup"""
        try:
            shutil.copy2(backup_path, target_path)
            self._log_activity(agent_name, "restore", target_path, f"from:{backup_path}")
            return True
        except Exception as e:
            self._log_activity(agent_name, "restore_failed", target_path, str(e))
            return False

# Example usage functions for agents
def agent_read_file(handler: MultiAgentFileHandler, file_path: str, agent_name: str):
    """Helper function for agents to read files"""
    content, file_hash = handler.read_file_for_agent(file_path, agent_name)
    print(f"Agent {agent_name} read {file_path} (hash: {file_hash[:8]})")
    return content

def agent_modify_file(handler: MultiAgentFileHandler, file_path: str, new_content: str, 
                     agent_name: str, operation_type: str = "modify"):
    """Helper function for agents to modify files with collaboration checks"""
    
    # Check if agent can modify
    can_modify, reason = handler.agent_can_modify(file_path, agent_name)
    if not can_modify:
        print(f"Agent {agent_name} cannot modify {file_path}: {reason}")
        return False
    
    # Get collaboration suggestions
    suggestions = handler.suggest_collaboration(file_path, agent_name, operation_type)
    print(f"Collaboration strategy: {suggestions['collaboration_strategy']}")
    
    # Write the file
    success = handler.write_file_for_agent(file_path, new_content, agent_name)
    if success:
        print(f"Agent {agent_name} successfully modified {file_path}")
    else:
        print(f"Agent {agent_name} failed to modify {file_path}")
    
    return success

if __name__ == "__main__":
    # Example usage
    handler = MultiAgentFileHandler("/home/alex/Desktop/Vibe_Coding/Python_Agents")
    
    # Simulate agent activities
    print("=== Multi-Agent File Handler Demo ===")
    
    # Agent 1 reads the snake game
    content = agent_read_file(handler, "/home/alex/Desktop/Vibe_Coding/Python_Agents/test.txt", "Agent1_Developer")
    
    # Agent 2 wants to do QA
    suggestions = handler.suggest_collaboration("/home/alex/Desktop/Vibe_Coding/Python_Agents/test.txt", "Agent2_QA", "qa")
    print(f"QA Agent suggestions: {suggestions}")
    
    # Show file history
    history = handler.get_file_history("/home/alex/Desktop/Vibe_Coding/Python_Agents/test.txt")
    print(f"File history entries: {len(history)}")