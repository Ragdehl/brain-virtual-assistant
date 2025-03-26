# Linting & Formatting

This document outlines the code quality standards, linting rules, and formatting guidelines for the Obsidian AI Assistant project.

## Code Quality Standards

### Python Standards
- PEP 8 compliance
- Type hints
- Docstrings
- Error handling
- Logging

### JavaScript Standards
- ESLint rules
- Prettier formatting
- TypeScript types
- Error handling
- Logging

## Linting Configuration

### Python Linting
```ini
# setup.cfg
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
ignore = E203, W503
per-file-ignores =
    __init__.py: F401

[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### JavaScript Linting
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

## Formatting Rules

### Python Formatting
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
line_length = 100
```

### JavaScript Formatting
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

## Code Style Examples

### Python
```python
from typing import Dict, List, Optional
from datetime import datetime

def create_task(
    title: str,
    description: str,
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> Dict[str, any]:
    """
    Create a new task with the given parameters.

    Args:
        title: The title of the task
        description: The description of the task
        priority: The priority level (low, medium, high)
        due_date: Optional due date for the task

    Returns:
        Dict containing the created task data

    Raises:
        ValueError: If priority is invalid or title is empty
    """
    if not title:
        raise ValueError("Title cannot be empty")
    
    if priority not in ["low", "medium", "high"]:
        raise ValueError("Invalid priority level")

    return {
        "task_id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": "todo"
    }
```

### JavaScript
```typescript
interface Task {
  taskId: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  dueDate?: Date;
  createdAt: Date;
  updatedAt: Date;
  status: 'todo' | 'in_progress' | 'done';
}

function createTask(
  title: string,
  description: string,
  priority: Task['priority'] = 'medium',
  dueDate?: Date
): Task {
  if (!title) {
    throw new Error('Title cannot be empty');
  }

  if (!['low', 'medium', 'high'].includes(priority)) {
    throw new Error('Invalid priority level');
  }

  return {
    taskId: uuidv4(),
    title,
    description,
    priority,
    dueDate,
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'todo'
  };
}
```

## Pre-commit Hooks

### Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## IDE Configuration

### VS Code Settings
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Continuous Integration

### GitHub Actions
```yaml
name: Lint and Format

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run linters
        run: |
          flake8
          mypy .
          black --check .
          isort --check-only .
```

## Best Practices

### Code Organization
- Clear module structure
- Logical file naming
- Consistent imports
- Proper documentation

### Code Quality
- Type safety
- Error handling
- Logging
- Testing

### Documentation
- Clear docstrings
- Type hints
- Comments
- README updates

### Version Control
- Clear commit messages
- Feature branches
- Pull requests
- Code review 