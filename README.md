# DreamSeed Portal V2

A goal-based AI-powered learning platform built as a modern monorepo with microservices architecture.

## 🏗️ Architecture

### Backend Services (FastAPI)
- **AI Orchestrator** (Port 8000) - Routes requests to specialized LLMs
- **Career API** (Port 8001) - Manages career paths and guidance
- **Learning API** (Port 8002) - Handles learning modules and content
- **Progress API** (Port 8003) - Tracks user learning progress

### Frontend Applications (React + Vite)
- **Portal App** - Main application with onboarding form
- **Learner App** - Dedicated learning experience interface

### Shared Packages
- **shared-types** - TypeScript types and Zod schemas
- **shared-ui** - Reusable React components

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Docker (optional)

### Development Setup

1. **Clone and install dependencies**
   ```bash
   git clone <repository-url>
   cd dreamseed
   npm install
   ```

2. **Build shared packages**
   ```bash
   npm run build --workspace=@dreamseed/shared-types
   npm run build --workspace=@dreamseed/shared-ui
   ```

3. **Start backend services**
   ```bash
   # Terminal 1 - AI Orchestrator
   cd services/ai-orchestrator
   pip install -r requirements.txt
   python app/main.py

   # Terminal 2 - Career API  
   cd services/career-api
   pip install -r requirements.txt
   python app/main.py

   # Terminal 3 - Learning API
   cd services/learning-api
   pip install -r requirements.txt
   python app/main.py

   # Terminal 4 - Progress API
   cd services/progress-api
   pip install -r requirements.txt
   python app/main.py
   ```

4. **Start frontend applications**
   ```bash
   # Terminal 5 - Portal App
   cd apps/portal-app
   npm install
   npm run dev

   # Terminal 6 - Learner App  
   cd apps/learner-app
   npm install
   npm run dev
   ```

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🌐 Access Points

- **Portal App**: http://localhost:5173 (with onboarding form)
- **Learner App**: http://localhost:5174 (learning interface)
- **AI Orchestrator**: http://localhost:8000
- **Career API**: http://localhost:8001
- **Learning API**: http://localhost:8002  
- **Progress API**: http://localhost:8003

## 📁 Project Structure

```
dreamseed/
├── apps/
│   ├── portal-app/          # Main portal with onboarding
│   └── learner-app/         # Learning experience app
├── services/
│   ├── ai-orchestrator/     # LLM routing service
│   ├── career-api/          # Career guidance service
│   ├── learning-api/        # Learning content service
│   └── progress-api/        # Progress tracking service
├── packages/
│   ├── shared-types/        # TypeScript types & Zod schemas
│   └── shared-ui/           # Shared React components
├── .github/workflows/       # CI/CD pipelines
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Multi-stage container build
└── nginx.conf              # Frontend proxy configuration
```

## 🛠️ Development Commands

```bash
# Install all dependencies
npm install

# Build all packages and apps
npm run build

# Run linting across workspaces
npm run lint

# Type checking across workspaces  
npm run type-check

# Run development servers
npm run dev
```

## 🧪 API Endpoints

### AI Orchestrator (8000)
- `GET /` - Health check
- `GET /models` - Available AI models
- `POST /generate` - Generate AI responses
- `POST /batch-generate` - Batch AI requests

### Career API (8001)
- `GET /career-paths` - List career paths
- `GET /career-paths/{id}` - Get specific path
- `POST /career-paths/{id}/recommend` - Get recommendations

### Learning API (8002)
- `GET /modules` - List learning modules (with filters)
- `GET /modules/{id}` - Get specific module
- `POST /modules/{id}/start` - Start module for user
- `GET /modules/search` - Search modules

### Progress API (8003)
- `GET /progress/{user_id}` - User's progress
- `GET /progress/{user_id}/{module_id}` - Module progress
- `POST /progress/{user_id}/{module_id}` - Update progress
- `GET /analytics/{user_id}` - User analytics

## 🎯 Features

### Portal App
- **Onboarding Form**: Comprehensive user intake with validation
- **Zod Schema Validation**: Type-safe form handling
- **Responsive Design**: Mobile-first approach
- **Career Goal Management**: Dynamic goal addition/removal

### Learner App  
- **Module Browser**: Filter by difficulty, type, tags
- **Progress Tracking**: Visual progress indicators
- **Interactive Learning**: Simulated learning experience
- **Module Types**: Videos, articles, exercises, quizzes

### AI Orchestrator
- **LLM Routing**: Intelligent request routing to specialized models
- **Mock Responses**: Realistic AI response simulation
- **Batch Processing**: Handle multiple requests efficiently
- **Model Management**: Track available AI models

## 🔧 Configuration

### Environment Variables
```bash
# Backend services
ENV=development|production
DATABASE_URL=postgresql://...
OPENAI_API_KEY=your-api-key

# Frontend apps  
VITE_API_BASE_URL=http://localhost:8000
```

### Docker Configuration
- Multi-stage builds for optimization
- Service isolation with Docker Compose
- Nginx reverse proxy for frontend apps
- Health checks for all services

## 🚢 Deployment

### CI/CD Pipeline
- **Testing**: Automated tests for Node.js and Python
- **Building**: Multi-target Docker builds  
- **Security**: Trivy vulnerability scanning
- **Deployment**: Ready for production deployment

### Production Considerations
- Configure CORS origins properly
- Set up real database connections
- Implement proper authentication
- Configure environment-specific variables
- Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Future Enhancements

- [ ] Real AI/LLM integration
- [ ] User authentication & authorization
- [ ] Database persistence (PostgreSQL)
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile applications
- [ ] Integration testing suite
- [ ] Performance monitoring
