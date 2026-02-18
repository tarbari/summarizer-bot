from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
import os


class LLMClient:
    """Client for interacting with LM Studio's OpenAI-compatible API using LangChain"""

    def __init__(self, config):
        """Initialize the LLM client with configuration"""
        self.config = config
        self.model = self._initialize_model()
        self.output_parser = StrOutputParser()

    def _initialize_model(self) -> ChatOpenAI:
        """Initialize the ChatOpenAI model with configuration from .env and config"""
        try:
            # Get API configuration
            api_key = os.environ.get("LLM_API_KEY")
            api_url = os.environ.get("LLM_API_URL")
            model_name = self.config.get_llm_model()

            if not all([api_key, api_url, model_name]):
                raise ValueError("Missing LLM API configuration")

            # Configure the model
            model = ChatOpenAI(
                api_key=lambda: (
                    api_key if api_key else "Failed"
                ),  # TODO: This is a hacky way to handle a missing API key...
                base_url=api_url,
                model=model_name,
                temperature=0.7,  # Slightly creative but focused
                timeout=30,  # 30 second timeout
                max_tokens=self.config.get_max_tokens(),  # Limit response length
            )

            return model

        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM model: {e}")

    def create_summary_prompt(self, messages: list[Dict[str, Any]]) -> str:
        """Create a formatted prompt for summarizing messages"""
        # Format messages with timestamp and author
        formatted_messages = []
        for msg in messages:
            # Parse ISO timestamp to HH:MM format
            timestamp = msg["timestamp"].split("T")[1].split(":")[0:2]
            timestamp_str = f"[{timestamp[0]}:{timestamp[1]}]"

            formatted_messages.append(
                f"{timestamp_str} {msg['author_name']}: {msg['content']}"
            )

        messages_text = "\n".join(formatted_messages)

        # Create the full prompt - focused on news summary format with character limit
        prompt = f"""Act as a professional news editor. The following are news articles and updates shared in a Discord news channel over the last 24 hours. Create a concise news summary in the style of a professional news briefing.

IMPORTANT: Your response MUST be 2000 characters or less to fit within Discord's message limits. Be concise and prioritize the most important information.

News Articles and Updates:
{messages_text}

Please provide a short news summary (2-4 paragraphs) in a professional journalistic style. Focus on the most newsworthy items, key developments, and important information. Write in a neutral, objective tone suitable for a news publication. Include the most significant stories first. Identify the links to the source articles and add those to the message.

REMEMBER: Your entire response must be ≤2000 characters. If the content is too long, focus only on the top 2-3 most important stories."""

        return prompt

    async def generate_summary(self, messages: list[Dict[str, Any]]) -> str:
        """Generate a summary using the LLM"""
        try:
            # Create the prompt
            prompt_text = self.create_summary_prompt(messages)

            # Create messages for the LLM
            messages_for_llm = [
                SystemMessage(
                    content="You are a helpful assistant that summarizes Discord channel conversations."
                ),
                HumanMessage(content=prompt_text),
            ]

            # Generate the summary
            response = await self.model.ainvoke(messages_for_llm)
            summary = self.output_parser.invoke(response)

            return summary

        except Exception as e:
            raise RuntimeError(f"Failed to generate summary: {e}")

    def test_connection(self) -> bool:
        """Test the connection to the LLM API"""
        try:
            # Simple test message
            test_messages = [
                SystemMessage(content="Test connection"),
                HumanMessage(content="Hello, are you working?"),
            ]

            # Sync call for testing
            response = self.model.invoke(test_messages)
            return True

        except Exception as e:
            print(f"LLM connection test failed: {e}")
            return False
