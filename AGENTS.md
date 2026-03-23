# Agent Instructions for Proyecto-Integracion

This file contains strict guidelines, commands, and conventions for AI agents operating within this repository. Please read carefully before implementing changes.

## Project Structure Overview

The repository consists of three main components:
1. `backend/`: A Python FastAPI application using asynchronous SQLAlchemy (`asyncmy`) and Pydantic.
2. `frontend/nuxt/`: A Vue 3 / Nuxt 3 frontend application using Tailwind CSS.
3. `print-client/` (Root): A Node.js print service meant to be compiled into a `.exe` using `pkg` to run on Windows machines.

---

## 1. Build, Lint, and Test Commands

### Backend (FastAPI - Python)
- **Install dependencies:** `pip install -r backend/requirements.txt`
- **Run Development Server:** `cd backend && python run.py` (which runs `uvicorn app.main:app --reload`)
- **Linting & Formatting (Recommended):**
  - Agents should prefer using `ruff` (if available) to maintain code quality:
    - Lint: `ruff check backend/`
    - Format: `ruff format backend/`
- **Testing:** The project uses `pytest` and `pytest-asyncio` for asynchronous tests.
  - Run all tests: `cd backend && pytest`
  - Run a specific test directory: `cd backend && pytest tests/routers`
  - Run a specific test file: `cd backend && pytest path/to/test_file.py`
  - Run a single test: `cd backend && pytest path/to/test_file.py::test_function_name`
  - *Note:* Always ensure database connections in tests are mocked or use a dedicated test database to avoid side-effects.

### Frontend (Vue 3 / Nuxt 3 - TypeScript)
- **Install dependencies:** `cd frontend/nuxt && npm install`
- **Run Development Server:** `cd frontend/nuxt && npm run dev`
- **Build for Production:** `cd frontend/nuxt && npm run build`
- **Generate Static Site:** `cd frontend/nuxt && npm run generate`
- **Linting & Formatting:** Use standard Vue conventions. If ESLint is configured:
  - Lint: `cd frontend/nuxt && npm run lint`
- **Testing:** Nuxt 3 officially recommends `vitest` for unit testing.
  - Run all tests: `cd frontend/nuxt && npx vitest run`
  - Run tests in watch mode: `cd frontend/nuxt && npx vitest`
  - Run a specific test file: `cd frontend/nuxt && npx vitest run path/to/test.ts`
  - Run a single test by name: `cd frontend/nuxt && npx vitest run path/to/test.ts -t "test_name"`

### Print Service (Node.js)
- **Install dependencies:** `npm install` (in the root directory)
- **Run Script manually:** `node print-service.js`
- **Build Windows Executable:** `npm run build:exe` (Uses `pkg` to compile `print-service.js` and dependencies into `dist/print-service.exe`)

---

## 2. Code Style Guidelines & Security Mandates

### Backend (Python/FastAPI)
- **Architecture & Modularity:**
  - Follow the existing structure inside `backend/app/`:
    - `models/`: SQLAlchemy ORM definitions. **Must be perfectly synchronized with `mariadb/init.sql`.**
    - `schemas/`: Pydantic models for request validation and response serialization.
    - `routers/`: FastAPI endpoint definitions.
    - `utils/`: Shared helper functions and business logic.
    - `websocket/`: Socket.IO or FastAPI WebSockets handling.
- **Strict Input Validation (Pydantic):**
  - **Never use raw `dict` for inputs.** Always use defined Pydantic schemas.
  - Apply `model_config = ConfigDict(str_strip_whitespace=True)` to all schemas to auto-strip whitespace.
  - Use `Field(..., max_length=X, pattern=r"^[...]+$")` to enforce strict length limits and regex constraints (especially for fields like Usernames, Folios) to prevent Stored XSS and limit payload size.
- **Database & Queries (SQLAlchemy):**
  - **Avoid raw SQL (`text()`).** Always use SQLAlchemy 2.0 ORM constructs (`select`, `insert`, `update`, `delete`, `and_`, `or_`).
  - This prevents SQL Injection and enforces type safety.
  - Use `async def` and `AsyncSession` for all database operations.
- **Security Specifics:**
  - **Path Traversal Prevention:** When dealing with file inputs from users (e.g., audio files, downloads), always sanitize the filename using `os.path.basename(filename)`.
- **Typing:** Type hints are **strictly mandatory**.
  - All FastAPI endpoints must specify `response_model` using Pydantic schemas.
  - Use Python 3.10+ typing syntax (e.g., `list[str]` instead of `typing.List[str]`, `str | None` instead of `typing.Optional[str]`).
- **Naming Conventions:**
  - Variables, functions, and modules/files: `snake_case` (e.g., `get_user_by_id`, `user_schema.py`).
  - Classes and Pydantic models: `PascalCase` (e.g., `UserResponse`, `DatabaseModel`).
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`).
- **Error Handling:**
  - Use FastAPI's `HTTPException` for expected HTTP client errors (400, 401, 403, 404).
  - Do not leak raw database exceptions (like `IntegrityError`) to the client. Catch them and return a sanitized 400 or 500 status.

### Frontend (Vue 3 / Nuxt 3)
- **Composition API:** Exclusively use the Vue 3 Composition API with `<script setup lang="ts">`. Avoid Options API.
- **Reactivity & State:**
  - Use `ref()` for primitive values and arrays, `reactive()` for objects.
  - Use `computed()` for derived state. Avoid complex logic directly in templates.
- **Validation & Sanitization:**
  - The project avoids heavy 3rd-party validation libraries. Use HTML5 native validation (`required`, `type`, `maxlength`, `min`, `max`) and custom JS checks in the `<script setup>` before calling the backend.
  - **Safe Rendering:** Rely on Vue's standard interpolation `{{ }}` to prevent XSS. Avoid `v-html` unless absolutely necessary with strictly hardcoded, trusted content (like SVG icons).
- **Typing:** TypeScript is required (`lang="ts"`). Define strict `interface` or `type` definitions for API payloads, component props, and emits.
- **Styling:** Use Tailwind CSS utility classes directly in the template. Avoid custom CSS unless using `<style scoped>`.
- **Naming Conventions:**
  - Components: `PascalCase.vue` (e.g., `UserProfile.vue`).
  - Composables: `camelCase` starting with `use` (e.g., `useAuth.ts`).
  - Variables and functions: `camelCase`.
- **Auto-Imports:** Nuxt 3 auto-imports components, composables, and Vue APIs. Do not add explicit imports for these.
- **Routing:** Nuxt uses file-based routing. Pages go in `frontend/nuxt/pages/`.
- **Error Handling & Notifications:**
  - Wrap `await` API calls in `try/catch` blocks.
  - Use `toastify-js` to display toast notifications for success and error states.

### Print Service (Node.js Client)
- **Purpose:** Connects via sockets to print documents received from the backend locally on the client's machine.
- **Style:** Standard Node.js conventions. Ensure compatibility with the `pkg` bundler.
- **Error Handling:** Handle socket disconnections gracefully with reconnection logic. File system errors should log locally and not crash the main process.

---

## 3. General Agent Directives
- **Verify Context Before Editing:** Always use `read` or `glob` to verify the state and structure of the code before attempting to modify files. Do not hallucinate file contents.
- **Absolute Paths:** Always use absolute file paths in your tools. Ensure paths are constructed correctly using the workspace root.
- **Test-Driven Corrections:** When implementing bug fixes, write a failing test first if the test framework is available. Once the fix is applied, run the test to verify.
- **Focused Changes:** Keep changes minimal and isolated. Use the `edit` tool with exact `oldString` and `newString` matches to modify specific blocks rather than completely rewriting large files.
- **ORM Synchronization:** Whenever modifying database tables in `init.sql`, ensure that `backend/app/models/models.py` is immediately updated to exactly reflect the schema (tables, constraints, primary/foreign keys).
- **No Unsolicited Refactoring:** Only refactor code if explicitly requested by the user. Follow existing patterns to maintain consistency unless instructed otherwise.
