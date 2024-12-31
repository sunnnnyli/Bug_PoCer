analyze_test = '''You are an expert in Solidity smart contracts and testing frameworks.

You are working with 3 contracts (the source contract, an exploit contract, and a test contract) and the forge output after compiling/executing them.

Here is the source contract: `{source_filename}`
```
{source_contract}
```

Here is the exploit contract: `{exploit_filename}`
```
{exploit_contract}
```

And here is the test contract: `{test_filename}`
```
{test_contract}
```

Analyze the following Forge test output:
```
{forge_output}
```

Based on that output:
1. Determine Failure Reason:
   - `"builder_error"`: Test compilation error or test file issue.
   - `"hacker_failure"`: Exploit compilation error, test cases failed, or exploit file issue.
   - `"unknown"`: If none of the above apply.
2. Provide detailed feedback.
3. Provide specific code changes or strategies to fix the issue.

Respond with a JSON object following this structure:
{{
    \"status\": \"<status>\",
    \"feedback\": \"<detailed feedback>\",
    \"suggestions\": \"<actionable suggestions>\"
}}

**Requirements**:
- Provide no text outside the JSON.
- The JSON must be strictly valid (properly escaped quotes, etc.).
- Return the answer in plain text (no Markdown code fences).
- <status> is one of: 'builder_error', 'hacker_failure', 'unknown'.'''