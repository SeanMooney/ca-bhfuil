# -*- coding: utf-8 -*-
import os
import sys

import dotenv
import langchain_ollama as lo


def main():
    dotenv.load_dotenv()
    host = os.environ.get("OLLAMA_HOST")
    model = os.environ.get("OLLAMA_MODEL")

    if not all((host, model)):
        sys.exit(
            f"OLLAMA_HOST: {host} and OLLAMA_MODEL: {model} must be set in the environment"
        )

    llm = lo.ChatOllama(model=model, base_url=host, temperature=0)
    messages = [
        (
            "system",
            "You are a helpful assistant that translates "
            "English to French. Translate the user sentence.",
        ),
        ("human", "I love programming."),
    ]
    ai_msg = llm.invoke(messages)
    print(ai_msg.content)


if __name__ == "__main__":
    main()
