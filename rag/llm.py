import os
import time

from google import genai


class GeminiLLM:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite"
        )

    def generate(self, prompt):

        max_retries = 3

        for attempt in range(max_retries):

            try:
                print(
                    f"Gemini request: "
                    f"{attempt + 1}/{max_retries}"
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )

                if not response or not response.text:
                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                print("Gemini response successful.")

                return response.text

            except Exception as e:

                error_message = str(e)

                print("Gemini error:")
                print(error_message)

                temporary_error = (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                    or "high demand" in error_message.lower()
                    or "capacity" in error_message.lower()
                )

                if not temporary_error:
                    raise

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        "Gemini is currently unavailable. "
                        "Please try again later."
                    )

                wait_time = 3 * (2 ** attempt)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)