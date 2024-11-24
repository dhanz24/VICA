from groq import Groq
from pdf2image import convert_from_bytes
import base64
from fastapi import UploadFile
from io import BytesIO
from PIL import Image


class PDFService:
    def __init__(self, groq: Groq) -> None:
        self._client = groq
        self._client.base_url = "https://api.groq.com/"
        

    async def describe_pdf(self, file: UploadFile) -> str:
        if file.content_type != "application/pdf":
            raise ValueError("File must be a PDF.")

        print(self._client.base_url)

        pdf_data = await file.read()
        pil_images = convert_from_bytes(pdf_data)
        base64_images = [self._convert_image_to_base64(image) for image in pil_images]

        descriptions = [
            self._describe_image(base64_image, page_number=i + 1)
            for i, base64_image in enumerate(base64_images)
        ]

        return "\n".join(descriptions)

    def _convert_image_to_base64(self, pil_image: Image.Image) -> str:
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _describe_image(self, base64_image: str, page_number: int) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                            This image may contain visual data like tables, charts, or graphs, as well as textual descriptions. Please follow these steps:
                            1. **Analyze** the visual data for any significant trends, patterns, or key takeaways.
                            2. **Summarize** important insights, such as how the data changes over time or across categories. Note any spikes, drops, or shifts in the data.
                            3. Identify **anomalies**, **outliers**, or unusual data points and mention their potential significance.
                            4. **Ignore** irrelevant elements (e.g., images of people) unless they directly contribute to understanding the data.
                            5. Focus on **describing the data** in terms of key trends and insights, rather than just explaining what is visible.
                            6. Provide a **comprehensive overview** that includes an analysis of both the visual content and the article’s text (if applicable).
                            7. Only provide answers based on available information.
                            8. Do not explicitly provide the answer step by step.
                        """,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ]
        
        completion = self._client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )

        image_description = completion.choices[0].message.content
        return f"Page {page_number} description:\n{image_description}\n"
