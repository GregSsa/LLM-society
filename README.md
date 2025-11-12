# LLM Society

LLM Society is a multi-agent simulation framework designed to explore complex social dynamics using local Large Language Models (LLMs). Each agent in the simulation is powered by an LLM, possessing a unique personality and state, and interacts with other agents within a shared environment.

## Features

- **Multi-Agent Simulation**: Run simulations with multiple AI agents interacting with each other.
- **Local LLM Support**: Powered by [Ollama](https://ollama.com/) to run models locally on your own machine.
- **Configurable Agents**: Define agent personalities, models, and initial states through a simple YAML configuration file.
- **Action-Based Interaction**: Agents communicate and act by generating structured JSON, allowing for complex interactions like messaging or internal thought.
- **Detailed Logging**: Every simulation run is logged to both the console and a unique timestamped file for later analysis.

## Prerequisites

- [Python 3.8+](https://www.python.org/)
- [Ollama](https://ollama.com/) installed and running.
- The Python packages `ollama` and `PyYAML`.

## Setup

1.  **Install and Run Ollama:**
    Follow the instructions on the [Ollama website](https://ollama.com/) to install it for your operating system. After installation, start the Ollama service. In a separate terminal, run:
    ```bash
    ollama serve
    ```

2.  **Pull the necessary LLM models:**
    Pull the models you intend to use in your simulation. The default `settings.yaml` uses `phi`.
    ```bash
    ollama pull phi
    ollama pull gemma3
    ```

3.  **Install Dependencies:**
    Install the required Python packages.
    ```bash
    pip install ollama pyyaml
    ```

## Running the Simulation

To run the simulation, execute the `env.py` script and provide the path to your configuration file.

```bash
python src/simulation.py settings.yaml
```

You can create multiple YAML files to run different simulation experiments.

## Configuration

The simulation is controlled by a YAML file (e.g., `settings.yaml`). Here is an overview of the main parameters:

- `name`: The name of the simulation, used for the output directory.
- `context`: The global context or "world rules" given to every agent.
- `steps`: The number of steps the simulation will run for.
- `agents`: A list of agent objects, each with its own configuration:
    - `id`: A unique identifier for the agent.
    - `model`: The Ollama model that will power this agent (e.g., `phi`).
    - `personality`: A description of the agent's personality, which influences its behavior.
    - `opinion`, `valence`, `trust`, etc.: Custom numerical state parameters for the agent.

### Example `settings.yaml`

```yaml
name: "SocietySim"
context: "You are an AI model designed to interact with other agents in a society simulation."
steps: 3
agents:
  - id: "A"
    model: "phi"
    personality: "Analytical, calm, values evidence."
    opinion: 0.7
    valence: -0.2
    openness: 0.3
    trust: 0.6
    sociability: 0.6
  - id: "B"
    model: "phi"
    personality: "Passionate, expressive, seeks emotional connection."
    opinion: 0.5
    valence: -0.6
    openness: 0.6
    trust: 0.4
    sociability: 0.8
```

## Outputs

All simulation outputs (logs) are saved in the `outputs/` directory. A new sub-directory is created for each simulation based on its `name`, and each run generates a unique, timestamped log file (e.g., `outputs/SocietySim/simulation_20251111_143000.log`).