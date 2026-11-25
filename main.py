import os
from dotenv import load_dotenv

load_dotenv()   

from langfuse import observe, get_client
from langfuse.openai import OpenAI

from prompts import SYSTEM_PROMPT

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Try in order; if one is rate-limited or removed, fall back to the next.
# Replace with current ":free" model IDs from openrouter.ai/models
MODELS = [
    "google/gemini-4-hydrogen",
]

@observe()
def ask(system, history):
    last_err = None
    for model in MODELS:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}] + history,
                max_tokens=2000,
                extra_body={"reasoning": {"effort": "low"}},
            )
            text = r.choices[0].message.content
            if text and text.strip():
                return text.strip()
            print(f"[{model} returned an empty reply (finish_reason={r.choices[0].finish_reason})]")
            # print(r.choices[0].finish_reason)
            return r.choices[0].message.content
        except Exception as e:
            last_err = e
            print(f"[{model} failed: {e}]")
    raise last_err

def chat(level="JLPT N3", lang="English", topic="favorite food"):
    system = SYSTEM_PROMPT.format(level=level, lang=lang)
    history = [{"role": "user", "content": f"(start the conversation about: {topic})"}]
    text = ask(system, history)
    history.append({"role": "assistant", "content": text})
    print(f"\n先生: {text}\n")

    while True:
        user_input = input("あなた: ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            print("またね！")
            break
        history.append({"role": "user", "content": user_input})
        history = history[-20:]  # keep recent turns only
        text = ask(system, history)
        history.append({"role": "assistant", "content": text})
        print(f"\n先生: {text}\n")

if __name__ == "__main__":
    try:
        chat()
    finally:
        get_client().flush()