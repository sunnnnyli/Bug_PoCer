reattempt = '''Your exploit failed the test case. The forge test output is:
```{forge_test_output}```

An expert in Solidity smart contracts and testing frameworks gave you the following error data analysis:
```{test_analysis}```

Additionally, here is the static-analysis report from olympix:
```{analysis_data}```

Objectives:
1. Identify the cause of failure by reviewing the forge output and the analysis data.
2. Update your exploit contract to address the issues and pass all assertions.
3. Return your revised exploit in strict JSON format:
{{
  "my_attempt": "<full updated exploit code>",
  "my_explanation": "<explanation>"
}}

No extra text outside the JSON object. No Markdown code fences.'''