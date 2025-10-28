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

## Complete PRP Workflow

### Overview

Each PRP (Product Requirements Process) follows a structured workflow from branch creation to post-release QC sign-off.

### Phase 1: Branch & Implementation

1. **Create unique branch from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b prp-016-multi-room-house
   ```

2. **Read PRP requirements**:
   - Review Definition of Ready (DOR)
   - Understand Definition of Done (DOD)
   - Note any dependencies

3. **Implement incrementally**:
   - Break work into small chunks (1-2 hours each)
   - Commit frequently with clear messages
   - Update PRP progress after each chunk
   - Leave emotional comments in PRP (see AGENTS.md)

4. **Write tests**:
   - Add unit tests for new features
   - Add at least one E2E test
   - Aim for >80% coverage

5. **Run quality checks**:
   ```bash
   ruff check . && ruff format .
   pytest tests/ -v
   mypy bot.py
   ```

### Phase 2: PR Creation & Review

1. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - PRP-016: Multi-room house exploration feature
   ```

2. **Create PR**:
   ```bash
   git push -u origin prp-016-multi-room-house
   gh pr create --title "PRP-016: Multi-Room Interactive House" --body "..."
   ```

3. **Wait for CI checks** (do NOT proceed until green ✅)

4. **Address review comments**:
   - Fix all issues (don't paper over them)
   - Address every nitpick professionally
   - Commit each fix separately
   - Respond to each comment

5. **Get approval** and merge:
   ```bash
   gh pr merge --squash
   ```

6. **Leave signal in PRP**:
   ```markdown
   ✅ PR merged: https://github.com/dcversus/dcmaidbot/pull/42
   ```

### Phase 3: Post-Release Workflow

**MANDATORY: Complete ALL steps after merge**

#### Step 1: Monitor Deployment

1. Watch GitHub Actions:
   ```bash
   gh run watch
   ```

2. Monitor pod rollout:
   ```bash
   kubectl get pods -n prod-core -l app=dcmaidbot -w
   ```

3. Update PRP with deployment status:
   ```markdown
   ### 🚀 Deployment Status - Oct 28, 2025

   - ✅ GitHub Actions: Build succeeded
   - ✅ Docker image pushed
   - ✅ Pods running: 2/2
   - ✅ Health checks passing
   ```

#### Step 2: Execute Production E2E Tests

1. Run E2E tests:
   ```bash
   pytest tests/e2e/production/ -v --production
   ```

2. Manual health check:
   ```bash
   curl https://dcmaidbot.theedgestory.org/health
   ```

3. Document results in PRP

#### Step 3: Verify Version & Commit

1. Visit https://dcmaidbot.theedgestory.org/

2. Verify:
   - Commit hash matches merge commit
   - Version matches `version.txt`

3. Document in PRP:
   ```markdown
   ### ✅ Version Verification

   - Commit: `abc1234` ✅
   - Version: `0.3.0` ✅
   ```

#### Step 4: Complete Post-Release Checklist

Execute ALL items in PRP's Post-Release Checklist section.

#### Step 5: Verify DOR/DOD/Tests Alignment

1. Review all PRP sections
2. Cross-check alignment
3. Document any gaps found

#### Step 6: QC Engineer Sign-Off

**Role: Quality Control Engineer**

Leave final sign-off in PRP:

```markdown
### ✅ QC Engineer Sign-Off - Oct 28, 2025

**Quality Acceptance Criteria Review:**

- ✅ All DOR items met
- ✅ All DOD items completed
- ✅ All tests passing
- ✅ Post-release checklist complete
- ✅ Deployment verified
- ✅ No regressions detected

**User Story Acceptance**: ✅ APPROVED

**QC Engineer**: Agent (automated role)
**Date**: October 28, 2025
**PRP**: PRP-016
```

### Phase 4: Incident Management (if needed)

**If incident detected during deployment:**

#### SRE Role Activates

1. **Leave ATTENTION signal**:
   ```markdown
   ### 🚨 ATTENTION: INCIDENT DETECTED - Oct 28, 2025 14:32 UTC

   **Incident Type**: Deployment Failure
   **Severity**: 🔴 CRITICAL
   **Status**: 🔥 ACTIVE
   ```

2. **Create Postmortem Section** in PRP with timeline table

3. **Investigate and document**:
   - Current status
   - Actions taken
   - Next steps

4. **Update with progress** until resolved

5. **Write complete postmortem** after resolution

6. **Create action item PRPs** to prevent recurrence

7. **Leave final SRE comment** marking incident resolved

See [AGENTS.md](AGENTS.md#incident-management--sre-workflow) for complete incident workflow.

### Phase 5: Next PRP

1. Mark current PRP as complete
2. Celebrate! 🎉
3. IMMEDIATELY start next highest priority PRP
4. Repeat from Phase 1

**NEVER stop working until ALL PRPs are complete!**

### Workflow Summary

```
┌─────────────────────────────────────────────┐
│ Phase 1: Branch & Implementation            │
├─────────────────────────────────────────────┤
│ ✅ Create branch from main                  │
│ ✅ Read PRP requirements                    │
│ ✅ Implement incrementally                  │
│ ✅ Write tests                              │
│ ✅ Run quality checks                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 2: PR Creation & Review               │
├─────────────────────────────────────────────┤
│ ✅ Update CHANGELOG                         │
│ ✅ Create PR                                │
│ ✅ Wait for CI (green)                      │
│ ✅ Address review comments                  │
│ ✅ Merge PR                                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 3: Post-Release Workflow              │
├─────────────────────────────────────────────┤
│ ✅ Monitor deployment                       │
│ ✅ Run production E2E tests                 │
│ ✅ Verify version/commit                    │
│ ✅ Complete post-release checklist          │
│ ✅ Verify DOR/DOD/Tests alignment           │
│ ✅ QC Engineer sign-off                     │
└─────────────────────────────────────────────┘
                    ↓
            ┌───────────────┐
            │ Incident?     │
            └───────┬───────┘
               No   │   Yes
                    │     └──> SRE Workflow
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 5: Next PRP                           │
├─────────────────────────────────────────────┤
│ ✅ Mark complete                            │
│ ✅ Celebrate                                │
│ ✅ Start next PRP immediately               │
└─────────────────────────────────────────────┘
```

### Role-Based Responsibilities

**Developer**:
- Phase 1 & 2 (implementation, PR)

**SRE (Site Reliability Engineer)**:
- Phase 3 Step 1 (deployment monitoring)
- Phase 4 (incident management if needed)

**QC Engineer (Quality Control)**:
- Phase 3 Steps 2-6 (testing, verification, sign-off)

See [AGENTS.md](AGENTS.md#role-based-workflow--sub-agent-skills) for complete role descriptions.

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
