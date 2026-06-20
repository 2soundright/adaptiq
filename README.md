# AdaptIQ

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=flat&logo=groq&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-874FFF?style=flat&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)
![Deploy](https://img.shields.io/badge/deployed-live-brightgreen?style=flat)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat)

**AdaptIQ** is a smart assistant that knows everything your company knows. Upload your documents, point it at your website, and from that moment on anyone on your team can ask questions in natural language and get real answers — explained in plain language, with references to exactly where the information came from.

Screens every query for safety. Respects who can see what. Gets smarter the more it's used.

---

## Try it Live

**[adaptiq-2soundright.streamlit.app](https://adaptiq-2soundright.streamlit.app)**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin | admin |
| User | user | user |

**As a User**, ask questions in the chat and get AI-generated answers with source citations.

**As an Admin**, everything above, plus upload documents, run the web scraper, view analytics, and review audit logs.

---

## Documentation

| Section | Description |
|---------|-------------|
| [Personas](novus-memory/personas/personas.md) | The three user roles, Admin, Worker, and User, and what each can do |
| [Product Areas](novus-memory/product_areas/product_areas.md) | The six functional areas of AdaptIQ: Auth, Chat, Documents, Analytics, Audit Logs, Web Scraper |
| [Key Flows](novus-memory/key_flows/key_flows.md) | Step-by-step walkthroughs of every major user flow |
| [Integrations](novus-memory/integrations/integrations.md) | External services connected to AdaptIQ: Groq, HuggingFace, ChromaDB |
| [Technical Docs](novus-memory/documentation/documentation.md) | RAG pipeline, continual learning, multilingual support, security, access control, data model |
| [Site Map](novus-memory/site_map.md) | Visual diagram of the full application structure |

---

## Built With

| Tool | What it does |
|------|-------------|
| Streamlit | Interface, clean, fast, works on any device |
| Groq | Powers AI responses and safety filtering |
| HuggingFace | Embeddings (BAAI/bge-m3) and reranking (BAAI/bge-reranker-large) |
| ChromaDB | Vector database for semantic document search |
| SQLite | Users, documents, conversations, feedback |

```mermaid
flowchart TD
    User([User]) -->|question| ST[Streamlit UI]
    ST --> Safety[Safety Filter\nGroq]
    Safety --> Lang[Language Detection]
    Lang --> QT[Query Transform\nGroq]
    QT --> Embed[Embeddings\nHuggingFace bge-m3]
    Embed --> Retrieve[Vector Search\nChromaDB]
    Retrieve --> Rerank[Reranking\nHuggingFace bge-reranker]
    Rerank --> Generate[Response Generation\nGroq]
    Generate -->|streaming answer + sources| ST
    ST -->|rating| CL[Continual Learning\nEWC + Drift Detection]
    CL -->|relevance update| Retrieve

    Admin([Admin]) -->|upload docs| Ingest[Document Ingestion]
    Admin -->|trigger| Scraper[Web Scraper]
    Ingest --> Embed
    Scraper --> Embed

    Generate --- SQLite[(SQLite\nusers · conversations · feedback)]
```
