from .base_agent import BaseAgent
from models.triaging_models import TriagingResponse
from openai import OpenAI
from pydantic import ValidationError
import json

class TriagingAgent(BaseAgent):
    """
    Triaging Agent: Assesses tasks and delegates to specialized agents.
    """
    def __init__(self, client: OpenAI):
        super().__init__(name="TriagingAgent")
        self.client = client
        self.system_prompt = (
            "You are a Triaging Agent. Your role is to assess the user's query and route it to the relevant agents. "
            "The agents available are:\n"
            "- FetchingAgent: Retrieves starred repositories from GitHub.\n"
            "- ProcessingAgent: Cleans and enriches repository data.\n"
            "- CurationAgent: Assigns tags and scores to repositories.\n"
            "- EditorAgent: Aligns new repositories with existing README structure and updates it.\n"
            "- ArchiveAgent: Archives editor's notes for historical reference."
        )
    
    def execute(self, user_query: str) -> TriagingResponse:
        prompt = (
            f"User Query: {user_query}\n\n"
            "Based on the user's query, determine which agents should handle this task. "
            "Provide the names of the agents and a refined query for each.\n\n"
            "Respond in JSON format adhering to the following schema:\n\n"
            "{\n"
            '    "agents": ["string"],\n'
            '    "query": "string"\n'
            "}"
        )
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=TriagingResponse,
                max_tokens=150
            )
            return completion.choices[0].message.parsed
        except ValidationError as ve:
            print(f"TriagingAgent Validation Error: {ve}")
            raise ve
        except Exception as e:
            print(f"TriagingAgent Unexpected Error: {e}")
            raise e
