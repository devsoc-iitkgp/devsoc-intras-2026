"""
Simplified Graph of Thought (GoT) Engine with Llama-3.3-70b
Architecture: Query -> RAG (top_k=30) -> GoT on chunks -> Single MoE round -> Final answer
"""

import logging
import asyncio
from typing import Dict, List, Optional
import json
import httpx

from src.services.chat_agent.experts import MoEGauntlet
from src.utils.embedding_client import ModalEmbeddingClient
from src.utils.groq_client import GroqClient

logger = logging.getLogger(__name__)


class SimplifiedGoTEngine:
    """
    Simplified Graph of Thought reasoning engine
    Process: Query -> RAG (30 chunks) -> Analyze chunks -> Single MoE verification -> Final answer
    """
    
    def __init__(
        self,
        modal_url: str,
        groq_api_key: str,
        query_api_url: str = "http://localhost:8000/query/search",
        top_k: int = 30
    ):
        """
        Initialize the simplified GoT Engine
        
        Args:
            modal_url: Modal embedding service URL
            groq_api_key: Groq API key
            query_api_url: URL for the RAG query API
            top_k: Number of chunks to retrieve from RAG
        """
        self.modal_url = modal_url
        self.groq_api_key = groq_api_key
        self.query_api_url = query_api_url
        self.top_k = top_k
        
        # Initialize components
        self.embedding_client = ModalEmbeddingClient(modal_url)
        self.groq_client = GroqClient(groq_api_key)
        self.moe_gauntlet = MoEGauntlet(self.groq_client)
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"SimplifiedGoTEngine initialized with top_k={top_k}")
    
    async def query_rag(self, query: str) -> Dict:
        """
        Query the RAG API to get relevant context
        
        Args:
            query: Search query
        
        Returns:
            Dict with results
        """
        try:
            logger.info(f"Querying RAG with top_k={self.top_k}")
            response = await self.http_client.post(
                self.query_api_url,
                json={"query": query, "top_k": self.top_k}
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"results": [], "error": str(e)}
    
    async def call_llm(self, prompt: str, max_tokens: int = 3072) -> str:
        """
        Call Llama-3.3-70b model
        
        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens
        
        Returns:
            LLM response
        """
        try:
            return await self.groq_client.generate_judge(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    async def check_relevance(self, query: str) -> Dict:
        """
        Check if the query is related to IIT Kharagpur/MetaKGP
        
        Returns:
            {
                "is_relevant": bool,
                "reasoning": str
            }
        """
        prompt = f"""You are a relevance checker for MetaKGP Wiki (IIT Kharagpur information system).

Question: {query}

Is this question about IIT Kharagpur, its campus, academics, facilities, events, societies, or any related information?

Answer ONLY with JSON:
{{
    "is_relevant": true/false,
    "reasoning": "brief explanation"
}}

Response:"""
        
        response = await self.call_llm(prompt, max_tokens=256)
        
        try:
            result = json.loads(response.strip())
            return result
        except:
            # Default to relevant if parsing fails
            return {"is_relevant": True, "reasoning": "Parse error, proceeding"}
    
    async def analyze_chunks(self, query: str, chunks: List[Dict]) -> str:
        """
        Analyze retrieved chunks and extract relevant information
        
        Args:
            query: Original query
            chunks: List of retrieved chunks from RAG
        
        Returns:
            Analyzed thought/summary from chunks
        """
        # Use only top 15 chunks to avoid token limit (30 chunks = 14k tokens)
        # Top 15 chunks should be ~7k tokens, well within limits
        chunks_to_analyze = chunks[:15]
        
        # Format chunks
        chunks_text = ""
        for i, chunk in enumerate(chunks_to_analyze, 1):
            chunks_text += f"\n--- Chunk {i} (Score: {chunk['score']:.3f}) ---\n"
            chunks_text += f"Title: {chunk['metadata']['title']}\n"
            chunks_text += f"Text: {chunk['text']}\n"
        
        prompt = f"""You are analyzing information from the MetaKGP wiki to answer a question about IIT Kharagpur.

Question: {query}

Retrieved Information (top 15 most relevant chunks from 30 total):
{chunks_text}

INSTRUCTIONS:
1. Analyze ALL the chunks carefully
2. Extract and synthesize relevant information that answers the question
3. Focus on facts, names, dates, numbers, and specific details
4. If some chunks don't contain the answer, acknowledge it
5. Be comprehensive but concise
6. If the information is insufficient, say so clearly

Provide a thorough analysis based on these chunks:"""
        
        logger.info("Analyzing top 15 chunks with LLM")
        return await self.call_llm(prompt, max_tokens=2048)
    
    async def generate_final_answer(self, query: str, analysis: str, verification_result: Dict) -> str:
        """
        Generate the final answer based on analysis and verification
        
        Args:
            query: Original query
            analysis: Analysis from chunks
            verification_result: MoE verification result
        
        Returns:
            Final answer
        """
        verification_remarks = verification_result.get("remarks", "")
        passed = verification_result.get("passed", False)
        final_score = verification_result.get("final_score", 0.0)
        
        prompt = f"""You are synthesizing verified information from the MetaKGP wiki (IIT Kharagpur).

Original Question: {query}

Analysis from Wiki Chunks:
{analysis}

Verification Status:
- Passed: {passed}
- Confidence Score: {final_score:.2f}
- Verification Notes: {verification_remarks}

INSTRUCTIONS:
1. Provide a clear, direct answer to the question
2. Use information from the analysis above
3. Structure your response well with proper formatting
4. Include specific facts, names, dates, and details
5. If information is incomplete, acknowledge the limitations
6. Be conversational but accurate
7. Do not make up information not present in the analysis

Final Answer:"""
        
        logger.info("Generating final answer")
        return await self.call_llm(prompt, max_tokens=2048)
    
    async def process_query(self, query: str) -> Dict:
        """
        Process a query through the simplified pipeline
        
        Pipeline:
        1. Check if query is relevant to MetaKGP
        2. Query RAG for top 30 chunks
        3. Analyze chunks with Graph of Thought reasoning
        4. Run single MoE verification round
        5. Generate final answer
        
        Args:
            query: User query
        
        Returns:
            Dict with final answer and metadata
        """
        logger.info(f"Processing query: {query}")
        
        try:
            # Step 1: Check relevance
            relevance = await self.check_relevance(query)
            
            if not relevance.get("is_relevant", True):
                logger.info(f"Query not relevant: {relevance.get('reasoning')}")
                return {
                    "query": query,
                    "answer": "This question is not related to IIT Kharagpur or MetaKGP. I can only answer questions about IIT Kharagpur campus, academics, facilities, events, societies, and related information from the MetaKGP wiki.",
                    "confidence": 0.0,
                    "chunks_retrieved": 0,
                    "verification_passed": False,
                    "reasoning": relevance.get("reasoning"),
                    "error": None
                }
            
            # Step 2: Query RAG
            logger.info("Step 2: Querying RAG")
            rag_results = await self.query_rag(query)
            
            if not rag_results.get("results"):
                logger.warning("No chunks retrieved from RAG")
                return {
                    "query": query,
                    "answer": "I don't have enough information in the MetaKGP wiki to answer this question. The wiki may not contain details about this topic yet.",
                    "confidence": 0.0,
                    "chunks_retrieved": 0,
                    "verification_passed": False,
                    "reasoning": "No relevant chunks found",
                    "error": rag_results.get("error")
                }
            
            chunks = rag_results["results"]
            logger.info(f"Retrieved {len(chunks)} chunks")
            
            # Format context for MoE
            context_text = "\n\n".join([
                f"[{i+1}] {chunk['text']}" 
                for i, chunk in enumerate(chunks[:10])  # Use top 10 for context
            ])
            
            # Step 3: Analyze chunks with GoT reasoning
            logger.info("Step 3: Analyzing chunks")
            analysis = await self.analyze_chunks(query, chunks)
            
            if not analysis:
                logger.error("Failed to analyze chunks")
                return {
                    "query": query,
                    "answer": "I encountered an error while analyzing the information. Please try again.",
                    "confidence": 0.0,
                    "chunks_retrieved": len(chunks),
                    "verification_passed": False,
                    "reasoning": "Analysis failed",
                    "error": "LLM analysis failed"
                }
            
            # Step 4: Single MoE verification round
            logger.info("Step 4: Running MoE verification")
            verification = await self.moe_gauntlet.verify_thought(
                thought=analysis,
                context=context_text,
                graph_history=[]  # No graph history in simplified version
            )
            
            logger.info(f"Verification result: {verification['remarks']}")
            
            # Step 5: Generate final answer
            logger.info("Step 5: Generating final answer")
            final_answer = await self.generate_final_answer(query, analysis, verification)
            
            if not final_answer:
                logger.error("Failed to generate final answer")
                return {
                    "query": query,
                    "answer": "I encountered an error while generating the answer. Please try again.",
                    "confidence": 0.0,
                    "chunks_retrieved": len(chunks),
                    "verification_passed": verification["passed"],
                    "reasoning": verification["remarks"],
                    "error": "Final answer generation failed"
                }
            
            # Return result
            confidence = verification["final_score"] * 0.9  # Scale down slightly
            
            # Extract query keywords (remove common words)
            query_lower = query.lower()
            common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in', 'at', 'to', 'for', 'on', 'with', 'by', 'from', 'what', 'who', 'where', 'when', 'how', 'why', 'which'}
            query_keywords = [word for word in query_lower.split() if word not in common_words and len(word) > 2]
            
            # Filter chunks that have query keywords in source_page or title
            relevant_chunks = []
            for chunk in chunks:
                source_page = chunk["metadata"]["source_page"].lower()
                title = chunk["metadata"]["title"].lower()
                
                # Check if any query keyword appears in source_page or title
                has_keyword = any(keyword in source_page or keyword in title for keyword in query_keywords)
                
                if has_keyword:
                    relevant_chunks.append(chunk)
            
            # If we have relevant chunks, use them; otherwise fall back to top chunks
            chunks_for_sources = relevant_chunks if relevant_chunks else chunks
            
            # Extract unique sources, prioritizing those with query keywords
            unique_sources = []
            seen_sources = set()
            for chunk in chunks_for_sources[:15]:  # Check top 15 relevant chunks
                source = chunk["metadata"]["source_page"]
                if source not in seen_sources and len(unique_sources) < 5:
                    unique_sources.append({
                        "page": source,
                        "score": chunk["score"]
                    })
                    seen_sources.add(source)
            
            # Format sources as list of page names
            source_pages = [s["page"] for s in unique_sources]
            
            return {
                "query": query,
                "answer": final_answer,
                "confidence": confidence,
                "chunks_retrieved": len(chunks),
                "verification_passed": verification["passed"],
                "verification_score": verification["final_score"],
                "reasoning": verification["remarks"],
                "sources": source_pages,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": "I encountered an error while processing your question. Please try again.",
                "confidence": 0.0,
                "chunks_retrieved": 0,
                "verification_passed": False,
                "reasoning": str(e),
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
