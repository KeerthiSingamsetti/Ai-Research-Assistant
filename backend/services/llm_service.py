import asyncio
import google.generativeai as genai

from backend.config import settings


class GeminiService:

    def __init__(self):

        print("Gemini API Key:", settings.GEMINI_API_KEY)

        genai.configure(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

    async def generate(
        self,
        prompt: str,
        retries: int = 3
    ) -> str:

        for attempt in range(retries):

            try:

                response = self.model.generate_content(
                    prompt
                )

                text = response.text.strip()

                if text:
                    return text

            except Exception as e:

                print(
                    f"GEMINI ERROR (Attempt {attempt + 1}):",
                    str(e)
                )

                if attempt == retries - 1:
                    return (
                        f"Gemini Error: {str(e)}"
                    )

                await asyncio.sleep(1)

        return "Failed to generate answer."


gemini_service = GeminiService()