import os
import uuid
import redis

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chatbot import chatbot


description = """
This API is a chatbot that answers questions about chemical engineering.
"""

def get_db():
  r = redis.Redis(
    host=os.getenv("REDIS_API_HOST"),
    port=os.getenv("REDIS_API_PORT"),
    password=os.getenv("REDIS_API_PASSWORD")
  )
  try:
    yield r
  finally:
    r.close()


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


class BotResult(BaseModel):
  """ Bot response to user query. """
  response: str
  id: str


class VoteResult(BaseModel):
  id: str
  upvoted: bool


@app.get("/", response_model=BotResult)
def search_textbook(user_query: str, db = Depends(get_db)) -> BotResult:
  """ Search for most relevant section in textbook and make response. """
  reply = bot.get_reply(user_query)
  id_ = uuid.uuid4().hex
  db.hset(id_, mapping={
    "user_query": user_query,
    "bot_reply": reply,
    "upvoted": 0,
  })
  return BotResult(response=reply, id=id_)


@app.post("/feedback/")
def feedback(vote: VoteResult, db = Depends(get_db)) -> str:
  """ User feedback on bot response. """
  try:
    reply = db.hgetall(vote.id)
    if vote.upvoted:
      reply["upvoted"] = 1
      print(f"{vote.id}: upvoted")
    else:
      reply["upvoted"] = -1
      print(f"{vote.id}: downvoted")
    db.hset(vote.id, mapping=reply)
  except Exception as e:
    print(e)
    return "Error logging feedback."
  return "Feedback received. Thank you!"