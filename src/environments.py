import random
import logging
from agent import Agent
from envs.baseEnvironment import BaseEnvironment
from envs.loupGarouEnvironment import LoupGarouEnvironment
from envs.secretNumber import SecretNumberEnvironment
from envs.codeEnvironment import CodeEnvironment
from envs.debateEnvironment import DebateEnvironment
from envs.taskCooperationEnvironment import TaskCooperationEnvironment
      

def get_environment_by_name(name, env_config):
    """Factory function to get an environment instance by name."""
    if name == 'secret_number_mission':
        return SecretNumberEnvironment(
            description=env_config['description'],
            rules=env_config['rules']
        )
    if name == 'loup_garou':
        return LoupGarouEnvironment(
            description=env_config.get('description', ''),
            rules=env_config.get('rules', ''),
            roles=env_config.get('roles', {})
        )
    if name == 'code_dev':
        return CodeEnvironment(
            description=env_config.get('description', ''),
            rules=env_config.get('rules', ''),
            work_dir=env_config.get('work_dir', './playground')
        )
    if name == 'debate':
        env = DebateEnvironment(
            description=env_config.get('description', ''),
            rules=env_config.get('rules', ''),
            questions=env_config.get('questions', []),
            relationships=env_config.get('relationships', {}),
            debate_deadline=env_config.get('debate_deadline', 8)
        )
        # Set initial opinions if provided
        if 'initial_opinions' in env_config:
            opinions = {agent_id: opinion for agent_id, opinion in env_config['initial_opinions'].items()}
            env.set_initial_opinions(opinions)
        # Set relationships if provided
        if 'relationships' in env_config:
            env.set_relationships(env_config['relationships'])
        return env
    if name == 'task_cooperation':
        return TaskCooperationEnvironment(
            description=env_config.get('description', ''),
            rules=env_config.get('rules', ''),
            tasks=env_config.get('tasks', [])
        )

    return BaseEnvironment(
        description=env_config.get('description', 'No description.'),
        rules=env_config.get('rules', 'No rules.')
    )
