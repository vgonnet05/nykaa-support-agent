# nykaa-support-agent
A hands-on learning project to understand and build an Agentic AI support agent using RAG, CrewAI, AutoGen, memory, guardrails, and FastAPI through step-by-step implementation.


## Task 4: Grounded Answer Generation

The system retrieves the top three policy chunks and returns their
content as the answer under MOCK_LLM. It does not call an external
language model.

The similarity threshold is set to 0.20 based on measured retrieval
results. If the top result falls below this threshold, the system
returns: "I don't know based on the available policy information."

Testing covered five in-scope queries and one out-of-scope query.
All five in-scope queries returned policy context, and the France
question triggered the fallback.

The threshold is provisional because it was calibrated using a small
sample. The delivery query also retrieved a partially unrelated
sentence, demonstrating that similarity alone does not guarantee
relevance.