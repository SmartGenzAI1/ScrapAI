# Contributing to ScrapAI

Thank you for your interest in contributing to **ScrapAI**! We welcome contributions from developers, researchers, and open-source enthusiasts.

---

## 🛠️ Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/SmartGenzAI1/ScrapAI.git
cd ScrapAI
```

### 2. Python Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run the Local Server
```bash
python backend/main.py
```
Open `http://localhost:8000` in your browser.

---

## 🧪 Running Tests

Before submitting a PR, make sure all automated tests pass:

```bash
pytest tests/ -v
```

---

## 📐 Coding Guidelines

- **Zero External API Dependency Guarantee**: Core vectorization, search, chunking, and extractive QA features must work 100% locally without requiring external cloud AI or API keys.
- **Type Hints & Docstrings**: Use Python type hints (`typing.List`, `typing.Dict`, `typing.Optional`) and descriptive docstrings.
- **Clean Architecture**: Follow the separation of concerns:
  - `backend/search/` for vectorization, BM25, and hybrid ranking algorithms.
  - `backend/scraper/` for crawler logic, robots.txt, and HTML extraction.
  - `backend/database/` for SQLAlchemy models and SQL queries.
  - `workers/` for background queue consumers and pipeline supervisors.
  - `frontend/` for the React SPA.

---

## 🤝 Submitting a Pull Request

1. Create a descriptive feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with a clear, human-readable commit message:
   ```bash
   git commit -m "feat(crawler): add configurable rate limiting per IP"
   ```
3. Push to your branch and open a Pull Request against `main`.
