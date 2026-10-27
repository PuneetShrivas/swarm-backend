# Swarm Project Base

A full-stack project base featuring a FastAPI backend and a Next.js (App Router) frontend, designed to manage and interact with a swarm of specialized agents. This project is tailored for easy deployment on Vercel.

## Structure

The project is structured as a monorepo with two main directories:

- `/backend`: The FastAPI application serving as the backend.
- `/frontend`: The Next.js application providing the user interface.

## Getting Started Locally

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Frontend (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The UI will be available at `http://localhost:3000`.

## Deployment to Vercel

This project is configured for deployment on Vercel.

1. Install the Vercel CLI if you haven't already:
   ```bash
   npm install -g vercel
   ```

2. From the root of the project, you can deploy the frontend or backend separately, or configure a single Vercel project with custom routing depending on your preference.

### Deploying the Backend
Navigate to the `backend/` folder and run `vercel`. The included `vercel.json` file configures the `@vercel/python` builder to deploy the FastAPI app as serverless functions.

### Deploying the Frontend
Navigate to the `frontend/` folder and run `vercel`. Vercel automatically detects Next.js projects and configures them accordingly.

## Extending the Swarm
- **Backend:** Add new endpoints in `backend/app/main.py` (or create separate router files) to handle complex agent logic, external API calls, or database interactions.
- **Frontend:** The `/chat` route demonstrates a basic interaction pattern. Expand this by integrating Vercel AI SDK or state management libraries as your swarm logic grows.