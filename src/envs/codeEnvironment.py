import os
import subprocess
import logging
from .baseEnvironment import BaseEnvironment

class CodeEnvironment(BaseEnvironment):
    """Environment for coding agents with file system and terminal access."""
    def __init__(self, description, rules, work_dir="./playground"):
        super().__init__(description, rules)
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        logging.info(f"CodeEnvironment initialized with work_dir: {self.work_dir}")

    def _get_files_in_work_dir(self):
        try:
            files = []
            for root, _, filenames in os.walk(self.work_dir):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), self.work_dir)
                    files.append(rel_path)
            return files
        except Exception as e:
            return f"Error listing files: {e}"

    def get_context(self):
        files = self._get_files_in_work_dir()
        base = super().get_context()
        return f"{base}\nCurrent Working Directory: {self.work_dir}\nFiles available: {files}"

    def perform_action(self, agent, action_details):
        if self.is_finished:
            return
        super().perform_action(agent, action_details)
        
        env_action = action_details.get('env_action')
        params = action_details.get('params', {}) or {}

        if env_action == 'read_file':
            path = params.get('path')
            if not path:
                self.log_private(agent, action_details, "Error: 'path' parameter missing.")
                return

            # Security check: ensure path is within work_dir
            target_path = os.path.abspath(os.path.join(self.work_dir, path))
            if not target_path.startswith(self.work_dir):
                self.log_private(agent, action_details, "Error: Access denied (path outside work_dir).")
                return
            
            if not os.path.exists(target_path):
                self.log_private(agent, action_details, f"Error: File '{path}' does not exist.")
                return

            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.log_private(agent, action_details, f"File Content ({path}):\n{content}")
            except Exception as e:
                self.log_private(agent, action_details, f"Error reading file: {e}")
            return

        if env_action == 'write_file':
            path = params.get('path')
            content = params.get('content')
            if not path or content is None:
                self.log_private(agent, action_details, "Error: 'path' or 'content' parameter missing.")
                return

            # Security check
            target_path = os.path.abspath(os.path.join(self.work_dir, path))
            if not target_path.startswith(self.work_dir):
                self.log_private(agent, action_details, "Error: Access denied (path outside work_dir).")
                return

            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"Agent {agent.id} wrote to file '{path}'.")
                self.log_private(agent, action_details, f"Success: File '{path}' written.")
            except Exception as e:
                self.log_private(agent, action_details, f"Error writing file: {e}")
            return

        if env_action == 'list_files':
            path = params.get('path', '.')
            # Security check
            target_path = os.path.abspath(os.path.join(self.work_dir, path))
            if not target_path.startswith(self.work_dir):
                self.log_private(agent, action_details, "Error: Access denied (path outside work_dir).")
                return

            if not os.path.exists(target_path):
                self.log_private(agent, action_details, f"Error: Path '{path}' does not exist.")
                return

            try:
                files = os.listdir(target_path)
                self.log_private(agent, action_details, f"Contents of '{path}': {files}")
            except Exception as e:
                self.log_private(agent, action_details, f"Error listing files: {e}")
            return

        if env_action == 'create_directory':
            path = params.get('path')
            if not path:
                self.log_private(agent, action_details, "Error: 'path' parameter missing.")
                return
            
            # Security check
            target_path = os.path.abspath(os.path.join(self.work_dir, path))
            if not target_path.startswith(self.work_dir):
                self.log_private(agent, action_details, "Error: Access denied (path outside work_dir).")
                return

            try:
                os.makedirs(target_path, exist_ok=True)
                self.log(f"Agent {agent.id} created directory '{path}'.")
                self.log_private(agent, action_details, f"Success: Directory '{path}' created.")
            except Exception as e:
                self.log_private(agent, action_details, f"Error creating directory: {e}")
            return

        if env_action == 'run_command':
            command = params.get('command')
            if not command:
                self.log_private(agent, action_details, "Error: 'command' parameter missing.")
                return
            
            # Simple security check (very basic)
            blocked_cmds = ['rm -rf', 'format', 'shutdown']
            if any(b in command for b in blocked_cmds):
                self.log_private(agent, action_details, "Error: Command blocked for security.")
                return

            self.log(f"Agent {agent.id} running command: {command}")
            try:
                # Capture output
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=10 # 10 seconds timeout
                )
                output = f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}\nReturn Code: {result.returncode}"
                self.log_private(agent, action_details, f"Command Result:\n{output}")
            except subprocess.TimeoutExpired:
                 self.log_private(agent, action_details, "Error: Command timed out.")
            except Exception as e:
                self.log_private(agent, action_details, f"Error running command: {e}")
            return

        self.log(f"Action '{env_action}' not recognized in CodeEnvironment.")
