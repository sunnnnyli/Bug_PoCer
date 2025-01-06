# Bug Pocer

Bug Pocer is a Python-based framework for analyzing, testing, and exploiting Solidity smart contracts. This tool leverages AI-driven pipelines and the Olympix static analysis tool to identify vulnerabilities and validate their exploitability.

## Overview

Bug Pocer operates in three main stages:

1. **Builder Stage**: Analyzes Solidity source code and generates test cases.
2. **Hacker Stage**: Uses test cases and analysis data to create exploit code.
3. **Tester Stage**: Validates exploits against the contract.

## Features

- AI-driven test case generation and refinement.
- Exploit creation and validation tailored to vulnerabilities.
- Iterative retries for refining results.
- Import parsing for comprehensive analysis.
- Modular architecture for streamlined operations.

## Services and Agents

### Services

The services act as middleware, streamlining communication between the main script (`bug_pocer.py`) and agents.

- **Builder Service**: Manages test generation via the `BuilderAgent` and handles file operations.
- **Hacker Service**: Facilitates exploit creation through the `HackerAgent`.
- **Tester Service**: Validates exploits using the `TesterAgent` and manages iterative retries.

### Agents

The agents implement core logic:

- **Builder Agent**: Generates Solidity test cases using AI.
- **Hacker Agent**: Creates and refines exploit code for vulnerabilities.
- **Tester Agent**: Executes and validates exploits, providing feedback for retries.

## Installation

### Prerequisites

- Python 3.8+
- Required Python libraries listed in `requirements.txt`.
- Olympix static analysis tool (`olympix.exe`).

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure Olympix is available in your system.
4. Set up the OpenAI API Key:
   ```bash
   export OPENAI_API_KEY=your_api_key
   ```

## Configuration

Default parameters are stored in `config.json`:

```json
{
    "builder_temp": 1,
    "hacker_temp": 1,
    "tester_temp": 1,
    "filename": null,
    "num_attempts": 5,
    "olympix_path": "/path/to/olympix",
    "forge_bug_pocs_dir": "/path/to/forge_bug_pocs"
}
```

## Usage

Run the main script to analyze Solidity contracts:

```bash
python bug_pocer.py -f <filename.sol> -bt <builder_temp> -ht <hacker_temp> -tt <tester_temp> -n <num_attempts> -c <config.json>
```

Examples:

- **Default config:**
  ```bash
  python bug_pocer.py
  ```
- **Custom config file:**
  ```bash
  python bug_pocer.py -c custom_config.json
  ```
- **Override parameters:**
  ```bash
  python bug_pocer.py -c config.json -f MyContract.sol
  ```

## Project Structure

```
├── bug_pocer.py               # Main script coordinating all services
├── services/                  # Middleware for agent interaction
│   ├── builder_service.py     # Handles test generation
│   ├── hacker_service.py      # Manages exploit creation
│   └── tester_service.py      # Executes and validates exploits
├── agents/                    # Core logic implementation
│   ├── builder/               # Test generation
│   ├── hacker/                # Exploit creation
│   └── tester/                # Exploit validation
├── lib/                       # Utility libraries
├── forge_bug_pocs/            # Generated files
│   ├── src/                   # Solidity source files
│   ├── test/                  # Test files
│   └── exploits/              # Exploit files
└── logs/                      # Log files
    ├── successes/             # Successful operations
    └── failures/              # Failed operations
```