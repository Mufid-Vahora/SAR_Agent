```mermaid
graph TD
    subgraph "User & Presentation Layer"
        A[👨‍💼 Compliance Officer] --> B{Frontend UI<br>(React/HTML/JS)}
    end

    subgraph "Application & Core Services Layer"
        B -- 1. Upload Case Files --> C[API Gateway]
        C --> D[<b>Case-Management-Service</b><br>(FastAPI)]
        D -- 2. Create Case --> E[(PostgreSQL<br>Case Data)]
        D -- 3. Trigger Ingestion --> F[<b>Data-Ingestion-Service</b><br>(FastAPI)]
        F -- "Uses pandas, pdfplumber, LlamaParse" --> G[Message Queue<br>(Apache Kafka / RabbitMQ)]
        G -- 4. Enqueue Standardized Data (JSON) --> H[<b>AI-Core-Service</b><br>(FastAPI)]

        subgraph "🧠 AI Core (RAG Pipeline)"
            H --> H1[Chunking]
            H1 --> H2[Embedding<br>(Sentence Transformers)]
            H2 --> H3[(Vector Database<br>FAISS / ChromaDB)]
            H3 --> H4[Retrieval]
            H4 -- Retrieved Context --> H5{LLM<br>(Llama 3.1 / MPT-7B)}
            H -- Structured Data --> H5
            H5 -- "Orchestrated by LangChain/Haystack" --> H6[5. Generate Narrative Draft]
        end

        H6 --> D
        D -- 6. Store Narrative --> E
        D -- 7. Provide Data for Review --> B
        B -- 8. Officer Reviews, Edits & Approves --> D
        D -- 9. Trigger Formatting --> I[<b>Jurisdiction-Formatter-Service</b><br>(FastAPI)]
        I -- "FinCEN Module (lxml, xmlschema)" --> J((FinCEN SAR<br>XML File))
        I -- "FIU-IND Module" --> K((FIU-IND STR<br>XML File))
        I -- 10. Send Formatted File --> L[<b>Secure-Submission-Service</b><br>(FastAPI)]
        L -- "FinCEN Module (Paramiko)" --> M{FinCEN BSA E-Filing<br>(SFTP)}
        L -- "FIU-IND Module (Requests)" --> N{FIU-IND FINGate 2.0<br>(REST API)}
        M -- 11. Acknowledgment --> L
        N -- 11. Acknowledgment --> L
        L -- 12. Update Status --> D
        D -- Final Status Update --> B
    end

    subgraph "🛡️ Cross-Cutting Enterprise Systems"
        O[<b>Audit-Logging-Service</b>] --> P[(Immutable Log Store<br>PostgreSQL / Elasticsearch)]
        D -- Log Actions --> O
        F -- Log Actions --> O
        H -- Log Actions --> O
        L -- Log Actions --> O
        B -- Log User Actions --> O

        Q[<b>Monitoring & Alerting</b><br>(Prometheus & Grafana)]
        Q -- Scrape Metrics --> D
        Q -- Scrape Metrics --> F
        Q -- Scrape Metrics --> H
        Q -- Scrape Metrics --> I
        Q -- Scrape Metrics --> L
    end

    style B fill:#e6f3ff,stroke:#0055cc
    style E fill:#fff2cc,stroke:#d6b656
    style G fill:#d5e8d4,stroke:#82b366
    style H fill:#f8cecc,stroke:#b85450
    style P fill:#e1d5e7,stroke:#9673a6
    style Q fill:#dae8fc,stroke:#6c8ebf