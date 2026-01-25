import random
import logging
from agent import Agent
from envs.baseEnvironment import BaseEnvironment
from envs.loupGarouEnvironment import LoupGarouEnvironment
from envs.secretNumber import SecretNumberEnvironment
      

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

    return BaseEnvironment(
        description=env_config.get('description', 'No description.'),
        rules=env_config.get('rules', 'No rules.')
    )
