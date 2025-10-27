# Contributing to DCMaidBot

Thank you for your interest in contributing to DCMaidBot! 💕

## Getting Started

1. Read [AGENTS.md](AGENTS.md) for complete development workflow
2. Review [PRPs/](PRPs/) directory for active tasks
3. Check existing issues and PRs

## Development Workflow

### Step 1: Setup Development Environment

```bash
git clone https://github.com/dcversus/dcmaidbot.git
cd dcmaidbot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install pre-commit hooks (IMPORTANT!)
pre-commit install
```

### Step 2: Create .env File

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Step 3: Pick a PRP

Review [PRPs/](PRPs/) directory and pick an available PRP to work on.

## Making Changes

### Branch Naming

```
prp-<number>-<brief-description>
```

Examples:
- `prp-003-postgresql-database`
- `prp-006-joking-system`

### Commit Messages

Follow conventional commits:

```
<type>: <description>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat: implement memory matching engine

- Add regex matching for memory expressions
- Support complex patterns like "send message if..."
- Integrate with message handler

Implements: PRP-004
```

### Code Quality

**Pre-commit hooks will automatically run before each commit!**

The following checks run automatically via pre-commit:
- ✅ Ruff linting (with auto-fix)
- ✅ Ruff formatting
- ✅ Type checking with mypy
- ✅ Trailing whitespace removal
- ✅ End-of-file fixing
- ✅ YAML validation
- ✅ Large file detection
- ✅ Merge conflict detection
- ✅ Private key detection
- ✅ All tests (unit + e2e)

**Manual run (optional):**

```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Or run individual checks:
ruff check .          # Lint
ruff format .         # Format
pytest tests/ -v      # Tests
mypy bot.py           # Type check
```

**If pre-commit fails:**
- Fix the issues shown in the output
- Stage your changes: `git add .`
- Commit again: `git commit -m "..."`
- Pre-commit will run again automatically

**To skip pre-commit (NOT RECOMMENDED):**
```bash
git commit --no-verify -m "..."
```

All checks must pass before PR approval!

## Pull Request Process

### 1. Before Creating PR

**CRITICAL CHECKLIST:**
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Linting clean (`ruff check .`)
- [ ] Formatting applied (`ruff format .`)
- [ ] **CHANGELOG.md updated in [Unreleased] section** ⚠️
- [ ] PRP progress updated with checkboxes
- [ ] Definition of Done (DOD) criteria met

### 2. PR Description Template

Use [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md):

**Must include:**
- PRP Number
- Summary
- Changes Made (Added/Changed/Removed/Fixed)
- Definition of Done checklist
- **CHANGELOG.md update confirmation**
- Testing summary
- Related PRs (if any)
- Next steps

### 3. Infrastructure Changes

If your PR requires infrastructure updates (Kubernetes, GitOps):

1. Create changes in main repo (dcmaidbot)
2. Create separate PR to [uz0/core-charts](https://github.com/uz0/core-charts)
3. **Comment on main PR with link to infrastructure PR**
4. Both PRs reviewed together
5. Merge both when approved

**Example:**
- PR #3 (dcmaidbot): Infrastructure cleanup
- PR #15 (core-charts): Add dcmaidbot Helm charts
- Comment: "Related infrastructure: uz0/core-charts#15"

### 4. Code Review

Reviewers check:
- [ ] CHANGELOG.md updated
- [ ] All DOD criteria met
- [ ] Tests passing (CI green)
- [ ] Code follows architecture patterns
- [ ] No linter/type errors
- [ ] PRP progress updated
- [ ] Documentation clear
- [ ] Related PRs linked (if applicable)

## CHANGELOG Requirements

**MANDATORY**: Every PR must update CHANGELOG.md

Format:
```markdown
## [Unreleased]

### Added
- New feature X
- New service Y

### Changed
- Modified behavior Z

### Removed
- Deprecated feature A

### Fixed
- Bug fix B
```

See [AGENTS.md](AGENTS.md#changelog-requirements-critical) for details.

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### E2E Tests

```bash
pytest tests/e2e/ -v
```

### Test Coverage

Aim for >80% coverage:

```bash
pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
dcmaidbot/
├── bot.py                 # Main entry point
├── handlers/              # Message/command handlers
├── middlewares/           # Middleware
├── models/                # Database models
├── services/              # Business logic
├── tests/                 # Tests
├── PRPs/                  # Product Requirements Processes
├── AGENTS.md              # Development guide
└── CONTRIBUTING.md        # This file
```

## PRP Workflow

1. Read AGENTS.md Core Goal
2. Pick a PRP from PRPs/*.md
3. Implement according to DOR/DOD
4. Write unit tests
5. Write one e2e test
6. Update PRP progress with comments
7. Run lint/typecheck/tests
8. Mark PRP as complete
9. **If PR creates related PRs: Comment with links**
10. Move to next PRP

## Documentation

### Code Comments

Only add comments when:
- User explicitly requests
- Code is complex and requires context

### Inline Documentation

Update relevant docs:
- README.md for user-facing changes
- AGENTS.md for workflow changes
- PRPs/*.md for progress updates

## Questions?

- Check [AGENTS.md](AGENTS.md) first
- Review existing PRs and issues
- Ask in PR comments

## Code of Conduct

- Be respectful and constructive
- Follow the waifu bot personality in contributions
- Love for the mysterious creators is mandatory! Nya~ 🎀
- Protect the admins, help their friends
- Make jokes, learn from reactions

Thank you for contributing to DCMaidBot! 💕
