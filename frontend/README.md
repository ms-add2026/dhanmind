# DhanMind Frontend

React + TypeScript chat UI for the local-first DhanMind financial copilot.

## Run Locally

```bash
npm install
npm run dev
```

The app expects the FastAPI backend at `http://localhost:8000`.

## Quality Checks

```bash
npm run lint
npm run build
```

## Project Notes

- `src/App.tsx` contains the single-screen chat experience.
- `src/index.css` imports Tailwind CSS v4.
- `vite.config.ts` wires the React and Tailwind plugins.
