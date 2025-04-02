# -*- coding: utf-8 -*-
import os
import sys
import typing as ty

import dotenv
import langchain_ollama as lo
import langchain_text_splitters as lts

from langchain_community import vectorstores
from langchain_core import documents
from langgraph import graph


# Define state for application
class State(ty.TypedDict):
    question: str
    context: ty.List[documents.Document]
    answer: str
    db: vectorstores.VectorStore
    llm: lo.ChatOllama


# Define application steps
def retrieve(state: State) -> dict:
    retrieved_docs = state["db"].similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State) -> dict:
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    # Define prompt for question-answering
    prompt = f"""
    Question: {state["question"]}
    Context: {docs_content}
    Answer:
    """
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
        ("human", prompt),
    ]
    response = state["llm"].invoke(messages)
    return {"answer": response.content}


def main():
    dotenv.load_dotenv()
    host = os.environ.get("OLLAMA_HOST")
    model = os.environ.get("OLLAMA_MODEL")
    embed_model = os.environ.get("EMBEDDING_MODEL")

    if not all((host, model)):
        sys.exit(
            f"OLLAMA_HOST: {host}, OLLAMA_MODEL: {model} and "
            f"EMBEDDING_MODEL: {embed_model} must be set in the environment"
        )

    llm = lo.ChatOllama(model=model, base_url=host, temperature=0)
    question = (
        "can you help me find a commit in https://opendev.org/openstack/nova and tell me about it?"
        "change-id: I63208c7bd5f9f4c3d5e4a40bd0f6253d0f042a37"
    )
    commit_message = """
    db: Resolve additional SAWarning warnings
    Resolving the following SAWarning warnings:

    Coercing Subquery object into a select() for use in IN(); please pass
    a select() construct explicitly

    SELECT statement has a cartesian product between FROM element(s)
    "foo" and FROM element "bar". Apply join condition(s) between each
    element to resolve.

    While the first of these was a trivial fix, the second one is a little
    more involved. It was caused by attempting to build a query across
    tables that had no relationship as part of our archive logic. For
    example, consider the following queries, generated early in
    '_get_fk_stmts':

    SELECT instances.uuid
    FROM instances, security_group_instance_association
    WHERE security_group_instance_association.instance_uuid = instances.uuid
        AND instances.id IN (__[POSTCOMPILE_id_1])

    SELECT security_groups.id
    FROM security_groups, security_group_instance_association, instances
    WHERE security_group_instance_association.security_group_id = security_groups.id
        AND instances.id IN (__[POSTCOMPILE_id_1])

    While the first of these is fine, the second is clearly wrong: why are
    we filtering on a field that is of no relevance to our join? These were
    generated because we were attempting to archive one or more instances
    (in this case, the instance with id=1) and needed to find related tables
    to archive at the same time. A related table is any table that
    references our "source" table - 'instances' here - by way of a foreign
    key. For each of *these* tables, we then lookup each foreign key and
    join back to the source table, filtering by matching entries in the
    source table. The issue here is that we're looking up every foreign key.
    What we actually want to do is lookup only the foreign keys that point
    back to our source table. This flaw is why we were generating the second
    SELECT above: the 'security_group_instance_association' has two foreign
    keys, one pointing to our 'instances' table but also another pointing to
    the 'security_groups' table. We want the first but not the second.

    Resolve this by checking if the table that each foreign key points to is
    actually the source table and simply skip if not. With this issue
    resolved, we can enable errors on SAWarning warnings in general without
    any filters.

    Conflicts:
        nova/objects/cell_mapping.py
        nova/tests/fixtures/nova.py

    NOTE(melwitt): The conflicts are because

    * Change Ia5304c552ce552ae3c5223a2bfb3a9cd543ec57c (db: Post
        reshuffle cleanup) is not in Wallaby

    * The WarningsFixture is in nova/tests/fixtures.py in Wallaby and
        change I07be8e16381592fc177eeecd4f0d7f2db93eb09d (tests: Enable
        SADeprecationWarning warnings) is also not in Wallaby

    Change-Id: I63208c7bd5f9f4c3d5e4a40bd0f6253d0f042a37
    Signed-off-by: Stephen Finucane <sfinucan@redhat.com>
    (cherry picked from commit 8142b9d)
    (cherry picked from commit ce2cc54)
    (cherry picked from commit 5b1d487)
    """
    metadata = {
        "source": "https://github.com/openstack/nova/commit/5d0325a78b2a5f7a9109290fb23d46a841042da6"
    }
    cm_doc = documents.Document(page_content=commit_message, metadata=metadata)
    text_splitter = lts.RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    )
    docs = text_splitter.split_documents([cm_doc])
    texts = [doc.page_content for doc in docs]

    embedding_function = lo.OllamaEmbeddings(model=embed_model)

    # load it in sqlite-vss in a table named state_union.
    # the db_file parameter is the name of the file you want
    # as your sqlite database.
    db = vectorstores.SQLiteVec.from_texts(
        texts=texts,
        embedding=embedding_function,
        table="state_union",
        db_file="./state/db/vec.db",
    )

    # Compile application and test
    graph_builder = graph.StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(graph.START, "retrieve")
    app = graph_builder.compile()

    response = app.invoke({"question": question, "llm": llm, "db": db})
    print(response["answer"])


if __name__ == "__main__":
    main()
