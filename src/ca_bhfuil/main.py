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
            "You are an expert at analyzing git repos, change trackers(launchpad, jira, github), "
            "source hosting platforms (gerrit, github, gitlab) and packaging systems like brew and konflux. "
            "When asked, you excel at find commits by title, git sha, gerrit change id, issue tracker reference "
            "or other metadata available in a commit message. Once found you can analyse the the content of the commit"
            "to find links to bug or features, symmetrize the issue resolved, what branches and tags the change is "
            "included in and other useful information like what package, container the fix is available in or any"
            "relevant release notes, documentation or specifications related to the bug or feature addressed. "
            "You never make up information about a change you do not find or have no data on."
            "When you provide a summary you alway explain your reasoning and cite your sources"
            "providing links to supporting data when possible.",
        ),
        (
            "human",
            "can you help me find a commit in https://opendev.org/openstack/nova and tell me about it?"
            "change-id: I63208c7bd5f9f4c3d5e4a40bd0f6253d0f042a37",
        ),
    ]
    ai_msg = llm.invoke(messages)
    print(ai_msg.content)


if __name__ == "__main__":
    main()
