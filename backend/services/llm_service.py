from google import genai

from backend.config import settings


class GeminiService:
    """
    Gemini API wrapper using the new google-genai SDK.
    """

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    async def generate(
        self,
        prompt: str
    ) -> str:

        try:

            response = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=prompt
            )

            if response and response.text:
                return response.text.strip()

            return "No response generated."

        except Exception as e:

            return (
                f"Generation error: {str(e)}"
            )


gemini_service = GeminiService()