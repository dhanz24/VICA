import os
import sys
import httpx
import base64
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, TextInput

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_security = HTTPBearer()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Backend.VICA.apps.VICA.utils.auth import get_current_user, get_verified_user, decode_token

chat_id = "7ea73edb-9f9f-458c-907e-b966719bcfb8"
CHAT_COMPLETIONS_ENDPOINT = "http://localhost:8000/groq/chat/completions"
RAG_ENDPOINT = "http://localhost:8000/rag/knowledge/query/{chat_id}"

LITERAL_API_KEY = os.getenv("LITERAL_API_KEY")

global_token_store = {}

@cl.header_auth_callback
async def header_auth_callback(headers: Dict) -> Optional[cl.User]:
    """Validate JWT tokens from headers or query parameters."""
    auth_header = headers.get("Authorization", "")
    token = None

    print("Headers:", headers)
    print("Authorization Header:", auth_header)
    
    # Periksa token dari Authorization header
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # Jika tidak ada header, ambil token dari query parameter
    if not token:
        
        referer = headers.get("Referer", "")
        query_params = parse_qs(urlparse(referer).query)
        token = query_params.get("token", [None])[0]

        print("Token from query parameter:", token)

    if not token:
        token = global_token_store.pop("default", None)


    if not token:
        raise RuntimeError("Token not provided.")
    
    try:
        user = get_current_user(request=None, manual_token=token)
        if user:
            global_token_store["default"] = token
            return cl.User(identifier=user.name, metadata={"id" : user.id, "name":user.name, "role":user.role, "email":user.email, "token":token})
        else:
            raise RuntimeError("Invalid token.")
    except Exception as e:
        raise RuntimeError(f"Authentication failed: {str(e)}")



@cl.on_chat_start
async def on_chat_start():
    """Retrieve and validate token from query parameter, and send chat settings."""
    user = cl.user_session.get("user")

    # Ambil http_referer
    http_referer = cl.user_session.get("http_referer", "")
    if not http_referer:
        await cl.Message(content="Access denied: Missing referrer.").send()
        raise cl.StopExecution("No referrer found.")

    # Parse URL untuk mendapatkan query parameter
    parsed_url = urlparse(http_referer)
    query_params = parse_qs(parsed_url.query)

    # Ambil token dari query parameter
    token = query_params.get("token", [None])[0]  # Ambil token pertama jika ada

    if not token:
        token = user.metadata.get("token")
        print (f'Token from user session{token}')
        
    if not token:
        await cl.Message(content="Access denied: Token is missing in the URL.").send()
        raise cl.StopExecution("Token missing in query parameters.")

    # Validasi token
    try:
        decoded_token = decode_token(token)  # Fungsi validasi token
        cl.user_session.set("user_data", decoded_token)  # Simpan data user ke sesi
        cl.user_session.set("auth_token", token)  # Simpan token ke sesi
    except Exception as e:
        await cl.Message(content=f"Invalid token: {e}").send()
        raise cl.StopExecution("Invalid token.")

    # Kirim pengaturan chat (Chat Settings)
    settings = await cl.ChatSettings(
        [
            Switch(id="RAG", label="Enable RAG", initial=True),
            Slider(
                id="Temperature",
                label="LLM - Temperature",
                initial=0.7,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="Max_Tokens",
                label="LLM - Max Tokens",
                initial=500,
                min=100,
                max=2000,
                step=100,
            ),
            TextInput(
                id="System_Prompt",
                label="System Prompt",
                placeholder="Describe the AI's identity, capabilities, or specific instructions here...",
                initial="You are a helpful and knowledgeable assistant. Answer questions clearly and concisely.", 
                multiline=True,  # Allow for multiline input
                rows=5  # Set the height of the input box
            ),
        ]
    ).send()


async def fetch_rag_response(question: str, chat_id: str) -> str:
    """Function to query the RAG service and retrieve knowledge."""
    url = RAG_ENDPOINT.format(chat_id=chat_id)
    payload = {"question": question}

    # Ambil token dari session
    auth_token = cl.user_session.get("auth_token")
    if not auth_token:
        return "Authentication token is missing. Please restart the session."

    headers = {"Authorization": f"Bearer {auth_token}"}
    
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
    # Ambil token dari session
    auth_token = cl.user_session.get("auth_token")
    if not auth_token:
        return "Authentication token is missing. Please restart the session."

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"}

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
    """Process user message based on the chat settings."""
    settings = cl.user_session.get("chat_settings", {})
    user_question = message.content.strip()

    # Dapatkan pengaturan RAG dan system prompt dari chat settings
    use_rag = settings.get("RAG", True)
    temperature = settings.get("Temperature", 0.7)
    max_tokens = settings.get("Max_Tokens", 500)
    system_prompt = settings.get("System_Prompt", "You are a helpful and knowledgeable assistant.")

    # Logic based on RAG setting
    if use_rag:
        # Fetch additional knowledge from RAG
        rag_response = await fetch_rag_response(question=user_question, chat_id=chat_id)
        print("RAG Response:", rag_response)
        llm_prompt = f"""{system_prompt}

User Question:
{user_question}

Retrieved Knowledge:
{rag_response}

Instructions:
Using the information from the 'Retrieved Knowledge' section above, answer the user's question in a clear and informative way."""
    else:
        # Use only LLM without RAG
        llm_prompt = f"""{system_prompt}

User Question:
{user_question}

Instructions:
Answer the user's question in a clear and informative way. Use general knowledge if applicable."""

    # Prepare the messages array for LLM
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": llm_prompt
        }
    ]

    # Send request to the backend for chat completion
    api_response = await fetch_chat_completion(messages=messages, temperature=temperature, max_tokens=max_tokens)

    # Display the response to the user
    await cl.Message(content=api_response).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """Update settings dynamically."""
    cl.user_session.set("chat_settings", settings)
    print("Updated settings:", settings)
