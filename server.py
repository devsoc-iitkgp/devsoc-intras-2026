import os
import time
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- LANGCHAIN IMPORTS ---
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# ==========================================
# CONFIGURATION
# ==========================================
DB_DIR = "C:/programming/prg/Devsoc-hackathon/chroma_db_graph"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

# PASTE YOUR GEMINI KEY HERE
MY_GEMINI_KEY = "AIzaSyA2wqAhkifsJ3uYzOx47gqDfod4NnoiT6o"

# ==========================================
# 1. MOE VERIFIER (The Auditor)
# ==========================================
class MoEVerifier:
    def __init__(self, llm):
        self.llm = llm

    def verify(self, question, answer, context_used):
        print(f"\n   🕵️  MoE Verifier is grading...")
        
        # EXPERT 1: SOURCE MATCHER
        source_prompt = ChatPromptTemplate.from_template("""
        You are the Source Matcher.
        CONTEXT: {context}
        CLAIM: {answer}
        TASK: Does the CONTEXT support the CLAIM?
        OUTPUT JSON: {{ "is_supported": boolean, "reason": "string" }}
        """)
        
        try:
            chain1 = source_prompt | self.llm | JsonOutputParser()
            result1 = chain1.invoke({"context": context_used, "answer": answer})
            if not result1['is_supported']:
                print(f"      ❌ Source Matcher Failed: {result1['reason']}")
                return False, f"Hallucination Detected: {result1['reason']}"
        except:
            pass 

        # EXPERT 2: LOGIC GUARD
        logic_prompt = ChatPromptTemplate.from_template("""
        You are the Logic Guard.
        QUESTION: {question}
        ANSWER: {answer}
        TASK: Is the answer relevant?
        OUTPUT JSON: {{ "is_relevant": boolean, "reason": "string" }}
        """)
        
        try:
            chain2 = logic_prompt | self.llm | JsonOutputParser()
            result2 = chain2.invoke({"question": question, "answer": answer})
            if not result2['is_relevant']:
                print(f"      ❌ Logic Guard Failed: {result2['reason']}")
                return False, f"Irrelevant Answer: {result2['reason']}"
        except:
            pass

        print("      ✅ Verified.")
        return True, "Verified"

# ==========================================
# 2. GRAPH AGENT (The Researcher)
# ==========================================
class GraphRAGAgent:
    def __init__(self):
        print("🧠 Initializing Graph Agent (Gemini 1.5 Flash)...")
        
        # 1. Load Memory (GPU)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.db = Chroma(persist_directory=DB_DIR, embedding_function=self.embeddings)
        
        # 2. Load Brain (Gemini)
        if not MY_GEMINI_KEY or "..." in MY_GEMINI_KEY:
            raise ValueError("❌ Missing Gemini API Key in server.py!")

        self.llm = ChatGoogleGenerativeAI(
            google_api_key=MY_GEMINI_KEY,
            model="gemini-2.5-flash", 
            temperature=0
        )
        
        self.verifier = MoEVerifier(self.llm)
        
        self.navigator_prompt = ChatPromptTemplate.from_template("""
        You are a Research Agent.
        
        GOAL: {goal}
        
        CURRENT INFORMATION:
        {context}
        
        INSTRUCTIONS:
        1. If you have the answer, reply: ANSWER: [Answer]
        2. If you need to search more, reply: HOP: [Topic Name]
        
        Output ONLY the line starting with ANSWER or HOP.
        """)
        
    def search(self, query):
        results = self.db.similarity_search(query, k=1)
        return results[0] if results else None

    def solve(self, user_query, max_hops=3):
        print(f"\n🚀 Processing: '{user_query}'")
        current_query = user_query
        visited_context = []
        
        for step in range(max_hops):
            print(f"   👣 Step {step+1}: Searching for '{current_query}'...")
            time.sleep(1) 
            
            node = self.search(current_query)
            if not node:
                break
                
            content = node.page_content
            source = node.metadata.get('title', 'Unknown')
            neighbors = node.metadata.get('graph_neighbors', 'None')
            
            visited_context.append(f"SOURCE: {source}\nCONTENT: {content}\nLINKS: {neighbors}")
            full_context = "\n\n".join(visited_context)
            
            chain = self.navigator_prompt | self.llm | StrOutputParser()
            try:
                decision = chain.invoke({"goal": user_query, "context": full_context})
                decision = decision.strip()
                
                match = re.search(r"(ANSWER|HOP):\s*(.*)", decision, re.DOTALL)
                if match:
                    action = match.group(1)
                    value = match.group(2).strip()
                    
                    if action == "ANSWER":
                        # Verify before returning
                        is_valid, reason = self.verifier.verify(user_query, value, full_context)
                        if is_valid:
                            return value
                        else:
                            return f"I found an answer, but verification failed: {reason}"
                    
                    elif action == "HOP":
                        print(f"      🔗 Hopping to -> {value}")
                        current_query = value
                else:
                    if step == max_hops - 1: return decision
            except Exception as e:
                return f"Error: {e}"

        return "I could not find the answer in the database."

# ==========================================
# 3. FASTAPI SERVER
# ==========================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

print("⏳ Starting Server and loading AI...")
# Initialize Agent ONCE when server starts to save time
agent = GraphRAGAgent()
print("✅ Server Ready!")

@app.post("/chat")
def chat(req: ChatRequest):
    print(f"Received Query: {req.query}")
    answer = agent.solve(req.query)
    return {"answer": answer}

