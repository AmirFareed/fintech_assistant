import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto").strip().lower()
QEHWA_MODEL_ID = os.environ.get("QEHWA_MODEL_ID", "junaid008/qehwa-pashto-llm")
QEHWA_DEVICE = os.environ.get("QEHWA_DEVICE", "auto").strip().lower()
QEHWA_MAX_NEW_TOKENS = int(os.environ.get("QEHWA_MAX_NEW_TOKENS", "300"))
QEHWA_TEMPERATURE = float(os.environ.get("QEHWA_TEMPERATURE", "0.3"))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

QEHWA_TEMPLATE = """Below is an instruction in Pashto or English. Write a detailed response in Pashto.

### Instruction:
{}

### Response:
"""

_groq_client = Groq(api_key=GROQ_API_KEY)
_qehwa_runtime = None

_EMPTY_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _has_groq_credentials() -> bool:
    return bool(GROQ_API_KEY)


def _select_provider(target_language: str) -> str:
    if LLM_PROVIDER in {"groq", "qehwa"}:
        return LLM_PROVIDER
    if _has_groq_credentials():
        return "groq"
    return "qehwa" if target_language == "ps" else "groq"


def _generate_with_groq(
    system_prompt: str,
    user_query: str,
    history: list[dict] | None = None,
) -> tuple[str, dict]:
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()
    usage = _EMPTY_USAGE.copy()
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens or 0,
            "completion_tokens": response.usage.completion_tokens or 0,
            "total_tokens": response.usage.total_tokens or 0,
        }
    return text, usage


def _load_qehwa_runtime():
    global _qehwa_runtime

    if _qehwa_runtime is not None:
        return _qehwa_runtime

    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Qehwa support requires `torch` to be installed."
        ) from exc

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Qehwa support requires `transformers` and `accelerate` to be installed."
        ) from exc

    model_kwargs = {}
    if QEHWA_DEVICE == "cpu":
        model_kwargs["dtype"] = torch.float32
        model_kwargs["device_map"] = "cpu"
    else:
        model_kwargs["dtype"] = torch.bfloat16
        model_kwargs["device_map"] = "auto"

    tokenizer = AutoTokenizer.from_pretrained(QEHWA_MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(QEHWA_MODEL_ID, **model_kwargs)

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    _qehwa_runtime = (tokenizer, model)
    return _qehwa_runtime


def _get_model_input_device(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        try:
            import torch
        except ImportError:
            return "cpu"
        return torch.device("cpu")


def _generate_with_qehwa(prompt: str) -> tuple[str, dict]:
    tokenizer, model = _load_qehwa_runtime()
    formatted_prompt = QEHWA_TEMPLATE.format(prompt)
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    input_device = _get_model_input_device(model)
    inputs = {key: value.to(input_device) for key, value in inputs.items()}

    outputs = model.generate(
        **inputs,
        max_new_tokens=QEHWA_MAX_NEW_TOKENS,
        temperature=QEHWA_TEMPERATURE,
        do_sample=QEHWA_TEMPERATURE > 0,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "### Response:" in decoded:
        return decoded.split("### Response:")[-1].strip(), _EMPTY_USAGE.copy()
    return decoded.strip(), _EMPTY_USAGE.copy()


def generate_response(
    system_prompt: str,
    user_query: str,
    target_language: str = "en",
    history: list[dict] | None = None,
) -> tuple[str, dict]:
    """Generate a response from the LLM.

    Returns (response_text, usage_stats) where usage_stats has keys:
    prompt_tokens, completion_tokens, total_tokens.
    """
    provider = _select_provider(target_language)

    try:
        if provider == "groq":
            return _generate_with_groq(system_prompt, user_query, history=history)
        # Qehwa: flatten history into prompt (no native multi-turn support)
        full_prompt = system_prompt + "\n\n" + user_query
        return _generate_with_qehwa(full_prompt)
    except Exception:
        if LLM_PROVIDER == "auto":
            fallback = "qehwa" if provider == "groq" else "groq"
            if fallback == "groq":
                return _generate_with_groq(system_prompt, user_query, history=history)
            full_prompt = system_prompt + "\n\n" + user_query
            return _generate_with_qehwa(full_prompt)
        raise
