# Research: Frontend Components & Redis Scaling

**Feature**: 003-we-now-need
**Date**: 2025-09-23
**Status**: Complete

## Executive Summary

This research covers implementing React frontend components for the existing Contentizer API and adding Redis for task queue and session management. All technical decisions are based on existing codebase analysis and scalability requirements.

## Technology Decisions

### Frontend Component Library
**Decision**: React 18+ with TypeScript, using existing Vite setup
**Rationale**:
- Already configured in `/frontend/` with Vite build system
- TypeScript provides type safety for complex video workflow states
- React hooks ideal for managing WebSocket connections and async operations
- Existing API client in `frontend/src/services/api.ts` ready for integration

**Alternatives considered**:
- Vue.js: Would require new build setup, team learning curve
- Svelte: Better performance but smaller ecosystem for video/media components
- Plain JS: Insufficient for complex state management needs

### State Management
**Decision**: React Context + useReducer for complex workflow state, useState for component-local state
**Rationale**:
- Video creation workflow has complex multi-step state (trending → script → media → compose → upload)
- WebSocket progress updates need global state distribution
- Context avoids prop drilling through workflow components
- No external state library needed for current scope

**Alternatives considered**:
- Redux: Overkill for current scope, adds complexity
- Zustand: Lighter but adds dependency, Context sufficient for now
- React Query: Good for server state but we need WebSocket integration

### UI Component Framework
**Decision**: Tailwind CSS + Headless UI components
**Rationale**:
- Rapid development for workflow-focused UI
- Good TypeScript support
- Headless components provide accessibility out of box
- Easy to customize for content creator workflows

**Alternatives considered**:
- Material-UI: Heavy bundle, opinionated design
- Ant Design: Complex setup, unnecessary features
- Custom CSS: Too slow for development timeline

### Redis Integration Strategy
**Decision**: Redis with redis-py client, separate Redis services layer
**Rationale**:
- Task queue: Background video processing needs reliable job management
- Session storage: User preferences and workflow state across browser restarts
- Real-time updates: Pub/sub for WebSocket progress notifications
- Horizontal scaling: Multiple backend instances can share job queue

**Alternatives considered**:
- In-memory queues: Lost on server restart, no horizontal scaling
- Database-based queues: Poor performance for high-frequency updates
- RabbitMQ: More complex setup, Redis sufficient for current needs

### Task Queue Pattern
**Decision**: Celery with Redis broker for background tasks
**Rationale**:
- Video processing (FFmpeg) can take 5-10 minutes
- Need task progress tracking and failure recovery
- Celery integrates well with FastAPI async patterns
- Redis provides both broker and progress storage

**Alternatives considered**:
- FastAPI BackgroundTasks: No persistence, lost on restart
- Python Threading: Blocks server resources, no recovery
- Custom async queue: Reinventing wheel, error-prone

### Session Management
**Decision**: Redis-based sessions with JWT tokens for API access
**Rationale**:
- User preferences and API keys need persistence
- Workflow state survives browser refresh/close
- JWT provides secure API access
- Redis TTL handles session expiration automatically

**Alternatives considered**:
- Database sessions: Slower for frequent reads/writes
- Local storage only: Lost across devices, no server-side state
- Memory sessions: Lost on server restart

## Architecture Patterns

### Frontend Component Architecture
- **Container/Presentation Pattern**: Workflow containers manage state, UI components focus on display
- **Custom Hooks**: Reusable logic for API calls, WebSocket connections, form handling
- **Error Boundaries**: Graceful handling of video processing failures
- **Progressive Enhancement**: Core functionality works without WebSocket real-time updates

### Backend Integration Patterns
- **Service Layer**: Redis operations isolated in separate service classes
- **Dependency Injection**: Redis clients injected into FastAPI routes
- **Circuit Breaker**: Fallback to database if Redis unavailable
- **Event-Driven**: Task progress events trigger WebSocket notifications

### Data Flow Patterns
- **Command Query Separation**: Commands through API, queries through Redis cache
- **Event Sourcing**: Task progress events stored for recovery and monitoring
- **Optimistic Updates**: UI shows immediate feedback, syncs with backend asynchronously

## Risk Mitigation

### Performance Risks
- **Video Processing Memory**: Use streaming APIs, process in chunks
- **WebSocket Connections**: Implement connection pooling and reconnection logic
- **Redis Memory**: Set TTL on all keys, implement LRU eviction

### Reliability Risks
- **Task Failures**: Retry logic with exponential backoff
- **Redis Downtime**: Graceful degradation to database-only mode
- **Browser Refresh**: Persist workflow state to Redis, restore on reconnection

### Security Considerations
- **API Keys**: Encrypt in Redis, never expose in frontend state
- **Session Security**: HTTP-only cookies, CSRF protection
- **File Access**: Validate all media asset paths, sandbox file operations

## Implementation Dependencies

### New Dependencies Required
**Backend**:
- `redis>=4.5.0` - Redis client
- `celery>=5.3.0` - Task queue
- `python-jose>=3.3.0` - JWT token handling

**Frontend**:
- `@headlessui/react` - Accessible UI components
- `tailwindcss>=3.3.0` - Utility CSS framework
- `react-hook-form>=7.45.0` - Form handling

### Infrastructure Requirements
- Redis server (development: local, production: managed service)
- WebSocket support in deployment (nginx configuration)
- File storage accessible to both web server and Celery workers

### Integration Points
- Existing FastAPI routes need WebSocket endpoints added
- Current SQLAlchemy models need Redis caching layer
- Frontend API client needs WebSocket connection management
- Task progress needs standardized event format

## Next Phase Preparation

**Data Model Requirements**:
- Session entity for Redis storage schema
- Task entity for job queue management
- Progress event entity for real-time updates
- UI state entity for workflow persistence

**Contract Requirements**:
- WebSocket protocols for progress updates
- Extended API contracts for session management
- Task queue API for job submission and monitoring
- File upload/download with progress tracking

**Testing Strategy**:
- Component tests for React workflow UI
- Integration tests for Redis session persistence
- Contract tests for WebSocket protocols
- Load tests for concurrent video processing

All research items resolved. Ready for Phase 1 design and contracts.