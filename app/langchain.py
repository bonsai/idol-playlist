from langchain_core.prompts import ChatPromptTemplate


SONG_REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "You review underground idol song catalog records. Return factual, concise judgments."),
        ("human", "Review this song record for identity/data quality:\\n{song}"),
    ]
)


def build_song_review_prompt(song: dict) -> str:
    return SONG_REVIEW_PROMPT.invoke({"song": song}).to_string()
