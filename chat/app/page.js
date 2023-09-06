"use client"
import { useState } from 'react';
import styles from '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput } from '@chatscope/chat-ui-kit-react';


const API_URL = "https://chebot-production.up.railway.app/"
const SPLIT_URL_ON = "This link was used to generate an answer:"
const BOOK = "https://eng.libretexts.org/Bookshelves/Chemical_Engineering/Phase_Relations_in_Reservoir_Engineering_(Adewumi)"

const getChatbotResponse = async (query) => {
  const url = `${API_URL}?user_query=${encodeURI(query)}`
  const response = await fetch(url) 
  return await response.json()
}


const postFeedback = async (id, upVote) => {
  const url = `${API_URL}feedback/`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      id: id,
      upvoted: upVote
    })
  })
  const res = await response.text()
  console.log(res)
  return res
}


const splitUrlFromResponse = (response) => {
  return response.split(SPLIT_URL_ON)
}


const upVoteHandler = (id) => {
  console.log("upvoted:", id)
  postFeedback(id, true)
}


const downVoteHandler = (id) => {
  console.log("downvoted:", id)
  postFeedback(id, false)
}


const VoteButton = ({clickHandler, upVote}) => {
  const text = upVote ? "Yes" : "No"
  return (
    <button onClick={clickHandler}>
      {text}
    </button>
  )
}


const Reference = ({ url }) => {
  return (
    <a target="_blank" href={url}>Reference</a>
  )
}


const VoteControls = ({ pkey }) => {
  if (!pkey) return null
  const [voted, setVoted] = useState(false)
  if (voted) return "Thanks!"
  return (
    <>
      Helpful?
      {<VoteButton
        clickHandler={
          () => {upVoteHandler(pkey); setVoted(true)}}
        upVote={true}/>}/
      {<VoteButton
        clickHandler={
          () => {downVoteHandler(pkey); setVoted(true)}}
        upVote={false} />}
    </>
  )
}


const CustomMessage = ({ idx, messages}) => {
  let message = messages[idx]
  return (
    <Message model={{
        direction: message.direction,
        position: message.position,
        type: 'custom'}}
      >
      <Message.CustomContent>
        <p>{message.message}</p>
        <div className="flex gap-2">
          {message.url ? <Reference url={message.url}/> : null}
          {idx > 0 ? <VoteControls pkey={messages[idx].id} /> : null}
        </div>
      </Message.CustomContent>
    </Message>
  )
}


export default function Home() {
  const [messages, setMessages] = useState([
    {
      message: "Hi! I'm the ChE GPT Bot. Ask me a question! I am only using the Reservoir Engineering book linked below as a reference for now. So I am more of an expert on Phase Equilibrium calculations for reservoir systems.",
      sentTime: "just now",
      sender: "Che Bot",
      direction: "incoming",
      position: "single",
      url: BOOK,
    }
  ])
  const [currentInput, setCurrentInput] = useState("")
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    setLoading(true)
    setMessages([...messages, {
      message: currentInput,
      sentTime: "just now",
      sender: "me",
      direction: "outgoing",
      position: "single"
    }])
    const {response, id} = await getChatbotResponse(currentInput)
    setLoading(false)
    let [clean_response, url] = splitUrlFromResponse(response)
    const msg = clean_response + `<a target="_blank" href=${url}>Reference</a>`
    setMessages((prev) => ([...prev,
      {
        message: clean_response,
        id: id,
        url: url,
        sentTime: "just now",
        sender: "ChE Bot",
        direction: "incoming",
        position: "single"
      }]))
  }

  return (
    <main className="min-h-screen p-24 w-9/12 h-screen">
      <div style={{ height: "100%", width: "100%"}}>
        <MainContainer>
          <ChatContainer>       
            <MessageList loading={loading}>
              {messages.map(
                (message, index) => (
                  message.direction === "incoming" ?
                    <CustomMessage
                      messages={messages}
                      key={index}
                      idx={index} /> :
                    <Message key={index} model={{
                      message: message.message,
                      sentTime: message.sentTime,
                      sender: message.sender,
                      direction: message.direction,
                      position: message.position}}/>))}
            </MessageList>
            <MessageInput
              attachButton={false}
              placeholder="Type message here"
              onChange={(e) => (setCurrentInput(e))}
              onSend={sendMessage}
            />
          </ChatContainer>
        </MainContainer>
      </div>
    </main>
  )
}