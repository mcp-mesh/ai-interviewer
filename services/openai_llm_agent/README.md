# OpenAI LLM Agent

A generic MCP Mesh agent for LLM processing operations using OpenAI ChatGPT API. This agent provides identical functionality to the Claude LLM agent but uses OpenAI's models instead.

## Features

- **Generic LLM Processing**: Process text with dynamic tool support
- **Tool Calling**: Support for structured output via OpenAI function calling
- **Multi-turn Conversations**: Handle conversation history and context
- **Retry Logic**: Built-in retry mechanism for API reliability
- **MCP Mesh Integration**: Full integration with the MCP Mesh framework

## Configuration

The agent uses environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `OPENAI_MAX_TOKENS` | `4000` | Maximum tokens in response |
| `OPENAI_TEMPERATURE` | `0.7` | Response randomness (0.0-1.0) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Available Models

- `gpt-4o` - Latest GPT-4 Omni model (default)
- `gpt-4o-mini` - Smaller, faster GPT-4 variant
- `gpt-4-turbo` - GPT-4 Turbo model
- `gpt-3.5-turbo` - GPT-3.5 Turbo model

## API Endpoints

### `process_with_tools`

Generic LLM processing with dynamic tool definitions.

**Parameters:**
- `text` (str): Primary content to process
- `system_prompt` (str, optional): System prompt for context
- `tools` (List[Dict], optional): Tool definitions in OpenAI format
- `messages` (List[Dict], optional): Pre-built message array
- `force_tool_use` (bool): Whether to force tool usage when tools are provided
- `model` (str): OpenAI model to use
- `max_tokens` (int): Maximum tokens in response
- `temperature` (float): Response randomness

### `get_llm_status`

Get current agent status and configuration.

## Usage Examples

### Basic Text Processing

```python
result = process_with_tools(
    text="Analyze this resume for key skills",
    system_prompt="You are an expert resume analyzer"
)
```

### Structured Output with Tools

```python
tools = [{
    "type": "function",
    "function": {
        "name": "extract_skills",
        "description": "Extract skills from resume",
        "parameters": {
            "type": "object",
            "properties": {
                "skills": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}]

result = process_with_tools(
    text="Resume text here...",
    tools=tools,
    force_tool_use=True
)
```

### Multi-turn Conversation

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's the weather like?"}
]

result = process_with_tools(messages=messages)
```

## Docker Usage

The agent is containerized and can be run with Docker:

```bash
docker build -t openai-llm-agent .
docker run -e OPENAI_API_KEY=your_key_here -p 9095:9095 openai-llm-agent
```

## Development

### Installing Dependencies

```bash
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

## License

MIT License