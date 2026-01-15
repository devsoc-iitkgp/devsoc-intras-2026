"""
Gemini Client
Client for Google Gemini API using google-genai SDK (chat-based approach)
"""

import logging
from typing import List
import asyncio

from google import genai

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google Gemini models using google-genai SDK
    Uses chat-based interface for better conversation handling
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Gemini client
        
        Args:
            api_key: Google API key for Gemini
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        
        # Create separate chat sessions for judge and expert
        self.judge_chat = self.client.chats.create(model="gemini-1.5-flash")
        self.expert_chat = self.client.chats.create(model="gemini-1.5-flash")
        
        logger.info("GeminiClient initialized with google-genai SDK (chat-based) using gemini-1.5-flash")
    
    async def generate_judge(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Call Gemini model for complex reasoning
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            logger.info(f"Calling Judge model with prompt length: {len(prompt)}")
            
            # Run in executor since genai SDK is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.judge_chat.send_message(prompt)
            )
            
            text = response.text
            logger.info(f"Judge model generated {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"Judge model error: {e}")
            # Create a new chat session on error
            self.judge_chat = self.client.chats.create(model="gemini-1.5-flash")
            raise
    
    async def generate_expert(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Call Gemini model for fast verification
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            logger.info(f"Calling Expert model with prompt length: {len(prompt)}")
            
            # Run in executor since genai SDK is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.expert_chat.send_message(prompt)
            )
            
            text = response.text
            logger.info(f"Expert model generated {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"Expert model error: {e}")
            # Create a new chat session on error
            self.expert_chat = self.client.chats.create(model="gemini-1.5-flash")
            raise
    
    async def batch_generate_expert(self, prompts: List[str], max_tokens: int = 1024) -> List[str]:
        """
        Batch generate using Expert model
        
        Args:
            prompts: List of input prompts
            max_tokens: Maximum tokens to generate per prompt
            
        Returns:
            List of generated texts
        """
        try:
            logger.info(f"Batch calling Expert model with {len(prompts)} prompts")
            
            results = []
            for prompt in prompts:
                text = await self.generate_expert(prompt, max_tokens)
                results.append(text)
            
            logger.info(f"Expert model batch generated {len(results)} responses")
            return results
            
        except Exception as e:
            logger.error(f"Expert batch error: {e}")
            raise
