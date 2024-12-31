# Bug Pocer

Bug Pocer is a Python-based framework for analyzing, testing, and exploiting Solidity smart contracts. This tool leverages advanced AI-driven pipelines (powered by GPT models) and the Olympix static analysis tool to identify vulnerabilities and validate their exploitability.

## Overview

The tool operates in three main stages:

1. **Builder Stage**:
   - Analyzes the Solidity source code.
   - Generates test cases to validate the contract's behavior.

2. **Hacker Stage**:
   - Uses the test cases and static analysis data to create exploit code.

3. **Tester Stage**:
   - Runs the generated exploits against the contract to validate their effectiveness.

## Features

- AI-driven analysis using OpenAI's GPT models.
- Automated test case generation and refinement.
- Exploit creation tailored to the contract's vulnerabilities.
- Test execution with feedback and suggestions for improvement.

## Installation

### Prerequisites

- Python 3.8+
- `pip` package manager
- Required Python libraries:
  - `langchain_openai`, `langgraph`, `typing_extensions`
  - Additional dependencies listed in `requirements.txt`.
- Olympix static analysis tool (`olympix.exe`).

### Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Olympix is available in your system and note its path.

4. Set up the OpenAI API Key:
   ```bash
   export OPENAI_API_KEY=your_api_key
   ```

## Usage

Run the main script `bug_pocer.py` to analyze Solidity contracts and identify vulnerabilities.

### Command-Line Arguments

```bash
python bug_pocer.py -f <filename.sol> -bt <builder_temp> -ht <hacker_temp> -tt <tester_temp> -n <num_attempts>
```

- `-f, --filename`: Name of the Solidity file to analyze. If not provided, all files in the source directory are analyzed.
- `-bt, --builder_temp`: Temperature for the builder AI model (default: 1).
- `-ht, --hacker_temp`: Temperature for the hacker AI model (default: 1).
- `-tt, --tester_temp`: Temperature for the tester AI model (default: 1).
- `-n, --num_attempts`: Number of attempts to refine tests or exploits before stopping (default: 7).

### Example

To analyze `MyContract.sol` with custom AI temperatures:

```bash
python bug_pocer.py -f MyContract.sol -bt 2 -ht 3 -tt 1 -n 10
```

## Project Structure

```
├── bug_pocer.py               # Main script coordinating all services
├── builder_agent.py           # Logic for building test cases
├── hacker_agent.py            # Logic for creating exploits
├── tester_agent.py            # Logic for validating exploits
├── builder_service.py         # Service wrapper for builder logic
├── hacker_service.py          # Service wrapper for hacker logic
├── tester_service.py          # Service wrapper for tester logic
├── lib/                       # Utility libraries
│   ├── file_lib.py            # File operations utilities
│   ├── log_lib.py             # Logging utilities
│   └── forge_lib.py           # Forge testing utilities
├── forge_bug_pocs/            # Directory for generated files (tests, exploits)
│   ├── src/                   # Solidity source files
│   ├── test/                  # Generated test files
│   ├── exploits/              # Generated exploit files
└── prompts/                   # AI prompt templates
```

## Logs

Logs are automatically generated to capture the workflow. Depending on the success or failure of the process, logs are moved to appropriate folders.

## How It Works

1. **Builder Service**:
   - Reads Solidity source code.
   - Generates test cases using a predefined skeleton and static analysis data.

2. **Hacker Service**:
   - Uses the static analysis data and generated tests to identify vulnerabilities.
   - Creates exploit code tailored to the identified vulnerabilities.

3. **Tester Service**:
   - Runs the exploits using Forge and evaluates their success.
   - Provides feedback for further refinement if the exploit fails.
