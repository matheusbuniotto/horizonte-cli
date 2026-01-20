# Goals CLI

A powerful, AI-enhanced Command Line Interface to track your life goals, vision, and progress.

## Features

- **Goal Management**: Create, track, and manage goals across different categories (Financial, Life, Health, Professional).
- **Smart Horizons**: Track Short Term vs Long Term vision.
- **AI Integration**:
    - **Smart Criteria**: AI suggests Specific, Measurable, Achievable, Relevant, and Time-bound criteria for your goals.
    - **Intelligent Check-ins**: Natural language updates ("I have 150k now") are automatically parsed and applied to relevant goals.
    - **Progress Analysis**: Get motivational feedback and analytical summaries of your progress.
- **Privacy First**: All data is stored locally.

## Installation

```bash
uv sync
```

## Usage

Run the CLI using `uv run`:

```bash
uv run goals [COMMAND]
```

### Common Commands

- `uv run goals init`: Initialize the database.
- `uv run goals add`: Add a new goal (interactive).
- `uv run goals list`: List all active goals.
- `uv run goals checkin`: Start an interactive check-in session.
- `uv run goals progress`: Visualize your overall progress.
