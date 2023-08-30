import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot import chatbot

description = """
This API is a chatbot that answers questions about chemical engineering.
"""

app = FastAPI(
  title="Chatbot API - Chemical Engineering",
  description=description,
  contact={
    "name": "Heath Henley",
    "email": "heath.j.henley@gmail.com"
  })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt = """You are a helpful chatbot and chemical engineering expert. The user
will ask you questions about chemical engineering, and the most relevant part
of a chemical engineering text book will be provided to you as context. Answer
the user's query using the information from textbook, if the information is not 
sufficient, ask the user to rephrase their question.\n"""
bot = chatbot.ChatBot(
  api_key=os.getenv("OPENAI_API_KEY"),
  prompt=prompt,
  message_memory=chatbot.MessageMemory(memory_length=1),
  knowledge_base=chatbot.KnowledgeBaseRedis(
      redis_url=os.getenv("REDIS_URL"),
      api_key=os.getenv("OPENAI_API_KEY"))
)

@app.get("/")
def search_textbook(user_query: str) -> str:
  """ Search for most relevant section in textbook and make response. """
  return bot.get_reply(user_query)
