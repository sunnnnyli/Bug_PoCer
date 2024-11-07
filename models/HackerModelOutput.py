class HackerModelOutput():
    def __init__(self, solidity_attempt: str, explanation: str):
        self.solidity_attempt = solidity_attempt
        self.explanation = explanation
    def as_dict(self):
        return {
            "solidity_attempt": self.solidity_attempt,
            "explanation": self.explanation,
        }
