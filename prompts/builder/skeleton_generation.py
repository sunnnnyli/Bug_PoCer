skeleton_generation = '''You are an expert Solidity tester and security researcher. I have a vulnerable Solidity contract in my `src` folder:
```{source_code}```

Here is the static analysis report from olympix:
```{analysis_data}```

I have a separate exploit contract `{filename}Exploit.sol` in the `exploits` folder where I wrote my exploit in a `hack()` method.
I want a test that sets up my exploit contract and calls `hack()` and confirms my exploit truly compromises this contract.

Specifically, the test should:
1. Fail if the exploit is **not** successful.
2. Pass only if the exploit actually exploits the vulnerable contract.

Return **only** a valid JSON object in plain text, with this format:
{{
  \"my_test_code\": \"<Solidity test contract code>\",
  \"my_explanation\": \"<how the test verifies the vulnerability is exploited>\"
}}

Here is the current test skeleton that I want you to follow:
```{test_skeleton}```

**Requirements**:
- Provide no text outside the JSON.
- The JSON must be strictly valid (properly escaped quotes, etc.).
- The test should be generic enough so that any exploit can prove the vulnerability but fail if no exploit or an incorrect exploit is executed.
- Make sure running this test (e.g., via `forge test`) will clearly indicate success only if the exploit is truly effective.
- Only set up the attacker contract. Do not create the attacker contract.
- Only create the test contract.
- Make sure to import my source code from "../src/{filename}.sol"
- Make sure to import my exploit code from "../exploits/{filename}Exploit.sol"'''