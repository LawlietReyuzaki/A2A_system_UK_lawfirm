"""
LLM Client wrapper for Google Gemini API.

Provides a unified interface for interacting with Gemini models,
with support for structured output, tool use, and conversation management.
"""

import os
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
import google.generativeai as genai
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    # In JSON mode this is usually a dict, but some model responses may be a list (e.g. `[ {...} ]`).
    structured_output: Optional[Any] = None


class GeminiClient:
    """
    Wrapper for Google Gemini API.
    
    Features:
    - System prompt management
    - Structured output with JSON mode
    - Conversation history tracking
    - Tool/function calling support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        default_temperature: float = 0.7
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model
        self.default_temperature = default_temperature
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        json_mode: bool = False,
        response_schema: Optional[Type[BaseModel]] = None
    ) -> LLMResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            json_mode: Force JSON output
            response_schema: Pydantic model for structured output
        """
        temp = temperature if temperature is not None else self.default_temperature
        
        # Build the full prompt
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System Instructions:\n{system_prompt}\n\n"
        
        full_prompt += f"User Request:\n{prompt}"
        
        # Configure generation
        generation_config = genai.GenerationConfig(
            temperature=temp,
            max_output_tokens=max_tokens,
        )
        
        if json_mode or response_schema:
            generation_config.response_mime_type = "application/json"
            if response_schema:
                # Add schema hint to prompt
                schema_hint = f"\n\nRespond with JSON matching this schema:\n{response_schema.model_json_schema()}"
                full_prompt += schema_hint
        
        # Generate response
        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        # Parse response
        content = response.text
        structured_output = None
        
        if json_mode or response_schema:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                    structured_output = json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0]
                    structured_output = json.loads(json_str)
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            },
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else "unknown",
            structured_output=structured_output
        )
    
    async def generate_with_schema(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> BaseModel:
        """
        Generate a response and parse into a Pydantic model.
        """
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True,
            response_schema=schema
        )
        
        if response.structured_output:
            return schema(**response.structured_output)
        
        raise ValueError(f"Failed to parse response into schema: {response.content}")


class AgentLLM:
    """
    Specialized LLM interface for agent operations.
    
    Provides high-level methods for common agent tasks like
    classification, extraction, and response generation.
    """
    
    def __init__(self, client: GeminiClient, agent_name: str, system_prompt: str):
        self.client = client
        self.agent_name = agent_name
        self.system_prompt = system_prompt
    
    async def classify(
        self,
        text: str,
        categories: List[str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify text into one or more categories"""
        
        prompt = f"""Classify the following text into the most appropriate category.

Categories: {', '.join(categories)}

Text to classify:
{text}

{f'Additional context: {context}' if context else ''}

Respond with JSON:
{{
    "category": "<primary category>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>",
    "secondary_categories": ["<other relevant categories>"]
}}"""
        
        response = await self.client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.2
        )
        
        return response.structured_output or {"category": "unknown", "confidence": 0.0}
    
    async def extract(
        self,
        text: str,
        fields: Dict[str, str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured information from text"""
        
        field_descriptions = "\n".join([f"- {k}: {v}" for k, v in fields.items()])
        
        prompt = f"""Extract the following information from the text.

Fields to extract:
{field_descriptions}

Text:
{text}

{f'Context: {context}' if context else ''}

Respond with JSON containing each field. Use null for fields not found.
Include a "confidence" object with confidence scores (0.0-1.0) for each field."""
        
        response = await self.client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.1
        )
        
        return response.structured_output or {}
    
    async def generate_response(
        self,
        query: str,
        context: str,
        constraints: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Generate a contextual response"""
        
        constraint_text = ""
        if constraints:
            constraint_text = "\n\nConstraints:\n" + "\n".join([f"- {c}" for c in constraints])
        
        prompt = f"""Generate a response to the following query.

Query: {query}

Context:
{context}

Tone: {tone}
{constraint_text}

Respond with JSON:
{{
    "response": "<your response>",
    "confidence": <0.0-1.0>,
    "requires_review": <true/false>,
    "review_reason": "<if requires_review is true>"
}}"""
        
        response = await self.client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.7
        )
        
        return response.structured_output or {"response": "", "confidence": 0.0}
    
    async def analyze(
        self,
        text: str,
        analysis_type: str,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Perform analysis on text"""
        
        criteria_text = ""
        if criteria:
            criteria_text = "\n\nEvaluation criteria:\n" + "\n".join([f"- {c}" for c in criteria])
        
        prompt = f"""Perform {analysis_type} analysis on the following text.

Text:
{text}
{criteria_text}

Provide a detailed analysis in JSON format including:
- summary: Brief summary of findings
- key_points: List of important points
- score: Overall score (0.0-1.0) if applicable
- recommendations: List of recommendations
- flags: Any concerns or issues flagged"""
        
        response = await self.client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.3
        )
        
        return response.structured_output or {}
