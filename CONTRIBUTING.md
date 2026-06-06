# Contributing to FinAdmin360

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/finadmin360.git
cd finadmin360
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
pre-commit install
cp .env.example .env  # Fill in your Azure values
```

## Branching

- `main` — production only, protected
- `develop` — integration branch, all features merge here
- `feature/your-description` — one branch per feature

```bash
git checkout develop && git pull origin develop
git checkout -b feature/your-feature-name
```

## Before opening a PR

```bash
black src/ dags/ tests/
ruff check src/ dags/ tests/ --fix
pytest tests/unit/ -v
cd dbt && dbt test
```

## Commit message format

`type: short description in lowercase`

Types: `feat` `chore` `docs` `test` `fix` `refactor`
