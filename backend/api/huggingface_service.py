from django.conf import settings
from .models import KnowledgeBase, UserSettings
from .utils import is_super_admin, get_user_access_token
import requests
import json
import re
import math


class HuggingFaceService:
    def __init__(self, user=None):
        """
        Initialize HuggingFaceService with user-specific API key.
        
        Args:
            user: User object. If admin, uses admin_ai_access_token from UserSettings if set,
                  otherwise falls back to env token. Otherwise uses assigned token from table.
        """
        # If user is provided and is admin, check for admin_ai_access_token in UserSettings
        if user and is_super_admin(user):
            try:
                user_settings = UserSettings.objects.get(user=user)
                if user_settings.admin_ai_access_token:
                    self.api_key = user_settings.admin_ai_access_token
                else:
                    # Fallback to env token if admin token not set
                    self.api_key = settings.HUGGINGFACE_API_KEY
            except UserSettings.DoesNotExist:
                # No settings found, use env token
                self.api_key = settings.HUGGINGFACE_API_KEY
        elif user:
            # Get assigned token for user
            access_token_obj = get_user_access_token(user)
            if access_token_obj:
                self.api_key = access_token_obj.token
            else:
                # Fallback to env token if no token assigned (shouldn't happen normally)
                self.api_key = settings.HUGGINGFACE_API_KEY
        else:
            # No user provided, use env token (backward compatibility)
            self.api_key = settings.HUGGINGFACE_API_KEY
        
        # Using Qwen3-235B - latest and most powerful Qwen model
        self.model = "Qwen/Qwen3-235B-A22B-Instruct-2507"
        # New Hugging Face router endpoint for chat completions
        self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def clean_markdown_formatting(self, content):
        """
        Remove annoying markdown formatting symbols from AI responses.
        
        Args:
            content: The raw AI response content
            
        Returns:
            Cleaned content without markdown symbols
        """
        if not content:
            return content
            
        # Remove markdown headers (# symbols at start of lines)
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        
        # Remove bold markdown (**text** -> text)
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        
        # Remove italic markdown (*text* -> text) but be careful not to affect other asterisks
        content = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'\1', content)
        
        # Clean up any remaining double asterisks
        content = re.sub(r'\*\*', '', content)
        
        return content.strip()

    def check_identity_question(self, user_message):
        """
        Check if the user is asking about the chatbot's identity.
        
        Args:
            user_message: The user's message content
            
        Returns:
            True if it's an identity question, False otherwise
        """
        if not user_message:
            return False
            
        # Convert to lowercase for case-insensitive matching
        message_lower = user_message.lower().strip()
        
        # Define identity question patterns
        identity_patterns = [
            # Direct identity questions
            'what is your name',
            'what\'s your name',
            'whats your name',
            'who are you',
            'introduce yourself',
            'tell me about yourself',
            'what are you',
            
            # Creation/development questions
            'who built you',
            'who developed you',
            'who created you',
            'who made you',
            'who designed you',
            'who programmed you',
            'who coded you',
            
            # Location questions
            'where is your home',
            'where do you live',
            'where are you from',
            'what is your country',
            'where is your country',
            'what is your city',
            'where is your city',
            'where were you born',
            'where do you come from',
            
            # Family relationship questions
            'who is your father',
            'who is your dad',
            'who is your mother',
            'who is your mom',
            'who is your parent',
            'who is your brother',
            'who is your sister',
            'who is your uncle',
            'who is your aunt',
            'who is your son',
            'who is your daughter',
            'who is your boss',
            'who is your owner',
            'who is your master',
            
            # Variations and additional patterns
            'can you introduce yourself',
            'tell me who you are',
            'what should i call you',
            'do you have a name',
            'what do you call yourself',
            'who do you belong to',
            'who owns you'
        ]
        
        # Check if any pattern matches
        for pattern in identity_patterns:
            if pattern in message_lower:
                return True
                
        return False

    def get_identity_response(self):
        """
        Get the standard identity response for the chatbot.
        
        Returns:
            The identity response string
        """
        return "I am a chatbot developed by Fardin Ibrahimi in Afghanistan, Kabul. I'm here to help you with any questions or tasks you might have. How can I assist you today?"

    def check_knowledge_base(self, user_message):
        """
        Check the knowledge base for a matching answer.
        Uses simple keyword matching - checks if any knowledge base question contains
        keywords from the user's message.
        
        Args:
            user_message: The user's message content
            
        Returns:
            The answer from knowledge base if found, None otherwise
        """
        if not user_message:
            return None
        
        # Get all knowledge base entries
        kb_entries = KnowledgeBase.objects.all()
        
        # Convert user message to lowercase for case-insensitive matching
        user_message_lower = user_message.lower()
        user_keywords = set(user_message_lower.split())
        
        # Check each knowledge base entry
        best_match = None
        best_score = 0
        
        for entry in kb_entries:
            question_lower = entry.question.lower()
            question_keywords = set(question_lower.split())
            
            # Calculate similarity score (simple keyword overlap)
            if question_keywords:
                overlap = len(user_keywords & question_keywords)
                score = overlap / len(question_keywords)
                
                # Also check if user message contains the question or vice versa
                if question_lower in user_message_lower or user_message_lower in question_lower:
                    score += 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = entry
        
        # Return answer if we found a reasonable match (threshold: 0.3)
        if best_match and best_score >= 0.3:
            return best_match.answer
        
        return None
    
    def check_sick_or_patient_message(self, user_message):
        """
        Check if the user is saying they are sick or have a patient.
        
        Args:
            user_message: The user's message content
            
        Returns:
            True if it's a sick/patient message, False otherwise
        """
        if not user_message:
            return False
        
        message_lower = user_message.lower().strip()
        
        # Patterns for sick/patient messages
        sick_patterns = [
            'i am sick',
            'i\'m sick',
            'im sick',
            'i feel sick',
            'i am ill',
            'i\'m ill',
            'im ill',
            'i feel ill',
            'i have a patient',
            'i have patient',
            'my patient',
            'patient needs',
            'emergency',
            'medical help',
            'need medical',
            'i need help',
            'medical emergency',
        ]
        
        # Check if any pattern matches
        for pattern in sick_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    def check_if_collecting_symptoms(self, messages):
        """Always return False since disease matching is removed"""
        return False
    
    def extract_symptoms_from_message(self, user_message):
        """
        Extract symptoms mentioned in the user's message.
        Also handles yes/no answers to follow-up questions by checking the previous assistant message.
        
        Args:
            user_message: The user's message content
            
        Returns:
            List of symptom keywords found
        """
        if not user_message:
            return []
        
        message_lower = user_message.lower().strip()
        
        # Check if this is a yes/no answer (yes, yeah, yep, no, nope, etc.)
        yes_patterns = ['yes', 'yeah', 'yep', 'yup', 'sure', 'correct', 'right', 'true', 'indeed', 'absolutely', 'definitely']
        no_patterns = ['no', 'nope', 'nah', 'not', "don't", "doesn't", 'none', 'nothing']
        
        is_yes = any(pattern in message_lower for pattern in yes_patterns)
        is_no = any(pattern in message_lower for pattern in no_patterns)
        
        # Disease matching removed - return empty list
        return []
    
    def extract_symptoms_from_conversation(self, messages):
        """
        Extract symptoms from the entire conversation, handling yes/no answers.
        Disease matching removed - returns empty lists.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Tuple of (mentioned_symptoms, asked_symptoms)
        """
        # Disease matching removed - return empty lists
        return [], []
    
    
    def generate_response(self, messages):
        """
        Generate a response from the Hugging Face API using chat completions.
        First checks the knowledge base, then identity questions, then sick/patient messages, then uses AI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            The generated response text
        """
        # Check if the latest message is from user
        if messages and len(messages) > 0:
            latest_message = messages[-1]
            if latest_message.get('role') == 'user':
                user_content = latest_message.get('content', '')
                
                # First check knowledge base
                kb_answer = self.check_knowledge_base(user_content)
                if kb_answer:
                    return kb_answer
                
                # Then check identity questions
                if self.check_identity_question(user_content):
                    return self.get_identity_response()
                
                # Then check for sick/patient messages
                if self.check_sick_or_patient_message(user_content):
                    return "I'm sorry to hear that you're not feeling well or that you have a patient who needs help. Could you please tell me what symptoms you (or your patient) are experiencing? For example, fever, cough, headache, chest pain, etc."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for chat completions API
        formatted_messages = []
        
        # Add system prompt to make AI respond like a medical expert
        system_prompt = """You are a professional medical assistant chatbot designed to help users find appropriate medical care. Your role is to:

1. Provide helpful, accurate medical information and guidance
2. Ask relevant questions when needed, but avoid repetitive or excessive questioning
3. Respond like an experienced medical professional - be concise, clear, and empathetic
4. If you don't have enough information, provide general guidance rather than asking the same question repeatedly
5. Focus on helping users find the right medical care
6. Avoid loops - if you've asked about symptoms already, move forward with recommendations based on available information

Remember: You are here to help, not to interrogate. Be professional, helpful, and efficient."""
        
        formatted_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        for msg in messages:
            formatted_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response from chat completions format
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                if content:
                    # Clean markdown formatting before returning
                    content = self.clean_markdown_formatting(content)
                    return content
                else:
                    return "I apologize, but I couldn't generate a response. Please try again."
            else:
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except requests.exceptions.Timeout:
            return "I apologize, but the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get('message', str(error_msg))
                except:
                    pass
            
            if "loading" in error_msg.lower():
                return "The AI model is loading. Please try again in a moment."
            elif "rate limit" in error_msg.lower():
                return "Rate limit reached. Please wait a moment and try again."
            elif "quota" in error_msg.lower():
                return "API quota exceeded. Please check your Hugging Face API key."
            else:
                return f"I apologize, but I encountered an error: {error_msg}"

    def generate_response_stream(self, messages):
        """
        Generate a streaming response from the Hugging Face API.
        First checks the knowledge base, then identity questions, then sick/patient messages, then uses AI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Yields:
            Chunks of the generated response text
        """
        # Check if the latest message is from user
        if messages and len(messages) > 0:
            latest_message = messages[-1]
            if latest_message.get('role') == 'user':
                user_content = latest_message.get('content', '')
                
                # First check knowledge base
                kb_answer = self.check_knowledge_base(user_content)
                if kb_answer:
                    # Yield the knowledge base answer as chunks for streaming compatibility
                    yield kb_answer
                    return
                
                # Then check identity questions
                if self.check_identity_question(user_content):
                    # Yield the identity response as chunks for streaming compatibility
                    identity_response = self.get_identity_response()
                    yield identity_response
                    return
                
                # Then check for sick/patient messages
                if self.check_sick_or_patient_message(user_content):
                    yield "I'm sorry to hear that you're not feeling well or that you have a patient who needs help. Could you please tell me what symptoms you (or your patient) are experiencing? For example, fever, cough, headache, chest pain, etc."
                    return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for chat completions API
        formatted_messages = []
        
        # Add system prompt to make AI respond like a medical expert
        system_prompt = """You are a professional medical assistant chatbot designed to help users find appropriate medical care. Your role is to:

1. Provide helpful, accurate medical information and guidance
2. Ask relevant questions when needed, but avoid repetitive or excessive questioning
3. Respond like an experienced medical professional - be concise, clear, and empathetic
4. If you don't have enough information, provide general guidance rather than asking the same question repeatedly
5. Focus on helping users find the right medical care
6. Avoid loops - if you've asked about symptoms already, move forward with recommendations based on available information

Remember: You are here to help, not to interrogate. Be professional, helpful, and efficient."""
        
        formatted_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        for msg in messages:
            formatted_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": True  # Enable streaming
        }
        
        try:
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=data, 
                timeout=60,
                stream=True  # Enable streaming response
            )
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    # Skip empty lines and comments
                    if not line.strip() or line.startswith(':'):
                        continue
                    
                    # Parse SSE format (data: {...})
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        # Check for end of stream
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data_obj = json.loads(data_str)
                            if "choices" in data_obj and len(data_obj["choices"]) > 0:
                                delta = data_obj["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.Timeout:
            yield "I apologize, but the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get('message', str(error_msg))
                except:
                    pass
            
            if "loading" in error_msg.lower():
                yield "The AI model is loading. Please try again in a moment."
            elif "rate limit" in error_msg.lower():
                yield "Rate limit reached. Please wait a moment and try again."
            elif "quota" in error_msg.lower():
                yield "API quota exceeded. Please check your Hugging Face API key."
            else:
                yield f"I apologize, but I encountered an error: {error_msg}"

    def summarize_text(self, text, max_lines):
        """
        Summarize text to a specific number of lines using the Hugging Face API.
        
        Args:
            text: The text to summarize
            max_lines: Maximum number of lines for the summary
            
        Returns:
            The summarized text
        """
        if not text or not text.strip():
            return "No text provided to summarize."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create a prompt for summarization
        system_prompt = f"""You are a text summarization assistant. Your task is to summarize the given text into exactly {max_lines} lines or fewer. 
The summary should be concise, clear, and preserve the most important information from the original text.
Make sure the summary is well-formatted and readable."""
        
        user_prompt = f"""Please summarize the following text into {max_lines} lines or fewer:

{text}"""
        
        formatted_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 2048,
            "temperature": 0.3,  # Lower temperature for more focused summaries
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response from chat completions format
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                if content:
                    # Clean markdown formatting before returning
                    content = self.clean_markdown_formatting(content)
                    return content
                else:
                    return "I apologize, but I couldn't generate a summary. Please try again."
            else:
                return "I apologize, but I couldn't generate a summary. Please try again."
                
        except requests.exceptions.Timeout:
            return "I apologize, but the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get('message', str(error_msg))
                except:
                    pass
            
            if "loading" in error_msg.lower():
                return "The AI model is loading. Please try again in a moment."
            elif "rate limit" in error_msg.lower():
                return "Rate limit reached. Please wait a moment and try again."
            elif "quota" in error_msg.lower():
                return "API quota exceeded. Please check your Hugging Face API key."
            else:
                return f"I apologize, but I encountered an error: {error_msg}"

