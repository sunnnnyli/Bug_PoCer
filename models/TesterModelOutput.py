class TesterModelOutput():
    def __init__(self, test_code: str, explanation: str):
        self.test_code = test_code
        self.explanation = explanation
    def as_dict(self):
        return {
            "test_code": self.test_code,
            "explanation": self.explanation,
        }
