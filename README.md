# 🎬 Contentizer - AI-Powered Content Creator Workbench

**An intelligent platform for automated YouTube content creation using AI**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://typescriptlang.org)

> Transform trending YouTube content into complete, ready-to-upload videos using AI-powered analysis, script generation, and media creation.

## 🚀 Features

### **🎯 Content Analysis**
- **YouTube Trending Analysis**: Automatically analyze top content across 5 categories
- **Theme Extraction**: AI-powered identification of top 3 themes per category
- **Flexible Input**: Support for automated analysis, manual topics, or complete scripts

### **📝 Script Generation**
- **AI-Powered Writing**: Generate conversational scripts between two speakers
- **Duration Control**: Ensure minimum 3-minute video content
- **Quality Validation**: Built-in script length and content validation

### **🎨 Media Creation**
- **Audio Generation**: Convert scripts to natural conversational audio
- **Visual Assets**: Generate relevant background images and video clips
- **Multi-Modal AI**: Leverages Gemini/OpenAI APIs for diverse content creation

### **🎞️ Video Production**
- **Automated Composition**: Synchronize audio with visual assets using FFmpeg
- **Quality Control**: Ensure proper resolution, format, and duration
- **Background Processing**: Async task management with real-time progress tracking

### **📤 Publishing**
- **YouTube Integration**: Direct upload to YouTube channels
- **Metadata Management**: Automated title, description, and tag generation
- **Status Tracking**: Real-time upload progress and error handling

## 🏗️ Architecture

### **Backend (Python + FastAPI)**
```
backend/
├── src/
│   ├── api/           # REST API endpoints
│   ├── models/        # SQLAlchemy database models
│   ├── services/      # Business logic and AI integrations
│   └── lib/           # Infrastructure (database, storage, tasks)
├── tests/             # Comprehensive test suite
└── main.py           # Application entry point
```

### **Frontend (React + TypeScript)**
```
frontend/
├── src/
│   ├── components/    # React UI components
│   ├── pages/         # Application pages
│   ├── services/      # API client and WebSocket
│   └── types/         # TypeScript definitions
└── package.json
```

### **Core Services**
- **YouTubeService**: Trending analysis and upload management
- **GeminiService**: AI content generation (scripts, audio, visuals)
- **MediaService**: Asset creation and management
- **VideoService**: FFmpeg-based video composition
- **ScriptService**: Script processing and validation

## 🛠️ Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- `uv` package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

### **Backend Setup**
```bash
# Clone repository
git clone git@github.com:Asdafers/contenitzer.git
cd contenitzer/backend

# Install dependencies
uv sync

# Start server
uv run python main.py
```

Server runs on `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### **Frontend Setup**
```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:3000`

### **Environment Configuration**
```bash
# Optional environment variables
export DATABASE_URL="sqlite:///./contentizer.db"
export STORAGE_PATH="/tmp/contentizer"
export GEMINI_API_KEY="your-gemini-key"        # For AI generation
export YOUTUBE_API_KEY="your-youtube-key"      # For trending analysis
export GEMINI_IMAGE_MODEL="gemini-2.5-flash-image"  # Primary model for images/videos
```

## 🧪 Testing

### **Run Backend Tests**
```bash
cd backend

# All tests
uv run pytest

# Specific test types
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/contract/      # API contract tests
```

### **API Testing**
```bash
# Health check
curl http://localhost:8000/health

# Manual script generation (no API key needed)
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "manual_script",
    "manual_input": "Speaker 1: Welcome to our show. Speaker 2: Thank you for having me."
  }'
```

## 📊 Database Schema

### **Core Entities**
- **UserConfig**: API keys and user preferences
- **ContentCategory**: YouTube content categorization
- **TrendingContent**: Analyzed trending videos
- **GeneratedTheme**: Extracted content themes
- **VideoScript**: Generated or manual scripts
- **VideoProject**: Complete video project container
- **MediaAsset**: Individual audio/image/video components
- **ComposedVideo**: Final rendered video ready for upload

### **Relationships**
```
ContentCategory (1) → (many) TrendingContent
TrendingContent (1) → (many) GeneratedTheme
GeneratedTheme (1) → (many) VideoScript
VideoScript (1) → (1) VideoProject
VideoProject (1) → (many) MediaAsset
VideoProject (1) → (1) ComposedVideo
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trending/analyze` | POST | Analyze YouTube trending content |
| `/api/scripts/generate` | POST | Generate or process scripts |
| `/api/media/generate` | POST | Create audio/visual assets |
| `/api/videos/compose` | POST | Compose final video |
| `/api/videos/upload` | POST | Upload to YouTube |
| `/health` | GET | System health check |

## 🔧 Technology Stack

### **Backend**
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: ORM with async support
- **Pydantic**: Data validation and serialization
- **uv**: Fast Python package management
- **pytest**: Comprehensive testing framework

### **Frontend**
- **React 18**: Modern UI library with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client with interceptors

### **AI & Media**
- **Gemini API**: Google's latest AI models for multi-modal content generation
- **Gemini 2.5 Flash Image**: Primary model for image and video generation
- **YouTube Data API v3**: Trending analysis and upload
- **FFmpeg**: Video composition and processing

### **Infrastructure**
- **SQLite/PostgreSQL**: Flexible database options
- **WebSocket**: Real-time progress updates
- **Async Task Queue**: Background job processing
- **Comprehensive Middleware**: Logging, rate limiting, security

## 📈 Performance

- **Async Operations**: All I/O operations are non-blocking
- **Background Processing**: Long-running tasks don't block API responses
- **Efficient Storage**: Organized file management with cleanup utilities
- **Resource Monitoring**: Built-in performance tracking and health checks

## 🔒 Security

- **Input Validation**: Comprehensive request validation with Pydantic
- **Rate Limiting**: Configurable request rate limits
- **Security Headers**: CORS, XSS protection, content type validation
- **API Key Encryption**: Secure storage of user credentials
- **Error Handling**: Sanitized error responses without sensitive data exposure

## 🚧 Development Workflow

### **Adding New Features**
1. Create feature specification in `specs/`
2. Write failing tests first (TDD)
3. Implement models, services, and API endpoints
4. Add frontend components and integration
5. Update documentation and deployment guides

### **Code Quality**
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **ESLint**: Frontend linting
- **Comprehensive test coverage**: Unit, integration, and contract tests

## 📚 Documentation

- **API Docs**: Auto-generated Swagger/OpenAPI at `/docs`
- **Database Schema**: Complete entity relationship documentation
- **Deployment Guide**: Production setup instructions
- **Development Guide**: Contributing and extension guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/code) assistance
- Powered by Google Gemini AI APIs (Gemini 2.5 Flash Image model)
- YouTube Data API for trending content analysis
- FFmpeg for professional video processing

---

**Ready to revolutionize your content creation workflow? Get started today!** 🚀