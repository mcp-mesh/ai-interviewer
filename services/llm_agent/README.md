# LLM Agent - Generic AI Processing Service

A generic LLM processing MCP Mesh agent for the AI Interviewer system, providing Claude API integration with dynamic tool support.

## Features

- **Generic Tool Interface**: Accepts dynamic tool definitions from calling agents
- **Claude API Integration**: Uses Anthropic's Claude models for text processing
- **Structured Output**: Supports tool calls for reliable structured data extraction
- **Multi-turn Conversations**: Handles complex dialogue scenarios
- **Retry Logic**: Built-in retry mechanism for API reliability
- **MCP Mesh Integration**: Full dependency injection and service discovery

## Architecture

### Service Identity
- **Name**: `llm-claude-agent`
- **Capability**: `llm-service`
- **Version**: `1.5` (Claude identifier)
- **Port**: `9094`
- **Tags**: `["llm-service", "claude", "anthropic", "text-processing", "ai-analysis"]`

### Core Tool: `process_with_tools`

```python
def process_with_tools(
    text: str,
    system_prompt: str = None,
    tools: List[Dict] = None,
    messages: List[Dict[str, str]] = None,
    force_tool_use: bool = True,
    model: str = "claude-3-sonnet-20240229",
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> Dict[str, Any]:
```

## Usage Examples

### Basic Text Processing
```python
# From another MCP Mesh agent
@mesh.tool(dependencies=["llm-service"])
async def analyze_text(text: str, llm_service: mesh.McpMeshAgent = None):
    response = await llm_service.process_with_tools(
        text=text,
        system_prompt="Analyze the following text for key themes."
    )
    return response["content"]
```

### Structured Data Extraction
```python
# Define tool schema in calling agent
resume_tool = {
    "name": "extract_resume_data",
    "description": "Extract structured information from resume text",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company": {"type": "string"},
                        "duration": {"type": "string"}
                    }
                }
            }
        }
    }
}

@mesh.tool(dependencies=["llm-service"])
async def extract_resume_info(resume_text: str, llm_service: mesh.McpMeshAgent = None):
    response = await llm_service.process_with_tools(
        text=resume_text,
        system_prompt="Extract structured information from this resume.",
        tools=[resume_tool],
        force_tool_use=True
    )
    
    # Parse the structured response
    if response["success"] and response["tool_calls"]:
        return response["tool_calls"][0]["parameters"]
    return None
```

### Multi-turn Conversation
```python
messages = [
    {"role": "user", "content": "Hello, I need help analyzing a document."},
    {"role": "assistant", "content": "I'd be happy to help analyze your document. Please share the content."},
    {"role": "user", "content": "Here's the document content..."}
]

response = await llm_service.process_with_tools(
    text="",  # Not used when messages provided
    messages=messages,
    system_prompt="You are a helpful document analyst."
)
```

## Configuration

### Environment Variables
```bash
# Required
CLAUDE_API_KEY=sk-ant-api03-...

# Optional
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7
LOG_LEVEL=INFO
```

### Available Models
- `claude-3-opus-20240229` - Most capable, highest cost
- `claude-3-sonnet-20240229` - Balanced performance/cost (default)
- `claude-3-haiku-20240307` - Fastest, lowest cost

## Response Format

```json
{
  "success": true,
  "content": "Text response from Claude...",
  "tool_calls": [
    {
      "id": "toolu_123",
      "name": "extract_data",
      "parameters": {
        "summary": "Professional summary...",
        "skills": ["Python", "Machine Learning"]
      }
    }
  ],
  "model": "claude-3-sonnet-20240229",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 75,
    "total_tokens": 225
  },
  "stop_reason": "tool_use",
  "processed_at": "2024-01-15T10:30:00Z",
  "input_length": 1250,
  "tools_provided": 1,
  "tool_use_forced": true
}
```

## Integration with PDF Extractor

The PDF extractor can use this LLM agent for structured analysis:

```python
# In PDF Extractor Agent
@mesh.tool(dependencies=["llm-service"])
async def analyze_resume_pdf(file_path: str, llm_service: mesh.McpMeshAgent = None):
    # Extract PDF text
    pdf_content = extract_text_from_pdf(file_path)
    
    if llm_service and pdf_content["success"]:
        # Define analysis tool
        analysis_tool = {
            "name": "analyze_resume",
            "description": "Analyze resume content and extract key information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "professional_summary": {"type": "string"},
                    "technical_skills": {"type": "array", "items": {"type": "string"}},
                    "years_experience": {"type": "number"},
                    "education_level": {"type": "string"},
                    "key_achievements": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
        
        # Call LLM service
        analysis = await llm_service.process_with_tools(
            text=pdf_content["text_content"],
            system_prompt="You are an expert resume analyzer. Extract and structure the key information from this resume.",
            tools=[analysis_tool],
            force_tool_use=True
        )
        
        return {
            **pdf_content,
            "structured_analysis": analysis["tool_calls"][0]["parameters"] if analysis["success"] else None
        }
```

## Development

### Local Development
```bash
# Install in editable mode
cd services/llm_agent
pip install -e .[dev]

# Set environment variables
export CLAUDE_API_KEY=sk-ant-api03-...
export LOG_LEVEL=DEBUG

# Run the agent
python -m llm_agent
```

### Docker Development
```bash
# Build
docker build -t llm-agent .

# Run
docker run -e CLAUDE_API_KEY=sk-ant-api03-... -p 9094:9094 llm-agent
```

### Testing
```bash
# Test MCP endpoint
curl -X POST http://localhost:9094/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "process_with_tools",
      "arguments": {
        "text": "Hello, world!",
        "system_prompt": "Respond enthusiastically."
      }
    }
  }'

# Test health endpoint
curl http://localhost:9094/health
```

## Production Deployment

The LLM agent is designed to be deployed as part of the AI Interviewer system using Docker Compose with MCP Mesh service discovery.

### Security Considerations
- Claude API key stored as environment variable
- Non-root container user
- No sensitive data logging
- Request/response size limits
- Rate limiting through retry logic

### Monitoring
- Health check endpoint at `/health`
- Comprehensive logging with structured format
- API usage tracking in responses
- Error handling with detailed error messages