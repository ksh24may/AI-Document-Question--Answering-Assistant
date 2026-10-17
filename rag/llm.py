
import os
from google import genai


class GeminiLLM:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt):
        try:
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt
            )

            if not response or not response.text:
                return "Gemini returned an empty response."

            return response.text.strip()

        except Exception as error:
            print(f"Gemini generation error: {error}")
            return (
                "Unable to generate an answer right now. "
                "Please try again later."
            )
