## Project Status

This project is currently in **Level 1: Foundation Setup**

### Completed:
- Database schema analysis
- Asset assignment system initialized
- Project structure created

### Current Focus:
- Setting up backend foundation (FastAPI + DB connection)
- Preparing environment configuration
- Building core infrastructure for Agentic System

### Next Steps:
- Database connection layer
- ORM models setup
- First data query test


## Phase 1: Asset Monitoring Pipeline

- Built SQLAlchemy-based data layer
- Implemented asset maintenance tracking
- Created due assets detection logic
- Developed Service → Tool → Agent pipeline (v1)


## Phase 2: Assignment Layer

- Implemented Assignment Service to map assets to responsible staff
- Added AssetAssignment relationship model
- Built Assignment Agent to enrich maintenance tasks with ownership data
- Introduced structured output using Pydantic (AssignmentResult)
- Fixed schema inconsistency in asset assignment table


## Phase 3: Email Generation Layer

- Implemented Email Agent to convert maintenance tasks into email messages
- Generated structured email format (to, subject, body)
- Integrated with Assignment Agent output (AssignmentResult schema)
- Built foundation for future SMTP/Gmail integration


## Phase 4: Email Notification

- Implemented Email Agent for reminder generation.
- Added Gmail SMTP integration.
- Built Email Sender Tool.
- Successfully delivered real maintenance reminder emails.
- Prepared the pipeline for notification logging and LLM-powered email generation.


## Current Progress

- Asset & Maintenance Services implemented
- Assignment system implemented
- Email sender integrated with SMTP
- Notification logging stored in PostgreSQL
- EmailSender refactored to structured result object


## Current Workflow

The current maintenance notification workflow:

```bash
Device Agent
|
v
Assignment Agent
|
v
Email Agent
|
v
Email Sender
|
v
Logger Agent
|
v
Notification Log Database
```




## Implemented Components

### Agents

- DeviceAgent
  - Retrieves maintenance due assets.

- AssignmentAgent
  - Finds responsible staff for each asset.

- EmailAgent
  - Generates maintenance reminder emails.

- LoggerAgent
  - Records notification results.

### Services

- AssetService
- AssignmentService
- NotificationLogService

### Tools

- Assignment Tool
- Email Sender
- Notification Logging Tool

## Database

The module uses PostgreSQL with SQLAlchemy ORM.

Implemented tables:

- asset
- staff
- asset_assignment
- asset_maintenance
- notification_log


# Current Workflow

## Architecture Overview

The system follows an Agentic Workflow architecture where each agent has a specific responsibility.

```text
                 Coordinator Agent
                        |
        --------------------------------
        |              |              |
        v              v              v
   Device Agent   Assignment Agent  Email Agent
        |              |              |
        v              v              v
  Asset Service  Assignment Service  Email Task
                                      |
                                      v
                              Email Sender Tool
                                      |
                                      v
                                 Logger Agent
                                      |
                                      v
                             Notification Log DB
```

The Coordinator Agent is responsible for orchestrating the workflow between different agents while keeping each component independent.

## Implemented Components

### Coordinator Agent

Implemented the workflow orchestration layer.

**Responsibilities:**

- Initialize required agents and tools.
- Execute the maintenance notification workflow.
- Pass structured outputs between agents.
- Collect execution results.

**Current execution flow:**

```text
Device Tasks
     |
     v
Assigned Maintenance Tasks
     |
     v
Generated Email Tasks
     |
     v
Email Sending Results
     |
     v
Notification Logs
```

## Database Section

### Project Structure

```text
agentic_module/
│
├── agents/
│   ├── __init__.py
│   ├── coordinator_agent.py
│   ├── device_agent.py
│   ├── assignment_agent.py
│   ├── email_agent.py
│   └── logger_agent.py
│
├── services/
│   ├── asset_service.py
│   ├── assignment_service.py
│   └── notification_log_service.py
│
├── tools/
│   ├── email_sender.py
│   ├── assignment_tool.py
│   └── notification_tool.py
│
├── models/
├── schemas/
├── main.py
└── db.py
```

## Current Progress

### Completed

- **Asset maintenance monitoring pipeline:** Fully functional.
- **Assignment workflow:** Automatically pairs tasks with staff.
- **Email generation and delivery:** Single-connection SMTP broadcast.
- **Notification logging:** Full auditing for success/failure states.
- **Coordinator Agent orchestration:** Smooth data flow between all layers.

> The first end-to-end maintenance notification workflow is now fully functional.

### Next Steps

- Refactor main execution layer.
- Expose workflow through FastAPI endpoints.
- Add API layer for triggering maintenance workflows.
- Introduce LangGraph for advanced agent orchestration.
- Integrate LLM capabilities for intelligent decision making.