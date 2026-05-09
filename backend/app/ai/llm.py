from langchain_openai import ChatOpenAI

from app.core.config import settings


DEFAULT_MODEL = "gemini/gemini-2.5-flash"
DEFAULT_LITELLM_PROXY_URL = "http://litellm.amzur.com:4000"


def resolve_model_name() -> str:
	model_name = settings.llm_model or DEFAULT_MODEL
	if model_name == "gemini-2.0-flash":
		return "gemini/gemini-2.5-flash"
	return model_name


def get_chat_model(temperature: float = 0.2) -> ChatOpenAI:
	api_key = settings.litellm_api_key
	if not api_key:
		raise ValueError("Missing LITELLM_API_KEY. Set LITELLM_API_KEY in .env")

	model_name = resolve_model_name()
	proxy_url = (settings.litellm_proxy_url or DEFAULT_LITELLM_PROXY_URL).rstrip("/")
	base_url = proxy_url if proxy_url.endswith("/v1") else f"{proxy_url}/v1"

	return ChatOpenAI(
		model=model_name,
		api_key=api_key,
		base_url=base_url,
		temperature=temperature,
	)
