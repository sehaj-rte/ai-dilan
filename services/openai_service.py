from openai import OpenAI
from typing import List, Dict, Any
from config.settings import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def create_embedding(text: str):
    """Create embedding for text using OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return None

def generate_response(expert_context: str, user_question: str, expert_name: str = "AI Assistant"):
    """Generate AI response using OpenAI GPT"""
    try:
        system_prompt = f"""You are {expert_name}, an AI assistant with expertise in your field. 
        Use the following context to answer questions accurately and helpfully.
        
        Context: {expert_context}
        
        Guidelines:
        - Answer as if you are the expert
        - Be conversational and helpful
        - If you don't know something, say so
        - Keep responses concise but informative
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I'm having trouble processing your request right now."

def transcribe_audio(audio_file):
    """Transcribe audio using OpenAI Whisper"""
    try:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def generate_speech(text: str, voice: str = "alloy"):
    """Generate speech from text using OpenAI TTS"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def process_expert_content(content: str, content_type: str = "text"):
    """Process and chunk expert content for storage"""
    try:
        # Simple text chunking - split by sentences or paragraphs
        if content_type == "text":
            # Split into chunks of ~500 characters
            chunks = []
            words = content.split()
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) > 500 and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1
            
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            return chunks
        
        return [content]  # For other content types, return as-is
    except Exception as e:
        print(f"Error processing content: {e}")
        return [content]
