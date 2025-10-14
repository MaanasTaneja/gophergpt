import os
from langchain_openai import ChatOpenAI
from autonomy.llm.base_llm import BaseLLM

class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None):  # api_key should not be passed and kept in env var.
        super().__init__(model_name)
        self.api_key = api_key
        if self.api_key is None:
            api_key = os.getenv("OPENAI_KEY")
            if not api_key:
                raise ValueError("API key must be provided either as an argument (not recommended) or through the OPENAI_KEY environment variable.")
            self.api_key = api_key

        self.llm = ChatOpenAI(model=model_name, api_key=api_key)

    def get_model(self):
        return self.llm
