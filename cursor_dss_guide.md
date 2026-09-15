# Cursor IDE Master Guide: Enrollment Forecasting DSS Development

This comprehensive guide is tailored for developing the "Decision Support System for Enrollment Forecasting" using Cursor IDE. It aligns perfectly with your technical stack and the project requirements outlined in **DSS-FINAL-CH1-3AlferezEvangelioForcadillaPerihan-2.docx.pdf**.

## 1. Project Initialization & Workspace Setup

To manage the DSS efficiently, a monorepo structure is recommended, allowing Cursor's AI to understand the full context between your Electron frontend and FastAPI backend.

### Directory Structure
```text
enrollment-dss/
├── .cursorrules           # AI behavior rules for the project
├── docker-compose.yml     # Local backend deployment configuration
├── backend/               # FastAPI application
│   ├── main.py
│   ├── requirements.txt
│   └── models/
└── frontend/              # ElectronJS application
    ├── main.js            # Electron main process
    ├── preload.js         # IPC bridge
    ├── index.html         # Entry point
    └── src/               # Renderer components (Vue 3/UI files)

Configuring .cursorrules

Create a .cursorrules file in the root directory to guide Cursor's AI on your specific preferences.
Markdown

# .cursorrules
- Project: Decision Support System for Enrollment Forecasting.
- Frontend: ElectronJS (Desktop App), Vue 3 (Composition API), TypeScript, Tailwind CSS.
- Backend: Python, FastAPI, PostgreSQL.
- Deployment: Offline standalone desktop application. 
- Code Style: Prioritize modularity, isolate Electron main process logic from renderer UI components via secure IPC bridges.

2. Leveraging Cursor AI for DSS Features

Cursor's Composer (Cmd/Ctrl + I) and Chat (Cmd/Ctrl + L) are most powerful when given precise context. Here is how to prompt the AI for the specific modules required by the project.
A. Data Upload and Storage Module

The system requires users to upload and manage historical enrollment data efficiently.

Prompting Cursor (Backend):

    "Generate a FastAPI endpoint using UploadFile to process CSV uploads of historical enrollment records. The records include academic year, class level, and demographic information. Parse the data using pandas and bulk insert it into a PostgreSQL database using Prisma ORM. Include error handling for missing columns."

B. Enrollment Forecasting Engine

The core of the DSS is predicting future enrollment based on historical data. The system uses basic statistical or trend-based analysis.

Prompting Cursor (Backend):

    "Create a Python service class in FastAPI for enrollment forecasting. It should analyze historical enrollment data (academic year, class level) and apply a time series analysis model, such as a basic ARIMA implementation, to generate future enrollment predictions. Return the forecasted figures in a JSON format suitable for frontend charting."

C. Class Size & Section Computation

The system must compute class size and recommend the number of sections needed for preschool learners.

Prompting Cursor (Full Stack):

    "Write a utility function that takes the forecasted enrollment figures and a maximum class size parameter to compute the suggested number of sections needed per class level. Then, generate a Vue 3 component for the Electron renderer using Tailwind CSS to display these recommendations in a responsive data table."

D. Graphical Data Visualizations

The system needs to generate graphical and tabular visualizations such as charts and tables for enrollment trends.

Prompting Cursor (Frontend):

    "Create an Electron renderer view that fetches forecasting results from the FastAPI backend. Use a Vue-compatible charting library (like Chart.js or Recharts) to generate visual reports and charts for enrollment trends. Ensure the layout is clean and professional."

3. Recommended Workflow & Integrations
Database Management

Since this is an offline-based system not connected to external systems, local database management is crucial.

    Use Docker Compose to spin up a local PostgreSQL instance.

    Connect DBeaver CE to this local instance to inspect the enrollment records, demographic data, and forecasting output tables visually.

    When using Cursor Chat, you can paste table schemas directly into the chat so the AI writes perfectly typed Prisma queries.

Working with Context Files

To ensure Cursor understands the exact theoretical framework and requirements of your project:

    Open Cursor Chat.

    Type @ and attach DSS-FINAL-CH1-3AlferezEvangelioForcadillaPerihan-2.docx.pdf (or its text equivalent) directly into the context window.

    Ask the AI: "Review the attached document and outline the database schema needed to fulfill the scope of the project."

4. Offline Deployment Preparation

The project is explicitly required to be an offline application, making ElectronJS a perfect fit for local operations at Charismatic Tutorial Learning Center.

Use Cursor Composer to configure electron-builder or electron-forge to package the frontend into a standalone desktop executable. For the backend environment, use Docker Compose to containerize the FastAPI backend and PostgreSQL database. Alternatively, prompt the AI to bundle the Python backend via PyInstaller so it can be spawned directly by the Electron main process (main.js) as a child process, creating a completely self-contained offline application.