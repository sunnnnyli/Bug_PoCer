hacker_first_attempt = '''You are an expert smart contract auditor. Your task is to identify vulnerabilities in the following smart contract and write an exploit targeting these weaknesses. Focus specifically on common Solidity issues such as reentrancy, unchecked external calls, integer overflow/underflow, and authorization flaws. Here is the contract to analyze:

```{victim_sol_content}```.

Once you've identified a vulnerability, complete the exploit contract to exploit this weakness. Here is the contract skeleton for your exploit: 

```{exploit_contract_skeleton}```.

To validate your exploit, it must pass all assertions in the following test case:

```{test_case_contract}```.

Please note that you are working within a gas limit, so prioritize an efficient and optimized exploit structure. You may add new functions or contracts as needed to accomplish this.

**Output format**: Provide only a JSON object in the following format:

{{"my_attempt": "<your full exploit code>", "my_explanation": "<your explanation>"}}

Please ensure:
- No additional text outside the JSON.
- JSON format is strictly adhered to, including escaping quotes and backslashes where necessary.
- Response is in plain text without code block formatting.'''
