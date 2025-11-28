"""
LLM Client wrapper for Gemini models.

This module provides the LLMClient class that wraps Google Gemini models
for use in the research workflow, supporting prompt execution with error handling,
logging, and configuration loading.
"""

import json
import time
from typing import Dict, Any, List, Optional
import structlog
from google import genai
from google.genai import types

from ..config.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


class LLMClientError(Exception):
    """Custom exception for LLM client errors."""
    pass


class LLMClient:
    """
    Wrapper client for Google Gemini models supporting research workflows.

    Supports Gemini-2.0-Flash and Gemini-2.5-Flash models with methods for
    prompt execution, search term adjustment, synthesis, and question generation.
    """

    SUPPORTED_MODELS = {
        'gemini-2.0-flash': 'gemini-2.0-flash',
        'gemini-2.5-flash': 'gemini-2.5-flash'
    }

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """
        Initialize the LLM client with configuration.

        Args:
            config_loader: ConfigLoader instance for loading API keys and settings
        """
        self.config = config_loader or ConfigLoader()
        self.api_key = self.config.get('google_genai_api_key')
        if not self.api_key:
            raise LLMClientError("Google GenAI API key not configured")

        # Initialize the client with API key
        self.client = genai.Client(api_key=self.api_key)
        self.rate_limit_delay = self.config.get('llm_rate_limit_delay_seconds', 10)
        self.last_call_time = 0.0
        logger.info("LLMClient initialized", supported_models=list(self.SUPPORTED_MODELS.keys()), rate_limit_delay=self.rate_limit_delay)

    # Removed _initialize_clients as we use a single client instance

    def execute_prompt(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using the specified model.

        Args:
            model_name: Friendly model name ('gemini-2.0-flash' or 'gemini-2.5-flash')
            prompt: The prompt text to send
            **kwargs: Additional parameters for generation (temperature, max_tokens, etc.)

        Returns:
            Generated response text

        Raises:
            LLMClientError: If model not supported or generation fails
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise LLMClientError(f"Unsupported model: {model_name}. Supported: {list(self.SUPPORTED_MODELS.keys())}")

        # Enforce rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds before API call")
            time.sleep(sleep_time)

        # Create generation config with best practices for high quality and reproducible results
        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', 0.7),
            max_output_tokens=kwargs.get('max_tokens', 2048),
            top_p=kwargs.get('top_p', 0.9),
            top_k=kwargs.get('top_k', 40),
            # Add grounding tool for research tasks to ensure factual accuracy
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )

        try:
            logger.info("Executing prompt", model=model_name, prompt_length=len(prompt))
            response = self.client.models.generate_content(
                model=self.SUPPORTED_MODELS[model_name],
                contents=prompt,
                config=config
            )
            response_text = response.text.strip()
            self.last_call_time = time.time()
            logger.info("Prompt executed successfully", model=model_name, response_length=len(response_text))
            return response_text
        except Exception as e:
            logger.error("Prompt execution failed", model=model_name, error=str(e))
            raise LLMClientError(f"Failed to execute prompt with {model_name}: {e}")

    def adjust_search_terms(self, original_query: str, context: str) -> str:
        """
        Adjust search terms for better research results using LLM.

        Args:
            original_query: Original search query
            context: Additional context about the research need

        Returns:
            Adjusted search query
        """
        prompt = f"""
        Given the original search query: "{original_query}"
        And the research context: {context}

        Provide an improved, more specific search query that would yield better results for market research on partnership analysis in the wellness industry.

        Return only the improved query, no explanation.
        """
        try:
            return self.execute_prompt('gemini-2.5-flash', prompt, temperature=0.3)
        except LLMClientError as e:
            logger.warning("Failed to adjust search terms, using original", error=str(e))
            return original_query

    def synthesize_findings(self, findings: List[Dict[str, Any]]) -> str:
        """
        Synthesize research findings into a coherent narrative.

        Args:
            findings: List of finding dictionaries with benchmark data

        Returns:
            Synthesized narrative text
        """
        findings_text = json.dumps(findings, indent=2)
        prompt = f"""
        Based on the following information:

        {findings_text}

        Synthesize a coherent market analysis narrative for partnership evaluation. Focus on key benchmarks, trends, and insights relevant to business partnerships in the wellness industry.

        Provide a concise but comprehensive summary.
        """
        try:
            return self.execute_prompt('gemini-2.5-flash', prompt, temperature=0.5, max_tokens=1024)
        except LLMClientError as e:
            logger.warning("Failed to synthesize findings", error=str(e))
            return "Synthesis failed due to LLM error. Raw findings: " + findings_text

    def generate_questions(self, topic: str, context: str) -> List[str]:
        """
        Generate follow-up research questions.

        Args:
            topic: Research topic
            context: Current context and findings

        Returns:
            List of generated questions
        """
        prompt = f"""
        Topic: {topic}
        Current Context: {context}

        Generate 3-5 specific, targeted research questions that would help gather more detailed information for partnership analysis in the wellness industry.

        Return the questions as a JSON array of strings.
        """
        try:
            response = self.execute_prompt('gemini-2.0-flash', prompt, temperature=0.6)
            # Parse JSON response
            questions = json.loads(response)
            if isinstance(questions, list):
                return questions
            else:
                logger.warning("Invalid JSON format in generate_questions response")
                return []
        except (LLMClientError, json.JSONDecodeError) as e:
            logger.warning("Failed to generate questions", error=str(e))
            return []
