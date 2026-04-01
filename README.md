# 🧠 MindTrack: Smart Mood & Mental Health Journal

> **Your companion for personal well-being, powered by Artificial Intelligence.**

MindTrack is a modern, full-stack application designed to help individuals track their mood, stress levels, and sleep patterns. By combining traditional journaling with state-of-the-art AI analysis, MindTrack provides deep insights into your mental health trends and emotional state.

---

## ✨ Key Features

- 📓 **Smart Journaling**: Record daily entries with mood scores (1-10), stress levels, and sleep duration.
- 🤖 **AI-Powered Insights**: Get sentiment analysis, extracted themes (tags), and empathetic feedback on every entry using OpenAI/OpenRouter.
- 📊 **Dynamic Analytics**: Visualize mood correlations and stress patterns through interactive, beautiful charts.
- 🔐 **Secure Authentication**: Built-in user registration and JWT-based secure login.
- ⚡ **Next-Gen UX**: A blazing-fast, responsive interface built with Next.js 15 and Tailwind CSS v4.

---

## 🛠 Tech Stack

### Frontend
- **Framework**: [Next.js 15+](https://nextjs.org/) (App Router)
- **Library**: [React 19](https://react.dev/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Charts**: [Recharts](https://recharts.org/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State Management**: [Zustand](https://github.com/pmndrs/zustand)

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database**: [PostgreSQL](https://www.postgresql.org/) (via SQLAlchemy & AsyncPG)
- **AI Integration**: OpenAI SDK / OpenRouter API
- **Authentication**: JWT (JSON Web Tokens) with Pydantic 2 validation

---

## 🚀 Quick Start (One-Command Launch)

We provide a specialized script that sets up the database, installs all dependencies, and launches both servers concurrently without heavy Docker builds.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/mindtrack-app.git
cd mindtrack-app

# 2. Add your AI API key to backend/.env
# (See 'Environment Variables' section below)

# 3. Launch everything
./start.local.sh
```

- 🟢 **Frontend**: [http://localhost:3000](http://localhost:3000)
- 🟢 **Backend API**: [http://localhost:8000](http://localhost:8000)
- 🟢 **Database**: `localhost:5432` (PostgreSQL)

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
Create a `.env` file in the `backend/` directory with the following values:

```env
DATABASE_URL=postgresql+asyncpg://mindtrack:mindtrack_secret@localhost:5432/mindtrack
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI Configuration
AI_API_KEY=sk-your-openai-or-openrouter-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (`frontend/.env.local`)
Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🏗 Architecture

```mermaid
graph TD
    User((User)) <--> NextJS[Next.js Frontend]
    NextJS <--> FastAPI[FastAPI Backend]
    FastAPI <--> Postgres[(PostgreSQL DB)]
    FastAPI <--> AI[OpenAI / OpenRouter API]
```

## 🛠 Manual Setup (Optional)

If you prefer to run components separately:

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

---

**Developed with ❤️ by Samsa016**
