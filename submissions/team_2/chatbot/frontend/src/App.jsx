import { useState } from 'react'

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const examplePrompts = [
    'Tell me about Spring Fest',
    'Main Building History',
    "Explain 'Hall Tempo'",
    'Life at Nehru Museum'
  ]

  const handleSendMessage = async (messageText) => {
    const query = messageText || inputValue
    if (!query.trim()) return

    // Add user message to chat
    const userMessage = {
      type: 'user',
      content: query
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/got/query', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      })

      const data = await response.json()
      
      // Add bot response to chat
      const botMessage = {
        type: 'bot',
        content: data.answer || data.error || 'No response received',
        confidence: data.confidence,
        nodesExplored: data.nodes_explored,
        graphJson: data.graph_json,
        htmlVisualization: data.html_visualization
      }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: `Error: ${error.message}`,
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-graphmind-dark">
      <header className="flex justify-between items-center px-8 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="#3B82F6" strokeWidth="2"/>
              <circle cx="12" cy="12" r="6" stroke="#3B82F6" strokeWidth="2"/>
              <circle cx="12" cy="12" r="2" fill="#3B82F6"/>
            </svg>
          </div>
          <span className="text-xl font-semibold text-graphmind-blue">GraphMind</span>
        </div>
        <div className="text-sm text-gray-400 tracking-wider">IIT KHARAGPUR</div>
      </header>

      <main className="flex-1 flex flex-col overflow-y-auto p-8">
        {messages.length === 0 ? (
          <div className="max-w-4xl mx-auto text-center py-12">
            <div className="inline-flex p-6 bg-[#1a2332] rounded-2xl mb-8">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="#3B82F6" strokeWidth="1.5"/>
                <path d="M12 6v6l4 2" stroke="#3B82F6" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h1 className="text-5xl font-semibold mb-4 text-white">How can I help you today?</h1>
            <p className="text-lg text-blue-400 leading-relaxed max-w-2xl mx-auto mb-12">
              I'm GraphMind, your intelligent companion for everything IIT<br />
              Kharagpur. Ask me about academics, culture, or campus<br />
              history.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
              {examplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  className="bg-[#0f1419] border border-[#1f2937] rounded-xl p-5 text-left cursor-pointer transition-all duration-200 hover:bg-[#1a1f2e] hover:border-graphmind-blue hover:-translate-y-0.5"
                  onClick={() => handleSendMessage(prompt)}
                >
                  <div className="text-base font-medium text-white mb-1">{prompt}</div>
                  <div className="text-xs text-gray-600">Click to ask GraphMind</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto w-full">
            <div className="flex flex-col gap-6">
              {messages.map((message, index) => (
                <div key={index} className={`flex gap-4 items-start ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                  {message.type === 'bot' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-lg overflow-hidden">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect width="24" height="24" rx="4" fill="#1E40AF"/>
                        <circle cx="12" cy="12" r="6" stroke="white" strokeWidth="1.5"/>
                      </svg>
                    </div>
                  )}
                  <div className={`flex-1 max-w-[80%] ${message.type === 'user' ? 'flex flex-col items-end' : ''}`}>
                    {message.type === 'bot' && (
                      <div className="text-sm mb-2 text-gray-400">
                        <strong>GraphMind</strong>
                      </div>
                    )}
                    {message.type === 'user' && (
                      <div className="bg-graphmind-blue text-white text-xs font-semibold px-3 py-1.5 rounded-full mb-2">
                        YOU
                      </div>
                    )}
                    <div className={`${message.type === 'user' ? 'bg-blue-600 text-white rounded-xl rounded-tr-none' : 'bg-graphmind-card text-gray-200 rounded-xl rounded-tl-none'} px-5 py-4 leading-relaxed whitespace-pre-wrap`}>
                      {message.content}
                    </div>
                    {message.type === 'bot' && message.confidence !== undefined && (
                      <div className="text-xs text-gray-500 mt-2 pl-5">
                        <span>Confidence: {message.confidence}</span>
                        {message.nodesExplored !== undefined && (
                          <span> | Nodes explored: {message.nodesExplored}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg overflow-hidden">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect width="24" height="24" rx="4" fill="#1E40AF"/>
                      <circle cx="12" cy="12" r="6" stroke="white" strokeWidth="1.5"/>
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="flex gap-2 p-4">
                      <span className="w-2 h-2 bg-graphmind-blue rounded-full animate-bounce [animation-delay:-0.32s]"></span>
                      <span className="w-2 h-2 bg-graphmind-blue rounded-full animate-bounce [animation-delay:-0.16s]"></span>
                      <span className="w-2 h-2 bg-graphmind-blue rounded-full animate-bounce"></span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="px-8 py-4 pb-6 border-t border-gray-800">
        <div className="max-w-4xl mx-auto mb-3 flex gap-3 items-center bg-[#0f1419] rounded-full px-6 py-3 border border-[#1f2937] focus-within:border-graphmind-blue transition-colors">
          <input
            type="text"
            className="flex-1 bg-transparent border-none outline-none text-white text-base placeholder-gray-600"
            placeholder="Message GraphMind..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          <button
            className="w-10 h-10 rounded-full border-none bg-transparent text-graphmind-blue flex items-center justify-center cursor-pointer transition-all duration-200 flex-shrink-0 hover:text-blue-400 disabled:text-gray-700 disabled:cursor-not-allowed"
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputValue.trim()}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        <div className="text-center text-sm text-graphmind-blue tracking-[0.2em] font-medium">
          YOGAH KARMASU KAUSHALAM
        </div>
      </footer>
    </div>
  )
}

export default App
