import ollama

from core import settings


class LLMTool:

    def __init__(self):

        self.model = settings.OLLAMA_MODEL


    def generate(
        self,
        prompt: str
    ) -> str:

        response = ollama.chat(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            options={
                "num_ctx": 16384
            }
        )


        return response["message"]["content"]