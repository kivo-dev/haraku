"""HARAKO AI tourism assistant (modular monolith: lives inside the existing FastAPI app).

Layers (each depends only on the ones above it):
  types / errors / validation / language   plain Python, no third-party imports
  llm/        provider adapters (Anthropic, OpenAI-compatible) behind one small interface
  data.py     `TourismData` protocol + the adapter that reuses HARAKO's existing routers and Neshan service
  tools.py    the only things the model may call (validated, time-limited, logged)
  itinerary.py, memory.py, prompts.py, orchestrator.py
  router.py   the HTTP layer (FastAPI) -- POST /v1/assistant/chat
"""
