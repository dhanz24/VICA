import chainlit as cl
import httpx
import base64

chat_id = "7ea73edb-9f9f-458c-907e-b966719bcfb8"
CHAT_COMPLETIONS_ENDPOINT = "http://localhost:8000/groq/chat/completions"
RAG_ENDPOINT = "http://localhost:8000/rag/knowledge/query/{chat_id}"
AUTH = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjllZGE0ZmE2LTVlOGMtNGVmYy1iNjIwLWMxMmRhOTQ2NjE0MyIsIm5hbWUiOiJhZG1pbiIsImV4cCI6MTczMjc1ODA0NH0.lDmS9sbEbGO_1pRItSdVx37FTHNJbEMvlnT-x67iH5Y"

@cl.set_chat_profiles
async def chat_profile():
    """Define chat profiles for RAG and Non-RAG modes."""
    return [
        cl.ChatProfile(
            name="With RAG",
            markdown_description="This chat will use **RAG (Retrieval-Augmented Generation)** to enhance responses with additional knowledge.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="Without RAG",
            markdown_description="This chat will **not use RAG**, and responses will rely solely on the LLM.",
            icon="https://picsum.photos/250",
        ),
    ]

@cl.on_chat_start
async def on_chat_start():
    """Retrieve and confirm the selected chat profile."""
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"You have selected the **{chat_profile}** chat profile. Let's get started!"
    ).send()

async def fetch_rag_response(question: str, chat_id: str) -> str:
    """Function to query the RAG service and retrieve knowledge."""
    url = RAG_ENDPOINT.format(chat_id=chat_id)
    payload = {"question": question}
    headers = {"Authorization": f"Bearer {AUTH}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data.get("result", "No result found")
        
        except httpx.TimeoutException as e:
            return "Request timed out while connecting to the RAG API."
        
        except httpx.RequestError as e:
            return f"Request error: {e}"

        except Exception as e:
            return f"Unexpected error: {e}"

async def fetch_chat_completion(messages, model: str = "llama-3.2-11b-vision-preview", max_tokens: int = 500, temperature: float = 0.7):
    """Function to send requests to the backend."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AUTH}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(CHAT_COMPLETIONS_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            return f"Error while connecting to the API: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

@cl.on_message
async def main(message: cl.Message):
    """Process user message based on the selected chat profile."""
    chat_profile = cl.user_session.get("chat_profile")  # Get the selected profile
    user_question = message.content.strip()

    # Logic based on the chat profile
    if chat_profile == "With RAG":
        # Fetch additional knowledge from RAG
        rag_response = await fetch_rag_response(question=user_question, chat_id=chat_id)
        print("RAG Response:", rag_response)
        llm_prompt = f"""User Question:
{user_question}

Retrieved Knowledge:
{rag_response}

Instructions:
Using the information from the "Retrieved Knowledge" section above, answer the user's question in a clear and informative way."""
    else:
        # Use only LLM without RAG
        llm_prompt = f"""User Question:
{user_question}

Instructions:
Answer the user's question in a clear and informative way. Use general knowledge if applicable."""

    # Prepare the messages array for LLM
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": llm_prompt}
            ]
        }
    ]

    # Add file attachments if provided
    if message.elements:
        file = message.elements[0]
        with open(file.path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")
        file_type = file.mime
        messages[0]["content"].append(
            {
                "type": "image_url" if file_type.startswith("image") else "pdf_url",
                "image_url" if file_type.startswith("image") else "pdf_url": {
                    "url": f"data:{file_type};base64,{file_data}"
                }
            }
        )

    # Send request to the backend for chat completion
    api_response = await fetch_chat_completion(messages=messages)

    # Display the response to the user
    await cl.Message(content=api_response).send()
