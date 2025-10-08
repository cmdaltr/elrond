# elrond Web Interface Design

**Feature**: Web-based interface for elrond digital forensics framework
**Target Version**: v2.1
**Status**: Design Phase

---

## Overview

Add a modern web interface to elrond that allows users to:
1. Select disk/memory images via path or upload
2. Choose analysis options via checkboxes
3. Monitor real-time progress for each tool
4. View and export results

## Architecture

### Technology Stack

**Backend**:
- **FastAPI** - Modern Python web framework with automatic OpenAPI docs
- **WebSockets** - Real-time progress updates
- **Celery** - Background task processing for long-running analyses
- **Redis** - Task queue and caching

**Frontend**:
- **React** - Component-based UI framework
- **Material-UI (MUI)** - Modern component library
- **WebSocket Client** - Real-time updates
- **Axios** - HTTP client for API calls

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           React Frontend (Port 3000)                   │ │
│  │  - Image Selection                                     │ │
│  │  - Analysis Options (Checkboxes)                       │ │
│  │  - Progress Bars (Real-time via WebSocket)            │ │
│  │  - Results Viewer                                      │ │
│  └─────────────┬──────────────────────┬───────────────────┘ │
└────────────────┼──────────────────────┼─────────────────────┘
                 │ HTTP/REST            │ WebSocket
                 │                      │
┌────────────────▼──────────────────────▼─────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ REST API Endpoints                                   │   │
│  │  - POST /api/images (add image)                      │   │
│  │  - GET /api/images (list images)                     │   │
│  │  - POST /api/analysis (start analysis)               │   │
│  │  - GET /api/analysis/{id} (get status)               │   │
│  │  - GET /api/results/{id} (get results)               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ WebSocket Manager                                    │   │
│  │  - /ws/{analysis_id} (progress updates)              │   │
│  │  - Broadcast tool progress                           │   │
│  │  - Send completion notifications                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Celery Task Manager                                  │   │
│  │  - run_analysis_task()                               │   │
│  │  - Progress callback → WebSocket                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis (Port 6379)                         │
│  - Celery task queue                                         │
│  - Session data                                              │
│  - Progress tracking                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  elrond Core Engine                          │
│  - ElrondEngine with progress callbacks                     │
│  - Platform adapters                                         │
│  - Tool execution                                            │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
elrond/
├── web/
│   ├── __init__.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── images.py        # Image management endpoints
│   │   │   ├── analysis.py      # Analysis endpoints
│   │   │   ├── results.py       # Results endpoints
│   │   │   └── websocket.py     # WebSocket handlers
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── image.py         # Image model
│   │   │   ├── analysis.py      # Analysis model
│   │   │   └── progress.py      # Progress model
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py      # Celery tasks
│   │   ├── config.py            # Backend configuration
│   │   └── dependencies.py      # FastAPI dependencies
│   └── frontend/
│       ├── package.json
│       ├── public/
│       │   └── index.html
│       └── src/
│           ├── App.jsx
│           ├── index.jsx
│           ├── components/
│           │   ├── ImageSelector.jsx
│           │   ├── AnalysisOptions.jsx
│           │   ├── ProgressMonitor.jsx
│           │   └── ResultsViewer.jsx
│           ├── services/
│           │   ├── api.js
│           │   └── websocket.js
│           └── styles/
│               └── main.css
├── pyproject.toml               # Add web dependencies
└── README_WEB.md                # Web interface documentation
```

## Features

### 1. Image Management

**UI Components**:
```jsx
<ImageSelector>
  - File browser button (local paths)
  - Drag & drop zone (future: upload large files)
  - Image list with details:
    - Path
    - Type (E01, VMDK, raw, DMG, etc.)
    - Size
    - Status (mounted/unmounted)
    - Remove button
</ImageSelector>
```

**Backend API**:
```python
POST /api/images
{
  "path": "/path/to/image.E01",
  "name": "evidence001"
}
→ Returns: {"image_id": "uuid", "type": "ewf", "size": 53687091200}

GET /api/images
→ Returns: [{"id": "uuid", "path": "...", "type": "...", ...}]

DELETE /api/images/{image_id}
→ Returns: {"success": true}
```

### 2. Analysis Options

**UI Components**:
```jsx
<AnalysisOptions>
  <CategoryGroup name="Memory Analysis">
    ☐ Volatility - Process List
    ☐ Volatility - Network Connections
    ☐ Volatility - DLL List
    ☐ Volatility - Command Line
  </CategoryGroup>

  <CategoryGroup name="Filesystem">
    ☐ Timeline Generation (Plaso)
    ☐ File Carving (Scalpel/Foremost)
    ☐ Deleted File Recovery
    ☐ Hash Analysis
  </CategoryGroup>

  <CategoryGroup name="Windows Artifacts">
    ☐ Registry Extraction (RegRipper)
    ☐ Event Logs
    ☐ Prefetch Files
    ☐ Browser History
  </CategoryGroup>

  <CategoryGroup name="macOS Artifacts">
    ☐ Keychain Export
    ☐ Unified Logs
    ☐ Plist Extraction
    ☐ Safari History
  </CategoryGroup>

  <CategoryGroup name="Security">
    ☐ Malware Scanning (ClamAV)
    ☐ YARA Rules
    ☐ Rootkit Detection
  </CategoryGroup>

  <OutputOptions>
    Output Directory: [/path/to/output]
    Case ID: [case-2025-001]
    ☑ Generate HTML Report
    ☑ Export to JSON
    ☐ Create Timeline
  </OutputOptions>

  <Button variant="primary">Start Analysis</Button>
</AnalysisOptions>
```

**Backend API**:
```python
POST /api/analysis
{
  "image_ids": ["uuid1", "uuid2"],
  "case_id": "case-2025-001",
  "output_directory": "/path/to/output",
  "options": {
    "memory_analysis": ["process_list", "network_connections"],
    "filesystem": ["timeline", "file_carving"],
    "windows_artifacts": ["registry"],
    "security": ["yara", "clamav"]
  }
}
→ Returns: {"analysis_id": "uuid", "status": "queued"}
```

### 3. Real-Time Progress Monitoring

**UI Components**:
```jsx
<ProgressMonitor analysisId="uuid">
  <OverallProgress>
    Overall Progress: [████████░░] 80% (8/10 tasks complete)
    Elapsed: 00:15:32 | Estimated: 00:19:20
  </OverallProgress>

  <TaskList>
    <Task name="Volatility - Process List" status="completed">
      [██████████] 100% - Completed in 2m 15s
      ✓ Found 156 processes
    </Task>

    <Task name="Volatility - Network Connections" status="running">
      [████████░░] 85% - Running (1m 45s elapsed)
      ⟳ Processing connection table...
    </Task>

    <Task name="Registry Extraction" status="pending">
      [░░░░░░░░░░] 0% - Waiting...
    </Task>

    <Task name="YARA Scanning" status="error">
      [████░░░░░░] 45% - Error occurred
      ✗ YARA rules file not found
    </Task>
  </TaskList>

  <LogViewer>
    [15:32:15] INFO: Starting analysis...
    [15:32:18] INFO: Mounted image at /tmp/elrond/mnt/uuid
    [15:32:20] INFO: Running Volatility process list...
    [15:34:35] INFO: Found 156 processes
    [15:34:35] INFO: Volatility process list completed
    [15:34:36] INFO: Running Volatility network connections...
  </LogViewer>
</ProgressMonitor>
```

**WebSocket Protocol**:
```javascript
// Client connects to WebSocket
ws = new WebSocket('ws://localhost:8000/ws/analysis_id')

// Server sends progress updates
{
  "type": "progress",
  "task_id": "volatility_process_list",
  "task_name": "Volatility - Process List",
  "progress": 85,
  "status": "running",
  "message": "Processing connection table...",
  "elapsed": 105,
  "estimated_total": 125
}

// Server sends completion
{
  "type": "complete",
  "task_id": "volatility_process_list",
  "status": "success",
  "result_summary": "Found 156 processes",
  "elapsed": 135
}

// Server sends error
{
  "type": "error",
  "task_id": "yara_scan",
  "error": "YARA rules file not found",
  "traceback": "..."
}

// Server sends overall status
{
  "type": "overall",
  "total_tasks": 10,
  "completed": 8,
  "running": 1,
  "pending": 1,
  "failed": 0,
  "overall_progress": 80
}
```

### 4. Results Viewer

**UI Components**:
```jsx
<ResultsViewer analysisId="uuid">
  <ResultsSummary>
    Analysis: case-2025-001
    Status: Completed
    Duration: 19m 20s
    Tasks: 10 completed, 0 failed
    Output: /path/to/output/case-2025-001
  </ResultsSummary>

  <ResultsTabs>
    <Tab name="Summary">
      <ArtifactCounts>
        - 156 Processes found
        - 42 Network connections
        - 892 Registry keys
        - 12 Suspicious files (YARA)
        - 0 Malware detected (ClamAV)
      </ArtifactCounts>
    </Tab>

    <Tab name="Processes">
      <DataTable
        columns={["PID", "Name", "PPID", "Threads", "Handles"]}
        data={processData}
        sortable
        filterable
      />
    </Tab>

    <Tab name="Registry">
      <TreeView data={registryData} />
    </Tab>

    <Tab name="Timeline">
      <TimelineViewer data={timelineData} />
    </Tab>

    <Tab name="Files">
      <FileExplorer data={filesData} />
    </Tab>

    <Tab name="Logs">
      <LogViewer data={logData} />
    </Tab>
  </ResultsTabs>

  <ExportButtons>
    <Button>Download HTML Report</Button>
    <Button>Export JSON</Button>
    <Button>Export CSV</Button>
    <Button>Download All Artifacts</Button>
  </ExportButtons>
</ResultsViewer>
```

**Backend API**:
```python
GET /api/analysis/{analysis_id}
→ Returns: {
  "id": "uuid",
  "status": "completed",
  "started_at": "2025-10-08T15:32:15",
  "completed_at": "2025-10-08T15:51:35",
  "duration": 1160,
  "tasks": [...],
  "output_directory": "/path/to/output"
}

GET /api/results/{analysis_id}
→ Returns: {
  "summary": {...},
  "processes": [...],
  "registry": {...},
  "timeline": [...],
  "files": [...]
}

GET /api/results/{analysis_id}/export/{format}
→ Returns: File download (HTML/JSON/CSV)
```

## Implementation Details

### Backend: Progress Tracking

**Modified ElrondEngine** to support progress callbacks:

```python
# elrond/core/engine.py

class ElrondEngine:
    def __init__(self, ..., progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback

    def run_tool(self, tool_name: str, **kwargs):
        if self.progress_callback:
            self.progress_callback({
                "task_id": tool_name,
                "status": "running",
                "progress": 0,
                "message": f"Starting {tool_name}..."
            })

        try:
            result = self._execute_tool(tool_name, **kwargs)

            if self.progress_callback:
                self.progress_callback({
                    "task_id": tool_name,
                    "status": "success",
                    "progress": 100,
                    "result_summary": result.summary
                })
        except Exception as e:
            if self.progress_callback:
                self.progress_callback({
                    "task_id": tool_name,
                    "status": "error",
                    "error": str(e)
                })
```

### Backend: WebSocket Manager

```python
# elrond/web/backend/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, analysis_id: str):
        await websocket.accept()
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = set()
        self.active_connections[analysis_id].add(websocket)

    def disconnect(self, websocket: WebSocket, analysis_id: str):
        self.active_connections[analysis_id].remove(websocket)

    async def broadcast(self, analysis_id: str, message: dict):
        if analysis_id in self.active_connections:
            for connection in self.active_connections[analysis_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await manager.connect(websocket, analysis_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, analysis_id)
```

### Backend: Celery Tasks

```python
# elrond/web/backend/tasks/analysis.py

from celery import Celery
from elrond.core.engine import ElrondEngine
from elrond.web.backend.api.websocket import manager

celery = Celery('elrond', broker='redis://localhost:6379/0')

@celery.task(bind=True)
def run_analysis_task(self, analysis_id: str, images: list, options: dict):
    async def progress_callback(update: dict):
        # Send progress update via WebSocket
        await manager.broadcast(analysis_id, {
            "type": "progress",
            **update
        })

    with ElrondEngine(
        case_id=options['case_id'],
        source_directory=images[0],
        output_directory=options['output_directory'],
        progress_callback=progress_callback
    ) as engine:
        # Run selected analyses
        for category, tools in options['options'].items():
            for tool in tools:
                engine.run_tool(tool)

        # Send completion
        await manager.broadcast(analysis_id, {
            "type": "complete",
            "analysis_id": analysis_id
        })
```

### Frontend: WebSocket Client

```javascript
// elrond/web/frontend/src/services/websocket.js

class WebSocketService {
  constructor() {
    this.ws = null;
    this.callbacks = {};
  }

  connect(analysisId, onProgress) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${analysisId}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'progress':
          onProgress(data);
          break;
        case 'complete':
          this.onComplete(data);
          break;
        case 'error':
          this.onError(data);
          break;
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default new WebSocketService();
```

## Dependencies

### Backend (pyproject.toml)

```toml
[project.optional-dependencies]
web = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "websockets>=12.0",
    "celery>=5.3.0",
    "redis>=5.0.0",
    "python-multipart>=0.0.6",  # File uploads
    "aiofiles>=23.2.0",          # Async file operations
]
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.5.0",
    "recharts": "^2.8.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0"
  }
}
```

## Running the Web Interface

### Development Mode

**Terminal 1 - Start Redis**:
```bash
redis-server
```

**Terminal 2 - Start Celery Worker**:
```bash
cd elrond
celery -A web.backend.tasks.analysis worker --loglevel=info
```

**Terminal 3 - Start Backend**:
```bash
cd elrond
uvicorn web.backend.main:app --reload --port 8000
```

**Terminal 4 - Start Frontend**:
```bash
cd elrond/web/frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### Production Mode

```bash
# Build frontend
cd elrond/web/frontend
npm run build

# Start backend (serves static frontend)
cd ../..
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000
```

## Security Considerations

1. **Authentication**: Add JWT-based authentication
2. **File Access**: Restrict file browser to specific directories
3. **Input Validation**: Validate all paths and options
4. **Rate Limiting**: Prevent abuse of analysis endpoints
5. **HTTPS**: Use SSL certificates in production
6. **CORS**: Configure appropriate CORS policies

## Testing

### Backend Tests
```python
# tests/web/test_api.py
def test_create_image(client):
    response = client.post("/api/images", json={
        "path": "/path/to/test.E01",
        "name": "test_image"
    })
    assert response.status_code == 200

def test_start_analysis(client):
    response = client.post("/api/analysis", json={
        "image_ids": ["uuid"],
        "case_id": "test-001",
        "options": {...}
    })
    assert response.status_code == 200
```

### Frontend Tests
```javascript
// frontend/src/components/__tests__/ImageSelector.test.jsx
test('renders image selector', () => {
  render(<ImageSelector />);
  expect(screen.getByText('Add Image')).toBeInTheDocument();
});
```

## Roadmap

### Phase 7.1: Core Web Interface (Week 1-2)
- ✅ Architecture design (this document)
- ⏳ Backend API implementation
- ⏳ WebSocket support
- ⏳ Basic frontend structure

### Phase 7.2: Image Management (Week 2)
- ⏳ Image selector component
- ⏳ Image list display
- ⏳ Path validation

### Phase 7.3: Analysis Options (Week 3)
- ⏳ Checkbox interface for tools
- ⏳ Option categories
- ⏳ Configuration validation

### Phase 7.4: Progress Monitoring (Week 3-4)
- ⏳ Real-time progress bars
- ⏳ Task status display
- ⏳ Log viewer

### Phase 7.5: Results Viewer (Week 4-5)
- ⏳ Results display components
- ⏳ Export functionality
- ⏳ Data visualization

### Phase 7.6: Polish & Testing (Week 5)
- ⏳ UI/UX refinements
- ⏳ Integration testing
- ⏳ Performance optimization
- ⏳ Documentation

---

*Document created: October 2025*
*elrond v2.1 - Web Interface Design*
