# bug_pocer

**bug_pocer** is a Solidity exploit framework designed to solve security challenges from the [Ethernaut](https://ethernaut.openzeppelin.com/) game. The project leverages the OpenAI library to assist in exploit development and includes a logging mechanism for tracking progress and results.

## Features

- **Exploit File Generation**: Write and test Solidity exploit files to bypass Ethernaut levels.
- **OpenAI Integration**: Uses the OpenAI API to help analyze and refine exploit strategies.
- **Detailed Logging**: Outputs results to a file with annotations on:
  - Compile success
  - Exploit correctness
  - Total run count
  - Forge output

## Getting Started

### Prerequisites

- **Solidity** and **Foundry** (for testing)
- **OpenAI API key** (if not embedded in your environment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sunnnnyli/bug_pocer.git
   cd bug_pocer
   ```

2. Install dependencies:
   ```bash
   # Install Foundry
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

3. Set up your environment:
   - Add your OpenAI API key in the environment variables or in the script configuration.

### Usage

1. **Run an exploit file**: To attempt an exploit on a specific Ethernaut level, run:
   ```bash
   python bug_pocer.py --chal <level_name>
   ```

   For example, to attempt an exploit on the Fallback level, run:
   ```bash
   python bug_pocer.py --chal Fallback
   ```

2. **Check logs**: View the `logs/output.txt` file for details on the last run, including:
   - Compile success
   - Correctness of the exploit
   - Run count
   - Forge output for each exploit attempt
