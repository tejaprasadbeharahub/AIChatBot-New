from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ai.llm import get_chat_model
from app.schemas.chat import ChatMessage


MEMORY_SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the provided conversation history from the current chat thread "
    "to answer follow-up questions. If the user already shared personal details in this thread "
    "(for example their name), prefer that context in your answer."
)


def _to_langchain_messages(history: list[ChatMessage], message: str) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=MEMORY_SYSTEM_PROMPT)]

    for item in history:
        if item.role == "system":
            messages.append(SystemMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))

    messages.append(HumanMessage(content=message))
    return messages


def _normalize_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    return str(content)


def generate_reply(message: str, history: list[ChatMessage], temperature: float = 0.2) -> str:
    model = get_chat_model(temperature=temperature)
    try:
        result = model.invoke(_to_langchain_messages(history=history, message=message))
        return _normalize_content(result.content)
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()
        if "api key" in lowered and ("invalid" in lowered or "incorrect" in lowered or "unauthorized" in lowered):
            raise ValueError("Invalid LITELLM_API_KEY. Please use a valid key for your LiteLLM proxy.") from exc
        if "key_model_access_denied" in lowered or "not allowed to access model" in lowered:
            raise ValueError(
                "Your LiteLLM key does not have access to this model. Set LLM_MODEL=gemini/gemini-2.5-flash in .env."
            ) from exc
        raise
