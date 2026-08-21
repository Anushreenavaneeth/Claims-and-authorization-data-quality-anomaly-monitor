# System Architecture

HDOP uses a decoupled modular architecture:

```
┌────────────────────────────────────────────────────────┐
│                        Frontend                        │
│               React + Vite Dashboard UI                │
└───────────────────────────▲────────────────────────────┘
                            │ WebSockets / HTTP REST API
┌───────────────────────────▼────────────────────────────┐
│                        Backend                         │
│                    FastAPI Core                        │
│        (Routers, Services, Event Hub, Realtime)        │
└──────┬────────────┬─────────────┬──────────────┬───────┘
       │            │             │              │
┌──────▼──┐  ┌──────▼──┐   ┌──────▼──┐   ┌───────▼───────┐
│ Database│  │  Cache  │   │   ML    │   │  RAG Engine   │
│ Postgres│  │  Redis  │   │ Models  │   │ Vector Store  │
└─────────┘  └─────────┘   └─────────┘   └───────────────┘
```
