# OpsIntel AI

**An Exasol-powered AI assistant for data operations, incident investigation, and data reliability.**

OpsIntel AI aims to help data and engineering teams detect pipeline failures, investigate likely root causes, assess data quality, recommend safe recovery steps, and verify whether an incident has been resolved.

> **Project status:** Early development — Day 1 repository setup and project foundation. Features listed as planned are not claimed to be implemented until supported by working code and tests.

## The Problem

Data and engineering teams often discover pipeline failures, stale dashboards, and data-quality issues only after they affect downstream analytics.

Investigating these incidents can require manually examining pipeline histories, logs, timestamps, upstream dependencies, and data-quality checks. This increases investigation time and makes it difficult to determine whether business data is trustworthy.

## Our Solution

OpsIntel AI is being developed as an evidence-driven data operations platform using Exasol Personal as its analytical data platform.

The intended workflow is:

1. **Detect:** Identify failed or delayed pipelines and potential data-quality problems.
2. **Investigate:** Collect relevant operational evidence.
3. **Explain:** Identify plausible root causes and distinguish evidence from assumptions.
4. **Recommend:** Suggest safe, actionable recovery steps.
5. **Verify:** Check whether the pipeline recovered and the resulting data meets the required conditions.

## Planned Modules

| Module | Responsibility |
|---|---|
| Pipeline Guardian | Detect pipeline failures, delays, and operational anomalies. |
| Root Cause AI | Explain likely causes using supporting evidence. |
| DataTrust | Evaluate freshness, completeness, consistency, and other data-quality signals. |
| Data Copilot | Answer operational questions using validated, read-only SQL. |
| Recovery and Verification | Recommend controlled recovery and verify outcomes. |

These modules represent the target design. Their implementation status will be updated as the project develops.

## Architecture

The intended high-level architecture is:

    Operational Data
          |
          v
    Exasol Personal
          |
          v
    Python Application / API
          |
          v
    Incident Detection
          |
          v
    Evidence Collection and Root-Cause Analysis
          |
          v
    Data Quality and Operational Insights
          |
          v
    Safe Recommendations
          |
          v
    Recovery Verification
          |
          v
    Results and Evidence for the User

The final architecture may evolve as the implementation and testing progress.

## Technology

- **Programming language:** Python
- **Analytical database:** Exasol Personal
- **Query language:** SQL
- **API layer:** To be finalized during implementation
- **AI integration:** To be selected and documented during implementation
- **Testing:** Automated tests and reproducible evaluation cases

Only technologies actually integrated into the final working version will be represented as completed dependencies.

## Repository Structure

The repository currently includes the following top-level development areas:

    opsintel-ai/
    ├── app/          # Application code
    ├── sql/          # SQL scripts and database-related work
    ├── .gitignore    # Files and directories excluded from Git
    └── README.md     # Project documentation

The structure will be expanded as additional modules, configuration, tests, and documentation are implemented.

## Getting Started

### Prerequisites

- Python installed on your system
- Git
- Exasol Personal configured for local or otherwise accessible use, when database integration is added

### Clone the repository

    git clone https://github.com/Anafa-thabassum/opsintel-ai.git
    cd opsintel-ai

### Set up a virtual environment

On macOS or Linux:

    python3 -m venv .venv
    source .venv/bin/activate

On Windows:

    python -m venv .venv
    .venv\Scripts\activate

### Install dependencies

Once the project's dependency file is available:

    pip install -r requirements.txt

### Configure the application

Database connection settings, required environment variables, and other configuration instructions will be documented when the relevant implementation is added.

Never commit database passwords, API keys, or other secrets.

### Run the application

The exact startup command will be added after the application entry point and run configuration are finalized. The repository's setup instructions will be kept synchronized with the working implementation.

## Data and Safety

- Use public or synthetic data only.
- Document the source and licence of every external dataset.
- Validate SQL before execution.
- Begin with read-only database access for AI-generated queries.
- Require appropriate safeguards and approval for recovery actions.
- Preserve evidence and test whether recovery actually succeeded.
- Never expose secrets in source code or logs.

## Evaluation Plan

The project will be evaluated using reproducible incident scenarios covering:

- Pipeline failure and delay detection
- Root-cause accuracy and evidence quality
- Data-quality assessment
- SQL safety and query correctness
- Recovery verification
- End-to-end latency and failure handling

Evaluation results will be published only after the corresponding tests have been run.

## Development Roadmap

The development plan progresses from repository and database foundations to incident detection, investigation, data-quality analysis, safe recovery, testing, and demonstration.

See the project plan and progress updates for the current implementation status.

## Hackathon

Built for **ExaThon India 2026**, using Exasol Personal as the required analytical data platform.

Official challenge information: https://www.exasol.com/events/exathon-india-2026/

## Licence

The project will be released under an OSI-approved open-source licence, such as MIT or Apache-2.0, before submission. The corresponding `LICENSE` file must be added to the repository.

## Project Status

This is an actively developed hackathon project. The README will be updated as features become operational, tests produce measurable results, and the setup process becomes reproducible.
