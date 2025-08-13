# ADR 0001: Initial Architecture Decision

## Context

The BlackboxProgramming project needed to settle on a technology stack for its initial implementation. The options considered included building the backend with FastAPI versus another Python framework and using React for the frontend. We also evaluated whether to begin with a monolithic repository or split services.

## Decision

We decided to implement the backend using FastAPI and the frontend using React. FastAPI provides modern async capabilities, automatic documentation generation, and strong typing via Pydantic, which will help us build a high‑performance API quickly. React offers a component‑based architecture with a large ecosystem, making it suitable for our collaborative code editor interface. We will keep all components (backend, frontend, agents) in a single repository for ease of development at this stage.

## Status

Accepted

## Consequences

Choosing FastAPI and React provides a robust foundation but means we need to maintain both Python and Node toolchains. The monorepo simplifies cross‑component changes but could become unwieldy as the project grows; we may revisit this choice later. With the architecture established, we can focus on implementing features and gradually introducing more services as needed.
