import os
import json
from typing import Optional, Dict, Any

class AIAssistant:
    """AI Assistant that converts natural language to commands and handles interactions."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "anthropic"):
        """
        Initialize the AI Assistant.

        Args:
            api_key: API key for the AI provider
            provider: AI provider to use ("anthropic" or "openai")
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = provider.lower()
        self.client = None

        if self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")
        elif self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed. Run: pip install openai")

    def parse_command(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse natural language input into a structured command or action.

        Args:
            user_input: Natural language input from user
            context: Optional context information (platform, history, etc.)

        Returns:
            Dictionary with parsed command/action information
        """
        if not self.client:
            return {
                "type": "error",
                "message": "AI client not initialized. Check API key and dependencies."
            }

        system_prompt = """You are a helpful AI assistant that converts natural language into structured commands and actions.

You can help users with:
1. Terminal commands (ls, cd, grep, etc.)
2. Sending messages (SMS, email, chat apps)
3. Making calls (phone calls, video calls)
4. Making orders (food delivery, shopping, etc.)
5. General interactions and automation

Respond with JSON in this format:
{
    "type": "command" | "message" | "call" | "order" | "interaction" | "conversation",
    "action": "specific action to take",
    "parameters": {
        // relevant parameters for the action
    },
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}

For terminal commands, use type "command" with the actual command in the "action" field.
For interactive actions (messages, calls, orders), use the appropriate type and include necessary parameters."""

        user_prompt = f"User input: {user_input}"
        if context:
            user_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                )
                content = response.content[0].text
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                content = response.choices[0].message.content
            else:
                return {"type": "error", "message": "Unknown provider"}

            # Extract JSON from response
            # Handle markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            return parsed

        except Exception as e:
            return {
                "type": "error",
                "message": f"Error parsing command: {str(e)}"
            }

    def generate_response(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a conversational response to user input.

        Args:
            user_input: User's message
            context: Optional context

        Returns:
            AI-generated response
        """
        if not self.client:
            return "AI client not initialized. Check API key and dependencies."

        system_prompt = "You are a helpful AI assistant in a terminal application. Provide concise, friendly responses."

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=512,
                    messages=[
                        {"role": "user", "content": f"{system_prompt}\n\nUser: {user_input}"}
                    ]
                )
                return response.content[0].text
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ]
                )
                return response.choices[0].message.content
            else:
                return "Unknown provider"
        except Exception as e:
            return f"Error generating response: {str(e)}"
