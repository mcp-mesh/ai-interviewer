# AI Interviewer System

Enterprise-grade technical screening system built on MCP Mesh architecture, designed for large organizations to efficiently screen entry and mid-level engineers.

## 📋 Quick Overview

The AI Interviewer is a distributed system that uses multiple specialized AI agents to conduct technical interviews. It features secure OAuth authentication, intelligent document processing, real-time interview chat, and comprehensive evaluation.

## 🏗️ System Architecture

- **Server-Side OAuth**: Secure authentication with Google, GitHub, Microsoft, Apple
- **Document Processing**: PDF/Word resume parsing with Claude AI
- **MCP Mesh Services**: Distributed microservices for scalability
- **Real-Time Chat**: WebSocket-based interview interface
- **Fraud Prevention**: Foundation for tab/window switching detection

## 📁 Documentation Structure

| Document | Description |
|----------|-------------|
| [`AI_INTERVIEWER_ARCHITECTURE.md`](./AI_INTERVIEWER_ARCHITECTURE.md) | **Main architecture document** - Complete system design, components, and technical implementation |
| [`DEVELOPMENT_GUIDE.md`](./DEVELOPMENT_GUIDE.md) | **Development setup guide** - OAuth testing options, local HTTPS, mock auth, and workflows |
| [`AI_INTERVIEWER_ARCHITECTURE_UPDATE.md`](./AI_INTERVIEWER_ARCHITECTURE_UPDATE.md) | **Recent updates** - DEV_MODE environment variable changes |

## 🚀 Quick Start (Development)

```bash
# Clone and setup
git clone <repo>
cd ai-interviewer

# Development mode (bypasses OAuth)
export DEV_MODE=true
uvicorn main:app --reload --port 8000

# Visit http://localhost:8000
# Auto-creates dev user session - ready to code!
```

## 🔐 Authentication Modes

### Development Mode
- **Environment**: `DEV_MODE=true`  
- **Authentication**: Auto-created dev user session
- **Use Case**: Local development and testing

### Production Mode  
- **Environment**: `DEV_MODE=false`
- **Authentication**: OAuth with Google, GitHub, Microsoft, Apple
- **Requirements**: HTTPS domain with valid SSL certificates

## 🎯 Target Use Case

**Enterprise Technical Screening**
- Large organizations receiving high-volume resumes
- Screening entry to mid-level engineering candidates
- Structured technical interviews with AI evaluation
- Fraud prevention and security measures

## 🛠️ Technology Stack

- **Backend**: FastAPI + MCP Mesh + Redis sessions
- **Frontend**: Static HTML/CSS/JavaScript (no complex frameworks)
- **AI Processing**: Claude API for resume parsing and question generation
- **Authentication**: Server-side OAuth2 Authorization Code flow
- **Storage**: Redis for sessions, PostgreSQL for registry
- **Deployment**: Kubernetes with SSL/HTTPS

## 📖 Getting Started

1. **Read the Architecture**: Start with [`AI_INTERVIEWER_ARCHITECTURE.md`](./AI_INTERVIEWER_ARCHITECTURE.md)
2. **Setup Development**: Follow [`DEVELOPMENT_GUIDE.md`](./DEVELOPMENT_GUIDE.md)
3. **Implementation**: Use the code examples and deployment guides
4. **Production**: Configure OAuth providers and SSL certificates

## 🔄 Latest Updates

- **DEV_MODE Environment Variable**: Simplified development authentication bypass
- **Server-Side Sessions**: Secure OAuth implementation with httpOnly cookies  
- **Static Frontend**: Lightweight HTML/JS instead of complex React setup
- **Enterprise Focus**: Registered users only, fraud prevention foundation

## 📞 Support

For questions about the AI Interviewer system architecture, refer to the documentation or create an issue in the repository.

---

**Note**: This system is designed for legitimate technical screening purposes. It includes security measures and is intended for authorized use by organizations conducting interviews with candidate consent.