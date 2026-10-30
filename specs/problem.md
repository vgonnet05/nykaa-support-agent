# Problem Statement: Nykaa Domain Support Agent

## Objective
Build an AI-powered customer support agent for Nykaa's e-commerce domain using Retrieval-Augmented Generation (RAG), CrewAI, AutoGen, memory, guardrails, and FastAPI.

## Core Requirements
- Create a synthetic order dataset with at least 40 records.
- Build a knowledge base containing 12 policy documents.
- Implement two chunking strategies and compare retrieval precision and recall.
- Generate grounded responses and reject unsupported questions.
- Implement order lookup and an escalation score.
- Build a three-agent CrewAI workflow.
- Add conversational memory and structured output validation.
- Implement input and output guardrails.
- Expose HTTP and WebSocket interfaces through FastAPI.
- Add structured logging, evaluation, and response caching.
- Demonstrate a two-agent AutoGen workflow.
- Apply least-privilege tool access, risk classification, and runtime budget limits.

## Implementation Principles
- Use deterministic `MOCK_LLM` mode for acceptance tests.
- Do not require external API keys or network access for acceptance tests.
- Keep customer PII masked in logs.
- Validate outputs and ground policy answers in retrieved knowledge.
- Document implementation decisions, test results, and evaluation metrics in the README.