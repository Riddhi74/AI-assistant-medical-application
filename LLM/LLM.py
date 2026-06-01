from langchain_ollama import OllamaLLM

def load_llm():

    llm = OllamaLLM(
        model="phi3:mini",
        temperature=0.2,
        num_ctx=512,
        streaming=True,
    )

    print("LLM loaded")

    return llm