                 Docker Compose
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    Frontend        Backend         PostgreSQL
                        │
                     Redis
                        │
                Chaos Injector
                        │
                 Alert Generated
                        │
                 LangGraph Agent
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Diagnose         Planner        Risk Classifier
                        │
                Safe? /      \ High Risk
                     │          │
                     ▼          ▼
              Docker MCP    Slack MCP
                     │          │
                     └────┬─────┘
                          ▼
                    Verify Recovery
                          │
                          ▼
                   Dashboard & Logs
                          │
                          ▼
                     Evaluation