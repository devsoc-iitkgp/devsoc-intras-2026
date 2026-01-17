
import os
import json
import re
import networkx as nx
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# 1. NEW IMPORT: Groq
from langchain_groq import ChatGroq

# --- GRAPH OF THOUGHTS ENGINE ---

class ThoughtNode:
    def __init__(self, id, question):
        self.id = id
        self.question = question
        self.retrieved_context = ""
        self.derived_thought = ""
        self.verified = False
        self.score = 0
        self.reasoning_paths = []  # NEW: Store multiple reasoning paths


class ReasoningPath:
    """Represents a single reasoning path/hypothesis with expert evaluations"""
    def __init__(self, path_id, claim, context, source_info=""):
        self.path_id = path_id
        self.claim = claim
        self.context = context
        self.source_info = source_info
        
        # Expert evaluations
        self.source_match_verdict = None
        self.source_match_conf = 0.0
        self.source_match_reason = ""
        
        self.halluc_verdict = None
        self.halluc_conf = 0.0
        self.halluc_details = ""
        
        self.logic_verdict = None
        self.logic_conf = 0.0
        self.logic_reason = ""
        
        # Final evaluation
        self.is_verified = False
        self.final_score = 0.0
        self.failure_reasons = []
    
    def get_consensus_score(self):
        """Calculate consensus score from all three experts"""
        if (self.source_match_verdict is None or 
            self.halluc_verdict is None or 
            self.logic_verdict is None):
            return 0.0
        
        avg_conf = (self.source_match_conf + self.halluc_conf + self.logic_conf) / 3
        return avg_conf
    
    def is_expert_consensus_passed(self):
        """Check if all experts agree (consensus)"""
        return (self.source_match_verdict and 
                (not self.halluc_verdict) and  # False means no hallucination
                self.logic_verdict)

def planner_agent(query):
    """
    Step 1: DECOMPOSITION & TRANSLATION
    Breaks the query into steps AND expands acronyms to full names.
    """
    system_prompt = """
    You are an expert Query Planner for IIT Kharagpur (MetaKGP).
    
    Your Goal: Break the user's query into simple, searchable sub-questions.
    
    CRITICAL RULE: The database does NOT understand acronyms. You MUST expand them.
    
    Use this Dictionary:
    - TFPS -> Technology Film and Photography Society
    - TLS -> Technology Literary Society
    - TSG -> Technology Students' Gymkhana
    - Gymkhana -> Technology Students' Gymkhana
    - RP / RP Hall -> Rajendra Prasad Hall of Residence
    - RK / RK Hall -> Radhakrishnan Hall of Residence
    - HMC -> Hall Management Centre
    -  VP -> Vice President
    -  GSec -> General Secretary
    
    Example:
    User: "Who is the VP of TFPS?"
    Output: ["Who is the Vice President of Technology Film and Photography Society?"]
    
    Return ONLY a valid JSON list of strings.
    """
    prompt = f"User Query: {query}\n\nPlan:"
    
    # We ask Llama 3 to give us a JSON plan
    response = llm.invoke([("system", system_prompt), ("human", prompt)]).content
    
    # Clean the response to ensure it's valid JSON
    try:
        start = response.find('[')
        end = response.rfind(']') + 1
        plan = json.loads(response[start:end])
        return plan
    except:
        return [query] # Fallback
    
def execution_agent(node, vector_db, graph_context):
    """
    Step 2: RETRIEVAL & DRAFTING - MULTI-PATH VERSION
    Retrieves multiple contexts and generates multiple reasoning paths.
    
    Each path represents a potential answer with its source context.
    """
    # A. Retrieve multiple relevant chunks
    print(f"    Retrieving contexts for: {node.question}")
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})  # Get 5 chunks
    docs = retriever.invoke(node.question)
    
    node.retrieved_context = "\n".join([d.page_content for d in docs])
    
    # B. Generate multiple reasoning paths from different contexts
    print(f"    Generating multiple reasoning paths...")
    
    # Path 1: Direct answer from primary context
    if docs:
        primary_context = docs[0].page_content
        prompt_path1 = f"""
        Sub-Question: {node.question}
        Primary Context: {primary_context}
        
        Based ONLY on this context, answer the sub-question directly.
        Be specific and cite what the source says.
        """
        path1_claim = llm.invoke(prompt_path1).content
        path1 = ReasoningPath(0, path1_claim, primary_context, "Primary Source")
        node.reasoning_paths.append(path1)
    
    # Path 2: Synthesized answer from multiple contexts
    if len(docs) > 1:
        multi_context = "\n".join([d.page_content for d in docs[:3]])
        prompt_path2 = f"""
        Sub-Question: {node.question}
        Multiple Contexts: {multi_context}
        
        Synthesize an answer using ALL available contexts.
        Mention which sources support each claim.
        """
        path2_claim = llm.invoke(prompt_path2).content
        path2 = ReasoningPath(1, path2_claim, multi_context, "Multi-Source Synthesis")
        node.reasoning_paths.append(path2)
    
    # Path 3: Time-aware answer (if asking about current/historical info)
    if "current" in node.question.lower() or "2025" in node.question.lower():
        prompt_path3 = f"""
        Sub-Question: {node.question}
        Available Context: {node.retrieved_context}
        
        This query asks for CURRENT information (2025).
        Extract ONLY claims marked as current, recent, or 2025/2024.
        Flag any outdated information.
        """
        path3_claim = llm.invoke(prompt_path3).content
        path3 = ReasoningPath(2, path3_claim, node.retrieved_context, "Temporal Filter (2025)")
        node.reasoning_paths.append(path3)
    
    # Set default thought (will be overridden after verification)
    if node.reasoning_paths:
        node.derived_thought = node.reasoning_paths[0].claim
    
    return node

# --- MoE VERIFICATION EXPERTS ---

def source_matcher(claim, context):
    """
    Expert 1: SOURCE MATCHER
    "Does the text in the retrieved chunk actually support this claim?"
    Returns: (verdict: bool, confidence: float, reasoning: str)
    """
    prompt = f"""
    You are a Source Matcher expert. Your job is to verify if a claim is directly supported by source text.
    
    CLAIM: {claim}
    
    SOURCE TEXT:
    {context}
    
    Question: Does the SOURCE TEXT explicitly contain information that directly supports this CLAIM?
    
    Respond in this exact JSON format:
    {{
        "verdict": "YES" or "NO",
        "confidence": 0.0 to 1.0,
        "reasoning": "Brief explanation of why the claim is or isn't supported"
    }}
    
    Be STRICT: The source must actually contain the claim, not just related information.
    """
    try:
        response = llm.invoke(prompt).content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return (result.get("verdict") == "YES", 
                    result.get("confidence", 0.5),
                    result.get("reasoning", ""))
    except:
        pass
    return (False, 0.3, "Error parsing source matcher response")


def hallucination_hunter(claim, context, original_query):
    """
    Expert 2: HALLUCINATION HUNTER
    "Is the bot inventing details not present in the scraped context?"
    Returns: (is_hallucination: bool, confidence: float, invented_details: str)
    """
    prompt = f"""
    You are a Hallucination Hunter expert. Your job is to detect if the bot is making up details.
    
    ORIGINAL QUERY: {original_query}
    CLAIM/RESPONSE: {claim}
    SCRAPED CONTEXT: {context}
    
    Analyze:
    1. What specific details does the CLAIM make?
    2. Which of these details are ACTUALLY present in the SCRAPED CONTEXT?
    3. Which details appear to be INVENTED or INFERRED (not in the context)?
    
    Respond in this exact JSON format:
    {{
        "is_hallucinating": true or false,
        "confidence": 0.0 to 1.0,
        "invented_details": "List specific details that are NOT in the context, or 'None' if everything is grounded"
    }}
    
    Be STRICT: If something isn't explicitly in the context, it's hallucination.
    """
    try:
        response = llm.invoke(prompt).content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return (result.get("is_hallucinating", False),
                    result.get("confidence", 0.5),
                    result.get("invented_details", "Unknown"))
    except:
        pass
    return (True, 0.3, "Error parsing hallucination detector response")


def logic_expert(claim, context, question):
    """
    Expert 3: LOGIC EXPERT
    "Does the conclusion follow from the premises?"
    Returns: (is_logical: bool, confidence: float, reasoning: str)
    """
    prompt = f"""
    You are a Logic Expert. Your job is to verify logical consistency.
    
    QUESTION: {question}
    PREMISES (from context): {context}
    CONCLUSION (bot's claim): {claim}
    
    Analyze:
    1. Are the premises clearly stated in the context?
    2. Does the conclusion logically follow from those premises?
    3. Are there any logical fallacies or unsupported jumps in reasoning?
    
    Respond in this exact JSON format:
    {{
        "is_logical": true or false,
        "confidence": 0.0 to 1.0,
        "reasoning": "Explanation of the logical flow (or lack thereof)"
    }}
    
    Example of LOGICAL: Context says "John is taller than Mary, Mary is taller than Sam" → Conclusion "John is taller than Sam" ✓
    Example of ILLOGICAL: Context says "Cats are animals" → Conclusion "Cats can talk" ✗
    """
    try:
        response = llm.invoke(prompt).content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return (result.get("is_logical", False),
                    result.get("confidence", 0.5),
                    result.get("reasoning", ""))
    except:
        pass
    return (False, 0.3, "Error parsing logic expert response")


def evaluate_reasoning_path(path, original_query, question):
    """
    Run all three experts on a single reasoning path.
    Updates the path object with expert verdicts.
    """
    # Expert 1: Source Matcher
    path.source_match_verdict, path.source_match_conf, path.source_match_reason = source_matcher(
        path.claim, 
        path.context
    )
    
    # Expert 2: Hallucination Hunter
    path.halluc_verdict, path.halluc_conf, path.halluc_details = hallucination_hunter(
        path.claim,
        path.context,
        original_query
    )
    
    # Expert 3: Logic Expert
    path.logic_verdict, path.logic_conf, path.logic_reason = logic_expert(
        path.claim,
        path.context,
        question
    )
    
    # Calculate final score and verdict
    path.final_score = path.get_consensus_score()
    path.is_verified = path.is_expert_consensus_passed() and path.final_score > 0.6
    
    # Capture failure reasons
    if not path.source_match_verdict:
        path.failure_reasons.append("Source not found")
    if path.halluc_verdict:
        path.failure_reasons.append("Hallucination detected")
    if not path.logic_verdict:
        path.failure_reasons.append("Illogical reasoning")
    
    return path


def rank_reasoning_paths(node, original_query):
    """
    Evaluate all reasoning paths and rank them by verification score.
    Returns sorted list of paths (best first).
    """
    print(f"\n   [MoE] Evaluating {len(node.reasoning_paths)} reasoning paths...")
    
    for i, path in enumerate(node.reasoning_paths):
        print(f"\n   ╔═ Path {i+1}: {path.source_info}")
        print(f"   ║ Claim: {path.claim[:100]}...")
        
        # Run all experts on this path
        evaluate_reasoning_path(path, original_query, node.question)
        
        # Display expert verdicts
        print(f"   ║ ├─ Source Matcher: {path.source_match_verdict} (conf: {path.source_match_conf:.2f})")
        print(f"   ║ │  └─ {path.source_match_reason}")
        print(f"   ║ ├─ Hallucination: {not path.halluc_verdict} (conf: {path.halluc_conf:.2f})")
        if path.halluc_details != "None":
            print(f"   ║ │  └─ {path.halluc_details}")
        print(f"   ║ ├─ Logic: {path.logic_verdict} (conf: {path.logic_conf:.2f})")
        print(f"   ║ │  └─ {path.logic_reason}")
        
        if path.is_verified:
            print(f"   ║ └─ VERDICT: ✓ VERIFIED (Score: {path.final_score:.2f}/1.0)")
        else:
            reasons = ", ".join(path.failure_reasons) if path.failure_reasons else "Low confidence"
            print(f"   ║ └─ VERDICT: ✗ REJECTED ({reasons})")
    
    # Sort by verification status (verified first) then by score
    ranked_paths = sorted(
        node.reasoning_paths,
        key=lambda p: (p.is_verified, p.final_score),
        reverse=True
    )
    
    return ranked_paths


def verification_agent(node, original_query):
    """
    Step 3: MoE VERIFICATION - COMPETITIVE EVALUATION
    Evaluates all reasoning paths against three expert verifiers.
    Selects the best verified path(s) for the final answer.
    """
    if not node.reasoning_paths:
        # Fallback: create a default path if none exist
        node.reasoning_paths.append(
            ReasoningPath(0, node.derived_thought, node.retrieved_context, "Default")
        )
    
    # Rank all paths using expert consensus
    ranked_paths = rank_reasoning_paths(node, original_query)
    
    # Select the best verified path
    best_path = ranked_paths[0] if ranked_paths else None
    
    if best_path:
        node.derived_thought = best_path.claim
        node.verified = best_path.is_verified
        node.score = int(best_path.final_score * 10)
        
        print(f"\n   [MoE] FINAL SELECTION: Path '{best_path.source_info}'")
        print(f"   [MoE] Final Answer: {best_path.claim[:150]}...")
    else:
        node.verified = False
        node.score = 0
        node.derived_thought = "(No reasoning path passed verification)"
    
    return node

def synthesis_agent(original_query, nodes):
    """
    Step 4: AGGREGATION - With Source Citations
    Combines all verified thoughts into the final answer with clear citations.
    """
    # Extract verified facts with their sources
    verified_facts_with_sources = []
    for n in nodes:
        if n.verified and n.reasoning_paths:
            best_path = n.reasoning_paths[0]
            for path in n.reasoning_paths:
                if path.is_verified:
                    best_path = path
                    break
            verified_facts_with_sources.append({
                "fact": best_path.claim,
                "source": best_path.source_info
            })
    
    facts_text = "\n".join([
        f"- {f['fact']} (Source: {f['source']})" 
        for f in verified_facts_with_sources
    ])
    
    prompt = f"""
    User Query: {original_query}
    
    Verified Facts gathered by researchers:
    {facts_text}
    
    Your task:
    1. Construct a coherent, helpful final answer using ONLY these verified facts
    2. Maintain source citations throughout
    3. If multiple paths said the same thing with different sources, mention that
    4. Be clear about what is verified vs what may have been rejected
    
    Format: Clear answer with (Source: XYZ) citations inline.
    """
    return llm.invoke(prompt).content


# --- CONFIGURATION ---
GOOGLE_API_KEY = "YOUR_API_KEY" # Keep this for Embeddings
GROQ_API_KEY = "YOUR_API_KEY"     # Paste your new gsk_... key here

VECTOR_DB_DIR = "faiss_index"
GRAPH_FILE = "metakgp_graph.gml"

# 2. SETUP BRAINS 
print("Loading Google Embeddings...")
# We keep Google for embeddings because your DB is already built with it!
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004", 
    google_api_key=GOOGLE_API_KEY
)

print("Loading Vector DB (Facts)...")
try:
    vector_db = FAISS.load_local(
        VECTOR_DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    print("Vector DB loaded!")
except Exception as e:
    print(f"Error loading Vector DB: {e}")
    # Tip: If this fails, run 'python ingest_modal.py' again
    exit()

print("Loading Graph (Logic)...")
try:
    G = nx.read_gml(GRAPH_FILE)
except:
    print("Warning: Graph file not found. Graph features will be skipped.")
    G = nx.Graph()

print("Initializing Groq (Llama 3)...")
# 3. CHANGE: Switch from Gemini to Groq
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile"
    
    
    ,  # A very powerful, fast model
    api_key=GROQ_API_KEY,
    temperature=0.3
)

# 4. HELPER FUNCTIONS
def get_graph_context(query):
    query = query.lower()
    related_nodes = []
    # Simple check to prevent errors if graph is empty
    if G.number_of_nodes() > 0:
        for node in G.nodes():
            if node.lower() in query:
                neighbors = list(G.neighbors(node))
                related_nodes.extend(neighbors[:5])
    
    if related_nodes:
        clean_names = [n.split('/')[-1].replace('_', ' ') for n in related_nodes]
        return f"Related topics: {', '.join(clean_names)}"
    return "No direct connections found."

def generate_response_got(query):
    print(f" [GoT] 1. Planning: Analyzing '{query}'...")
    plan = planner_agent(query)
    print(f" [GoT]    Plan: {plan}")
    
    nodes = []
    
    # Execute the Graph
    for i, sub_question in enumerate(plan):
        print(f" [GoT] 2. Executing Step {i+1}: {sub_question}")
        
        node = ThoughtNode(id=i, question=sub_question)
        g_context = get_graph_context(sub_question)
        node = execution_agent(node, vector_db, g_context)
        node = verification_agent(node, query)  # UPDATED: Pass original query
        
        print(f" [GoT] 3. Verification Score: {node.score}/10")
        nodes.append(node)

        # --- NEW CODE: DYNAMIC GRAPH UPDATE ---
        # Only add to graph if it's VERIFIED and useful (not "I don't know")
        if node.verified and "I don't know" not in node.derived_thought:
            print(f" [Graph] Learning new fact: {node.question}...")
            
            # 1. Add the Node (The Sub-Question)
            # We store the answer as a property of the node
            G.add_node(node.question, label="Thought", answer=node.derived_thought)
            
            # 2. Add the Edge (Connect it to the main topic)
            # We try to link it to the main query terms if they exist in the graph
            # Or just link to the previous node to show a "chain of thought"
            if i > 0:
                prev_node = nodes[i-1]
                G.add_edge(prev_node.question, node.question, relation="leads_to")
            
            # 3. SAVE TO DISK (Persistence)
            try:
                nx.write_gml(G, GRAPH_FILE)
                print(" [Graph] Memory updated on disk.")
            except Exception as e:
                print(f" [Graph] Warning: Could not save graph: {e}")
        # --------------------------------------
    
    print(f" [GoT] 4. Synthesizing Final Answer...")
    final_answer = synthesis_agent(query, nodes)
    return final_answer

# 5. START CHATTING (Only when running bot.py directly, not when imported by app.py)
if __name__ == '__main__':
    print("\nBOT IS READY! (Type 'exit' to stop)")
    while True:
        q = input("\nYou: ")
        if q.lower() in ["exit", "quit"]:
            break
        
        try:
            # CHANGED: Now calling the Graph of Thoughts function
            response = generate_response_got(q)
            print(f"\nBot: {response}")
        except Exception as e:
            print(f"Error: {e}")