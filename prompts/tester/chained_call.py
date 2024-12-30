chained_call = '''Your task is to parse the following data into the structured output model with keys "status", "feedback", and "suggestions":

```{ai_response}```

Return the final result strictly as valid JSON with no extra text.
Make sure that "status" is one of: 'builder_error', 'hacker_failure', 'unknown'.'''