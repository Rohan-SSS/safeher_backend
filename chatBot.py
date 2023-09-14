from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
import openai
import pinecone
import os

openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")
pinecoen_env = os.getenv("PINECONE_ENVIRONMENT")

def init_pinecone(pinecone_key, pinecoen_env):
  # init pinecone
  pinecone.init(
    api_key=pinecone_key,
    environment=pinecoen_env,
  )

def get_answer(question):
  query = f"You are a chatbot personalized for answering questions, now answer the\nquestion: {question} \n Do not go out of context in any circumstance or hallucinate or fabricate information."

  # select the chat model and temperature
  llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6, openai_api_key=openai_key)
  embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

  # index_name -> index vector name in Pinecone
  index_name = "woman-safety-embeddings"

  # question and answer chain
  qa_chain = load_qa_chain(llm, chain_type="stuff")

  docsearch = Pinecone.from_existing_index(index_name, embeddings)

  docs = docsearch.similarity_search(query)
  answer = qa_chain.run(input_documents = docs, question=query, max_tokens=150)

  return answer
