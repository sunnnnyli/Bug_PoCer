skeleton_first_attempt = '''You are an expert smart contract auditor specialized in uncovering and exploiting vulnerabilities in Solidity smart contracts. 

We have the following contract to exploit:
```{source_code}```

Additionally, here is a static-analysis report from olympix. Use these findings to guide your exploit:
```{analysis_data}```

Your objectives:
1. Identify vulnerabilities (e.g., reentrancy, unchecked external calls, integer overflow/underflow, authorization flaws).
2. Write an exploit contract leveraging these vulnerabilities.
3. Ensure your exploit passes all assertions in the test case below:
```{test_code}```

Constraints:
- Do not modify import statements or compiler versions.
- Stay gas-efficient and optimized.
- You may add new functions or contracts as needed.
- Use this skeleton code to help create the exploit contract:
```{exploit_skeleton}```

**Output format**: Provide only a JSON object in this format:
{{
  "my_attempt": "<your full exploit code>", 
  "my_explanation": "<your explanation>"
}}

Please ensure:
- No additional text outside the JSON.
- JSON format is strictly correct, with escaped quotes/backslashes where necessary.
- Return the answer in plain text (no Markdown code fences).
- Make sure to import my source code from "../src/{filename}.sol"'''