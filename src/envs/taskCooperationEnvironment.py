import logging
from .baseEnvironment import BaseEnvironment


class TaskCooperationEnvironment(BaseEnvironment):
    """Environment for task-based cooperation with skill requirements."""
    
    def __init__(self, description, rules, tasks: list = None):
        super().__init__(description, rules)
        self.tasks = tasks or []
        self.task_completion = {}  # task_id -> completion_percentage
        self.agent_assignments = {}  # agent_id -> [task_id, ...]
        self.contributions = {}  # (agent_id, task_id) -> effort_points
        self.completed_tasks = []
        self.failed_tasks = []
        self.project_start_time = 0
        
        # Initialize tasks
        for task in self.tasks:
            task_id = task.get('id')
            self.task_completion[task_id] = 0.0
        
        logging.info(f"TaskCooperationEnvironment initialized with {len(self.tasks)} tasks")
        self._log_task_list()
    
    def _log_task_list(self):
        """Log all available tasks."""
        for task in self.tasks:
            logging.info(f"Task {task['id']}: {task['name']} (requires {task.get('required_effort', 100)} effort points)")
    
    def perform_action(self, agent, action_details):
        if len(self.completed_tasks) + len(self.failed_tasks) >= len(self.tasks):
            return  # All tasks resolved
        
        super().perform_action(agent, action_details)
        env_action = action_details.get('env_action')
        params = action_details.get('params', {}) or {}
        
        if env_action == 'assign_to_task':
            task_id = params.get('task_id')
            self._assign_agent_to_task(agent.id, task_id)
        
        elif env_action == 'contribute':
            task_id = params.get('task_id')
            effort = params.get('effort', 0)
            skill_bonus = params.get('skill_bonus', 1.0)
            self._add_contribution(agent.id, task_id, effort, skill_bonus)
        
        elif env_action == 'request_help':
            task_id = params.get('task_id')
            skill_type = params.get('skill_type', 'any')
            self._log_help_request(agent.id, task_id, skill_type)
        
        elif env_action == 'complete_task':
            task_id = params.get('task_id')
            self._check_task_completion(task_id)
    
    def _assign_agent_to_task(self, agent_id: str, task_id: str):
        """Assign an agent to work on a specific task."""
        if agent_id not in self.agent_assignments:
            self.agent_assignments[agent_id] = []
        
        if task_id not in self.agent_assignments[agent_id]:
            self.agent_assignments[agent_id].append(task_id)
            logging.info(f"Agent {agent_id} assigned to task {task_id}")
        else:
            logging.info(f"Agent {agent_id} is already assigned to task {task_id}")
    
    def _add_contribution(self, agent_id: str, task_id: str, effort: int, skill_bonus: float = 1.0):
        """Add contribution points to a task."""
        if task_id in self.completed_tasks or task_id in self.failed_tasks:
            logging.warning(f"Task {task_id} is already resolved")
            return
        
        # Apply skill bonus
        effective_effort = int(effort * skill_bonus)
        key = (agent_id, task_id)
        
        if key not in self.contributions:
            self.contributions[key] = 0
        
        self.contributions[key] += effective_effort
        self.task_completion[task_id] = self.task_completion.get(task_id, 0) + effective_effort
        
        logging.info(f"Agent {agent_id} contributes {effective_effort} effort (x{skill_bonus} bonus) to task {task_id}")
        logging.info(f"Task {task_id} progress: {self.task_completion[task_id]}")
    
    def _log_help_request(self, agent_id: str, task_id: str, skill_type: str):
        """Log a help request for a task."""
        logging.info(f"Agent {agent_id} requests help on task {task_id} (skill: {skill_type})")
    
    def _check_task_completion(self, task_id: str):
        """Check if a task is completed based on effort threshold."""
        if task_id in self.completed_tasks or task_id in self.failed_tasks:
            return
        
        # Find task in list
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return
        
        required_effort = task.get('required_effort', 100)
        current_progress = self.task_completion.get(task_id, 0)
        
        if current_progress >= required_effort:
            self.completed_tasks.append(task_id)
            logging.info(f"✓ TASK COMPLETED: {task_id} ({current_progress}/{required_effort})")
            if len(self.completed_tasks) == len(self.tasks):
                self.is_finished = True
                logging.info("All tasks completed! Project finished successfully.")
        else:
            logging.info(f"Task {task_id} not yet complete: {current_progress}/{required_effort}")
    
    def env_step(self):
        """Advance the environment by one step."""
        super().env_step()
        logging.info(f"--- Cooperation Step {self.step} ---")
        self._log_progress()
    
    def _log_progress(self):
        """Log the overall progress of the project."""
        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        in_progress = total_tasks - completed - failed
        
        logging.info(f"Project Progress: {completed} completed, {in_progress} in progress, {failed} failed")
        
        for task in self.tasks:
            task_id = task['id']
            progress = self.task_completion.get(task_id, 0)
            required = task.get('required_effort', 100)
            status = "✓" if task_id in self.completed_tasks else ("✗" if task_id in self.failed_tasks else "→")
            logging.info(f"  {status} {task_id}: {progress}/{required}")
    
    def get_prompt(self):
        """Get task cooperation state for agents."""
        task_info = []
        for task in self.tasks:
            task_id = task['id']
            progress = self.task_completion.get(task_id, 0)
            required = task.get('required_effort', 100)
            percentage = min(100, int(progress / required * 100))
            
            if task_id in self.completed_tasks:
                status = "✓ COMPLETED"
            elif task_id in self.failed_tasks:
                status = "✗ FAILED"
            else:
                status = f"→ {percentage}%"
            
            task_info.append(f"  [{status}] {task_id}: {task['name']} ({progress}/{required})")
        
        agent_info = []
        for agent_id, tasks in sorted(self.agent_assignments.items()):
            agent_info.append(f"  {agent_id}: {', '.join(tasks) if tasks else 'not assigned'}")
        
        return f"""
PROJECT STATE:
Tasks ({len(self.completed_tasks)}/{len(self.tasks)} completed):
{chr(10).join(task_info)}

Agent Assignments:
{chr(10).join(agent_info) if agent_info else "  No agents assigned yet"}
"""
    
    def get_context(self):
        """Return full context for agents."""
        base = super().get_context()
        return f"{base}\n{self.get_prompt()}"
