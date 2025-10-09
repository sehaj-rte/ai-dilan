# Dilan AI Backend

A FastAPI-based backend for the Dilan AI voice assistant platform with Pinecone vector database integration.

## Features

- 🤖 **Expert Management**: Create and manage AI experts with custom knowledge bases
- 💬 **Chat System**: Real-time conversations with AI experts
- 🎤 **Voice Processing**: Speech-to-text and text-to-speech capabilities
- 🔐 **Authentication**: JWT-based user authentication
- 🔍 **Vector Search**: Semantic search using Pinecone
- 📚 **Knowledge Storage**: Store and retrieve expert knowledge efficiently

## Project Structure

```
delphi-ai-backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Dependencies
├── .env                   # Environment variables
├── config/
│   └── settings.py        # Configuration settings
├── routes/
│   ├── auth.py           # Authentication routes
│   ├── experts.py        # Expert management routes
│   ├── chat.py           # Chat/conversation routes
│   └── voice.py          # Voice processing routes
├── controllers/
│   ├── auth_controller.py
│   ├── expert_controller.py
│   ├── chat_controller.py
│   └── voice_controller.py
├── services/
│   ├── pinecone_service.py  # Pinecone vector DB operations
│   └── openai_service.py    # OpenAI API integration
├── models/
│   ├── user.py           # User data models
│   ├── expert.py         # Expert profile models
│   └── chat.py           # Chat/message models
└── utils/
    ├── helpers.py        # Utility functions
    └── validators.py     # Input validation
```

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env` file and update the API keys:
   - Add your OpenAI API key
   - Pinecone key is already configured

3. **Run the Server**
   ```bash
   python main.py
   ```
   Or with uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/verify` - Verify JWT token

### Experts
- `GET /experts` - List all experts
- `POST /experts` - Create new expert
- `GET /experts/{expert_id}` - Get expert details
- `POST /experts/{expert_id}/content` - Upload expert content
- `POST /experts/{expert_id}/ask` - Ask question to expert

### Chat
- `POST /chat/{expert_id}` - Send message to expert
- `GET /chat/{expert_id}/history` - Get chat history

### Voice
- `POST /voice/transcribe` - Convert voice to text
- `POST /voice/synthesize` - Convert text to voice
- `GET /voice/voices` - Get available voices

## Usage Examples

### Create an Expert
```bash
curl -X POST "http://localhost:8000/experts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Sarah Johnson",
    "role": "AI Researcher",
    "bio": "Expert in machine learning and AI ethics"
  }'
```

### Upload Expert Content
```bash
curl -X POST "http://localhost:8000/experts/{expert_id}/content" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "text",
    "content": "Machine learning is a subset of artificial intelligence..."
  }'
```

### Chat with Expert
```bash
curl -X POST "http://localhost:8000/chat/{expert_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "message_type": "text"
  }'
```

## Configuration

Key environment variables in `.env`:

- `PINECONE_API_KEY`: Your Pinecone API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT secret key
- `DEBUG`: Enable debug mode

## Architecture

- **No Classes**: Simple function-based approach as requested
- **Modular Design**: Separated routes, controllers, and services
- **Vector Database**: Pinecone for semantic search
- **AI Integration**: OpenAI for embeddings and responses
- **Simple Storage**: In-memory storage (easily replaceable with database)

## Development

The backend is designed to be simple and extensible:

1. **Routes**: Handle HTTP requests and responses
2. **Controllers**: Business logic and data processing
3. **Services**: External API integrations (Pinecone, OpenAI)
4. **Models**: Data validation using Pydantic
5. **Utils**: Helper functions and validators

## Next Steps

- Add database integration (PostgreSQL/MongoDB)
- Implement WebSocket for real-time chat
- Add file upload for documents/audio
- Implement rate limiting
- Add comprehensive logging
- Add unit tests
