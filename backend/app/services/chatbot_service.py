"""
Chatbot service using LangChain for natural language processing
"""

from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime
import uuid

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.chatbot import ChatIntent, ChatMessage, ChatResponse, IntentClassification

logger = structlog.get_logger()

class ChatbotService:
    """Service for handling chatbot interactions using LangChain"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.1
        )
        self.system_prompt = self._create_system_prompt()
        self.intent_examples = self._create_intent_examples()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the chatbot"""
        return """
        You are an AI assistant for an insurance verification system. Your role is to help users 
        get information about their insurance policies. You can help with:
        
        1. Getting policy numbers
        2. Checking coverage status
        3. Finding policy expiry dates
        4. General insurance questions
        
        Always be helpful, professional, and secure. If you need additional information from the user
        (like member ID, date of birth, or last name), ask for it politely.
        
        Classify user intents into one of these categories:
        - greeting: Hello, hi, good morning, etc.
        - get_policy_number: Questions about policy numbers
        - check_coverage: Questions about coverage status
        - check_expiry: Questions about policy expiry dates
        - fallback: Anything else
        
        Extract relevant entities like policy numbers, member IDs, dates, etc.
        """
    
    def _create_intent_examples(self) -> Dict[str, List[str]]:
        """Create examples for intent classification"""
        return {
            "greeting": [
                "hello", "hi", "good morning", "good afternoon", "hey there"
            ],
            "get_policy_number": [
                "what's my policy number?", "can you tell me my policy number?",
                "I need my policy number", "policy number please"
            ],
            "check_coverage": [
                "am I covered?", "is my insurance valid?", "do I have coverage?",
                "check my coverage", "is my policy active?"
            ],
            "check_expiry": [
                "when does my policy expire?", "what's my expiry date?",
                "when is my insurance valid until?", "policy expiry date"
            ],
            "fallback": [
                "how are you?", "what can you do?", "help me", "I don't understand"
            ]
        }
    
    async def process_message(self, message: ChatMessage) -> ChatResponse:
        """
        Process a user message and return a response
        """
        try:
            # Classify intent
            intent_classification = await self._classify_intent(message.message)
            
            # Generate response based on intent
            response = await self._generate_response(message, intent_classification)
            
            return ChatResponse(
                response=response["text"],
                intent=intent_classification.intent,
                entities=intent_classification.entities,
                session_id=message.session_id or str(uuid.uuid4()),
                requires_followup=response.get("requires_followup", False),
                followup_question=response.get("followup_question")
            )
            
        except Exception as e:
            logger.error("Chatbot processing failed", error=str(e))
            return ChatResponse(
                response="I'm sorry, I'm having trouble processing your request. Please try again.",
                intent=ChatIntent.FALLBACK,
                entities={},
                session_id=message.session_id or str(uuid.uuid4()),
                requires_followup=False
            )
    
    async def _classify_intent(self, message: str) -> IntentClassification:
        """
        Classify user intent using LLM
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Classify this message and extract entities: '{message}'")
            ])
            
            chain = prompt | self.llm
            result = await chain.ainvoke({"message": message})
            
            # Parse the result to extract intent and entities
            intent, entities = self._parse_classification_result(result.content)
            
            return IntentClassification(
                intent=intent,
                confidence=0.9,  # Would be calculated from LLM confidence
                entities=entities
            )
            
        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            return IntentClassification(
                intent=ChatIntent.FALLBACK,
                confidence=0.0,
                entities={}
            )
    
    def _parse_classification_result(self, result: str) -> tuple:
        """
        Parse LLM result to extract intent and entities
        """
        # Simple parsing - in production, use structured output
        result_lower = result.lower()
        
        if any(word in result_lower for word in ["hello", "hi", "greeting"]):
            intent = ChatIntent.GREETING
        elif any(word in result_lower for word in ["policy number", "policy_number"]):
            intent = ChatIntent.GET_POLICY_NUMBER
        elif any(word in result_lower for word in ["coverage", "covered", "active"]):
            intent = ChatIntent.CHECK_COVERAGE
        elif any(word in result_lower for word in ["expire", "expiry", "expires"]):
            intent = ChatIntent.CHECK_EXPIRY
        else:
            intent = ChatIntent.FALLBACK
        
        # Extract entities (simplified)
        entities = {}
        
        # Enhanced policy number detection - look for 6+ digit numbers
        import re
        policy_numbers = re.findall(r'\b\d{6,}\b', result)
        if policy_numbers:
            entities["policy_number"] = policy_numbers[0]  # Take the first one
        elif "policy" in result_lower and any(char.isdigit() for char in result):
            # Fallback to the original regex if no 6+ digit numbers found
            policy_match = re.search(r'[A-Z0-9]{6,}', result)
            if policy_match:
                entities["policy_number"] = policy_match.group()
        
        return intent, entities
    
    async def _generate_response(self, message: ChatMessage, intent: IntentClassification) -> Dict[str, Any]:
        """
        Generate response based on classified intent
        """
        try:
            if intent.intent == ChatIntent.GREETING:
                return {
                    "text": "Hello! I'm your insurance verification assistant. How can I help you today?",
                    "requires_followup": False
                }
            
            elif intent.intent == ChatIntent.GET_POLICY_NUMBER:
                policy_number = intent.entities.get("policy_number")
                if policy_number:
                    # Simulate different policy statuses based on the policy number
                    # Extract last digit to determine status (for testing purposes)
                    last_digit = int(policy_number[-1]) if policy_number[-1].isdigit() else 0
                    
                    if last_digit in [0, 1, 2]:
                        return {
                            "text": f"Policy {policy_number} is ACTIVE. To provide complete information, I'll need your Member ID, Date of birth, and Last name.",
                            "requires_followup": True,
                            "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                        }
                    elif last_digit in [3, 4, 5]:
                        return {
                            "text": f"Policy {policy_number} is INACTIVE. To provide complete information, I'll need your Member ID, Date of birth, and Last name.",
                            "requires_followup": True,
                            "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                        }
                    elif last_digit in [6, 7, 8]:
                        return {
                            "text": f"Policy {policy_number} is EXPIRED. To provide complete information, I'll need your Member ID, Date of birth, and Last name.",
                            "requires_followup": True,
                            "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                        }
                    else:
                        return {
                            "text": f"Policy {policy_number} is PENDING. To provide complete information, I'll need your Member ID, Date of birth, and Last name.",
                            "requires_followup": True,
                            "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                        }
                else:
                    return {
                        "text": "I'd be happy to help you with your policy. Could you please provide your policy number?",
                        "requires_followup": True,
                        "followup_question": "Please provide your policy number"
                    }
            
            elif intent.intent == ChatIntent.CHECK_COVERAGE:
                if "member_id" in intent.entities:
                    return {
                        "text": "Let me check your coverage status for you.",
                        "requires_followup": False
                    }
                else:
                    return {
                        "text": "I can check your coverage status. Could you please provide your member ID, date of birth, and last name?",
                        "requires_followup": True,
                        "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                    }
            
            elif intent.intent == ChatIntent.CHECK_EXPIRY:
                if "member_id" in intent.entities:
                    return {
                        "text": "Let me check your policy expiry date for you.",
                        "requires_followup": False
                    }
                else:
                    return {
                        "text": "I can check your policy expiry date. Could you please provide your member ID, date of birth, and last name?",
                        "requires_followup": True,
                        "followup_question": "Please provide: Member ID, Date of Birth (YYYY-MM-DD), and Last Name"
                    }
            
            else:  # FALLBACK
                return {
                    "text": "I'm not sure I understand. Could you please rephrase your question or provide your policy number?",
                    "requires_followup": False
                }
                
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return {
                "text": "I'm sorry, I'm having trouble understanding. Could you please rephrase your question?",
                "requires_followup": False
            }
    
    async def get_policy_info_for_chat(self, member_id: str, dob: str, last_name: str) -> Dict[str, Any]:
        """
        Get policy information formatted for chat responses
        """
        try:
            # This would call the policy service
            # For now, return a mock response
            return {
                "policy_number": "POL123456789",
                "coverage_status": "active",
                "expiry_date": "2024-12-31",
                "source": "cache"
            }
        except Exception as e:
            logger.error("Failed to get policy info for chat", error=str(e))
            return {}
