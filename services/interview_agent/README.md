# Interview Agent

AI-powered technical interviewer agent for the AI Interviewer MCP Mesh system. Conducts dynamic interviews based on role requirements and candidate profiles with Redis session management.

## Features

- **Dynamic Interview Conductor**: Generates contextually relevant follow-up questions
- **Session Management**: Redis-based persistent interview sessions
- **Role-Aware Questioning**: Tailors questions to specific job requirements
- **Conversation Tracking**: Maintains complete interview history
- **LLM Integration**: Uses configured LLM service for intelligent question generation

## Architecture

The Interview Agent operates as a stateless service with Redis providing session persistence:

1. **Session Creation**: Creates new interview sessions with role and resume context
2. **Question Generation**: Uses LLM service to generate relevant interview questions
3. **Conversation Management**: Tracks Q&A history in Redis with TTL
4. **Context Preservation**: Maintains full context for better follow-up questions

## API Endpoints

### `conduct_interview`
Main interview conductor function:

```python
conduct_interview(
    resume_content: str,          # Candidate's resume text/data
    role_description: str,        # Job role requirements
    user_session_id: str,         # Session identifier
    candidate_answer: str = None  # Optional previous answer
) -> Dict[str, Any]
```

**Flow:**
1. Store candidate answer if provided
2. Retrieve full conversation history from Redis
3. Generate next question using LLM with full context
4. Store question in Redis and return to caller

### `get_interview_session`
Retrieve session data and conversation history.

### `end_interview_session`
Mark interview as completed and generate summary.

### `get_agent_status`
Get agent health status and Redis connectivity.

## Configuration

Environment variables:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=optional
REDIS_DB=0

# MCP Mesh Configuration
MCP_MESH_REGISTRY_URL=http://registry:8080
```

## Dependencies

- **llm-service**: Required for question generation
- **Redis**: Required for session management
- **MCP Mesh Registry**: For service discovery

## Session Data Structure

Redis stores interview sessions as JSON:

```json
{
  "session_id": "uuid-string",
  "role_description": "Senior Python Developer...",
  "resume_content": "Candidate background...",
  "conversation": [
    {
      "type": "question",
      "content": "Tell me about your Python experience...",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    {
      "type": "answer", 
      "content": "I have 5 years of Python development...",
      "timestamp": "2024-01-01T10:01:00Z"
    }
  ],
  "created_at": "2024-01-01T10:00:00Z",
  "last_updated": "2024-01-01T10:01:00Z",
  "status": "active"
}
```

## Question Types

The agent generates various question types:

- **opener**: Initial background questions
- **technical**: Technology-specific knowledge
- **experience**: Past work and projects
- **problem_solving**: Hypothetical scenarios
- **behavioral**: Soft skills and teamwork
- **clarification**: Follow-up for deeper understanding

## Usage Examples

### Start New Interview
```python
response = conduct_interview(
    resume_content="Senior developer with 8+ years...",
    role_description="We need a Python backend engineer...",
    user_session_id="interview-123"
)
# Returns first question
```

### Continue Interview
```python
response = conduct_interview(
    resume_content="Senior developer with 8+ years...",
    role_description="We need a Python backend engineer...",
    user_session_id="interview-123",
    candidate_answer="I've worked with Django and FastAPI..."
)
# Stores answer, returns follow-up question
```

### Get Session Data
```python
session = get_interview_session("interview-123")
print(f"Questions asked: {session['statistics']['total_questions']}")
```

## Integration

The Interview Agent integrates with the AI Interviewer system:

1. **API Server** calls `conduct_interview` with role/resume/answer
2. **Agent** manages session state in Redis
3. **LLM Service** generates contextually relevant questions
4. **API Server** tracks time limits and controls interview flow

## Development

### Local Development
```bash
pip install -e .[dev]
python -m interview_agent
```

### Docker Development
```bash
docker build -t interview-agent .
docker run -p 8084:8084 -e REDIS_HOST=redis interview-agent
```

### Testing
```bash
pytest tests/ -v --cov
```

## Error Handling

- **Redis Unavailable**: Graceful degradation with error responses
- **LLM Service Down**: Returns error instead of crashing
- **Session Not Found**: Creates new session automatically
- **Invalid Data**: Comprehensive error messages and logging

## Performance

- **Session TTL**: 2 hours (configurable)
- **Redis Connection**: Connection pooling with timeout
- **Question Generation**: ~2-5 seconds per question
- **Memory Usage**: Stateless design, minimal memory footprint

## Monitoring

The agent provides comprehensive status information:

- Redis connectivity and performance
- Session statistics and active sessions
- LLM service dependency health  
- Question generation success rates