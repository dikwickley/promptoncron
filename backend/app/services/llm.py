from __future__ import annotations

import json
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt, wait_fixed
from tenacity import RetryError
from tenacity import retry_if_not_exception_type

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.services.llm_schema import TableResult


class LLMConfigError(RuntimeError):
    pass


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mock_llm(*, task_name: str) -> TableResult:
    return TableResult(
        columns=[
            {"key": "timestamp", "label": "Timestamp", "type": "date"},
            {"key": "task", "label": "Task", "type": "string"},
        ],
        rows=[{"timestamp": _utcnow_iso(), "task": task_name}],
        summary="mock result",
    )


def _build_langchain_model(*, provider: str, model: str):
    settings = get_settings()
    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigError("OPENAI_API_KEY not set (LLM_PROVIDER=openai)")
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=1,
            max_tokens=2000,
        )

    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise LLMConfigError("DEEPSEEK_API_KEY not set (LLM_PROVIDER=deepseek)")
        return ChatOpenAI(
            model=model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.0,
            max_tokens=2000,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMConfigError("GEMINI_API_KEY not set (LLM_PROVIDER=gemini)")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0,
            max_output_tokens=2000,
        )

    raise RuntimeError(f"Unsupported LLM_PROVIDER={provider}")


def generate_structured_table(
    *,
    system_prompt: str,
    user_prompt: str,
    task_name: str,
) -> tuple[TableResult, dict | None, str | None]:
    """
    Returns: (TableResult, token_usage, llm_model)
    """
    settings = get_settings()
    provider = (settings.llm_provider or "mock").lower()

    if provider == "mock":
        return _mock_llm(task_name=task_name), None, None

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
        # Don't retry on schema/empty-output errors; those are prompt/model behavior, not transient.
        retry=retry_if_not_exception_type((LLMConfigError, ValidationError, ValueError)),
    )
    def _attempt() -> TableResult:
        llm = _build_langchain_model(provider=provider, model=settings.default_llm_model)

        # Enforce JSON via parser instructions + parse.
        # NOTE: We intentionally avoid model-native structured output here because
        # some providers/tooling tend to return `{}` for dict-typed fields like rows[*],
        # resulting in "empty tables". The explicit JSON prompt produces better filled values.
        parser = PydanticOutputParser(pydantic_object=TableResult)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}\n\n{format_instructions}"),
                ("human", "{user_prompt}"),
            ]
        )
        chain = prompt | llm
        msg = chain.invoke(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        text = getattr(msg, "content", "") or ""
        return parser.parse(text)

    table = _attempt()
    return table, None, settings.default_llm_model


def stringify_for_web_results(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


