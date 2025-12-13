# Repository Conventions for Traceability

**Repository:** milosriki/geminivideo  
**Created:** 2025-12-07  
**Purpose:** Maintain consistent traceability between ideas, code, and documentation going forward  

---

## Overview

This document establishes conventions and best practices for maintaining traceability in the geminivideo repository. Following these conventions ensures that ideas can be tracked from conception through implementation and maintenance.

---

## Idea Identification System

### Idea ID Format

All ideas should be identified using the following format:

```
IDEA-XXX: Brief Description
```

**Examples:**
- `IDEA-001: AI Video Analysis Engine`
- `IDEA-053: Advanced Thumbnail Generation`
- `IDEA-100: Multi-Region Deployment`

**Rules:**
- IDs are sequential three-digit numbers (001, 002, etc.)
- IDs are assigned when an idea is first documented
- IDs are never reused, even if an idea is abandoned
- Brief description should be under 50 characters

### Idea Tags

Each idea should be tagged with one or more category tags:

**Primary Categories:**
- `core-feature` - Essential platform functionality
- `feature` - Additional feature
- `enhancement` - Improvement to existing feature
- `integration` - External system integration
- `infrastructure` - Platform infrastructure
- `frontend` - UI/UX feature
- `backend` - Backend service feature
- `ml` - Machine learning related
- `ai` - AI/LLM related
- `devops` - Deployment and operations
- `documentation` - Documentation work

**Secondary Tags:**
- `security` - Security related
- `performance` - Performance optimization
- `cost-optimization` - Cost reduction
- `analytics` - Analytics and reporting
- `testing` - Testing infrastructure
- `monitoring` - Monitoring and observability

**Status Tags:**
- `implemented` - Feature complete
- `in-progress` - Actively being developed
- `planned` - Planned for future
- `at-risk` - No activity in >= 90 days
- `abandoned` - Explicitly abandoned

---

## Commit Message Convention

### Format

```
[IDEA-XXX] Brief description of change

Detailed explanation of what was changed and why.

Related: IDEA-YYY (if applicable)
Implements: IDEA-XXX
Fixes: #issue-number (if applicable)
```

### Examples

**New Feature:**
```
[IDEA-034] Add AI video generation using Gemini 2.0

Implements text-to-video generation with Gemini 2.0 API.
Includes scene composition and style transfer capabilities.

Implements: IDEA-034
Related: IDEA-006 (Titan Core integration)
```

**Enhancement:**
```
[IDEA-013] Improve Thompson Sampling with ignorance zone

Adds ignorance zone logic for service businesses to avoid
premature ad killing during awareness phase.

Implements: IDEA-013 (enhancement)
Related: IDEA-029
```

**Bug Fix:**
```
[IDEA-003] Fix FFmpeg pipeline memory leak

Fixes memory leak in video rendering by properly closing
FFmpeg processes.

Implements: IDEA-003 (bug fix)
Fixes: #45
```

**Documentation:**
```
[DOCS] Update IDEA-025 deployment documentation

Updates Cloud Run deployment guide with new environment
variables and health check configuration.

Related: IDEA-025
```

---

## Pull Request Convention

### Title Format

```
[IDEA-XXX] Brief description
```

### PR Description Template

```markdown
## Idea Reference
IDEA-XXX: [Brief Description]

## Description
[Detailed description of what this PR implements]

## Implementation Details
- [Detail 1]
- [Detail 2]
- [Detail 3]

## Code Changes
### New Files
- `path/to/new/file.ts` - Description
- `path/to/another/file.py` - Description

### Modified Files
- `path/to/modified/file.ts` - What changed
- `path/to/another/modified.py` - What changed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] Documentation updated

## Related Issues
- Implements: IDEA-XXX
- Related: IDEA-YYY
- Closes: #issue-number

## Documentation Updates
- [ ] Code comments added
- [ ] API documentation updated
- [ ] User guide updated
- [ ] README updated
- [ ] Traceability map updated

## Checklist
- [ ] Code follows repository style guidelines
- [ ] All tests passing
- [ ] No linter warnings
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Breaking changes documented

## Screenshots/Demo
[If applicable, add screenshots or demo links]
```

### PR Labels

Apply appropriate labels to PRs:

**Type Labels:**
- `feature` - New feature
- `enhancement` - Enhancement to existing feature
- `bugfix` - Bug fix
- `documentation` - Documentation changes
- `infrastructure` - Infrastructure changes
- `refactor` - Code refactoring

**Priority Labels:**
- `priority:critical` - Critical issue
- `priority:high` - High priority
- `priority:medium` - Medium priority
- `priority:low` - Low priority

**Status Labels:**
- `work-in-progress` - Still being developed
- `ready-for-review` - Ready for code review
- `needs-testing` - Needs testing before merge
- `blocked` - Blocked by other work

---

## Issue Convention

### Issue Title Format

**Feature Request:**
```
[IDEA] Brief description of feature
```

**Bug Report:**
```
[BUG] Brief description of bug
```

**Enhancement:**
```
[ENHANCEMENT] Brief description of enhancement
```

### Issue Labels

**Required Labels:**
- Category label (feature, bug, enhancement, etc.)
- Priority label
- Component label (frontend, backend, ml-service, etc.)

**Optional Labels:**
- `good-first-issue` - Good for new contributors
- `help-wanted` - Help wanted from community
- `breaking-change` - Introduces breaking changes
- `needs-discussion` - Needs team discussion

---

## Branch Naming Convention

### Format

```
<type>/<idea-id>-<brief-description>
```

### Types

- `feature/` - New feature
- `enhancement/` - Enhancement to existing feature
- `bugfix/` - Bug fix
- `hotfix/` - Critical production fix
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### Examples

```
feature/IDEA-053-thumbnail-generation
enhancement/IDEA-013-thompson-sampling-improvements
bugfix/IDEA-003-ffmpeg-memory-leak
docs/IDEA-025-deployment-guide-update
```

---

## Code Comment Convention

### File Headers

**TypeScript/JavaScript:**
```typescript
/**
 * IDEA-XXX: Brief Description
 * 
 * Detailed description of what this file implements.
 * 
 * @module ModuleName
 * @see {@link ../docs/IDEAS_CATALOG.md#idea-xxx}
 */
```

**Python:**
```python
"""
IDEA-XXX: Brief Description

Detailed description of what this module implements.

Related:
    - IDEA-YYY: Related idea
    
See Also:
    - docs/IDEAS_CATALOG.md#idea-xxx
"""
```

### Function/Method Comments

Include IDEA reference for functions implementing specific features:

```typescript
/**
 * Generates creative variations using DCO engine.
 * 
 * Implements IDEA-014: Dynamic Creative Optimization
 * 
 * @param creative - Base creative to vary
 * @param options - Variation options
 * @returns Array of creative variations
 */
function generateVariations(creative: Creative, options: VariationOptions): Creative[] {
  // Implementation
}
```

---

## Documentation Convention

### Documentation Structure

All feature documentation should follow this structure:

```markdown
# IDEA-XXX: Feature Name

**Status:** [Implemented/In Progress/Planned]
**Last Updated:** YYYY-MM-DD
**Owner:** [Team/Person]

## Overview
[Brief overview of the feature]

## Motivation
[Why this feature is needed]

## Implementation
[How it's implemented]

### Code Paths
- `/path/to/main/file` - Main implementation
- `/path/to/related/file` - Related functionality

### API Endpoints
- `POST /api/endpoint` - Description
- `GET /api/endpoint/{id}` - Description

### Configuration
- `config_key` - Description

## Usage Examples
[Examples of how to use the feature]

## Testing
[How to test this feature]

## Related Ideas
- IDEA-YYY: Related feature
- IDEA-ZZZ: Dependent feature

## References
- [Documentation](link)
- [PR](link)
- [Issue](link)
```

---

## File Organization

### New Features

When adding a new feature, create documentation in the appropriate location:

**Feature Documentation:**
```
/docs/features/IDEA-XXX-feature-name.md
```

**Implementation Notes:**
```
/docs/implementation/IDEA-XXX-implementation.md
```

**API Documentation:**
```
/docs/api/IDEA-XXX-api.md
```

### Code Organization

Organize code by feature/idea when possible:

```
/services/service-name/
  ├── features/
  │   ├── idea-xxx/
  │   │   ├── index.ts
  │   │   ├── implementation.ts
  │   │   └── tests.ts
  │   └── idea-yyy/
  │       └── ...
  └── ...
```

---

## Traceability Maintenance

### Regular Reviews

Conduct traceability reviews:

**Bi-Weekly:**
- Review new ideas and assign IDs
- Update IDEAS_CATALOG.md with new entries
- Review in-progress ideas for activity
- Update status of completed work

**Monthly:**
- Comprehensive review of all ideas
- Identify ideas at risk (>= 90 days no activity)
- Update TRACEABILITY_MAP.md with new implementations
- Generate status reports

**Quarterly:**
- Review and prune abandoned ideas
- Archive old documentation
- Update conventions as needed

### Update Process

When updating traceability documents:

1. **IDEAS_CATALOG.md:**
   - Add new ideas with full details
   - Update status of existing ideas
   - Update last activity dates
   - Add new PRs/issues/commits

2. **TRACEABILITY_MAP.md:**
   - Add new code paths for implemented ideas
   - Update related PRs and commits
   - Add new documentation references
   - Update implementation status

3. **WHERE_ARE_WE_NOW.md:**
   - Update current status section
   - Add new features to major ideas
   - Update recent activity highlights
   - Refresh risks and gaps

---

## Automation

### Automated Checks

Set up automated checks for traceability:

**Pre-commit Hooks:**
```bash
# Check for IDEA reference in commit message
if ! grep -qE '^\[IDEA-[0-9]{3}\]' commit_msg; then
  echo "Error: Commit message must start with [IDEA-XXX]"
  exit 1
fi
```

**PR Validation:**
```yaml
# .github/workflows/pr-validation.yml
- name: Validate PR Title
  run: |
    if [[ ! "${{ github.event.pull_request.title }}" =~ ^\[IDEA-[0-9]{3}\] ]]; then
      echo "PR title must start with [IDEA-XXX]"
      exit 1
    fi
```

### Automated Reporting

Create scripts for automated reporting:

**Activity Report:**
```bash
# scripts/generate-activity-report.sh
# Generates report of idea activity in last 30 days
```

**Traceability Check:**
```bash
# scripts/check-traceability.sh
# Validates all ideas have corresponding implementations
```

---

## Best Practices

### Do's

✅ **Always reference ideas in commits and PRs**
✅ **Keep IDEAS_CATALOG.md up to date**
✅ **Document code with idea references**
✅ **Update traceability documents regularly**
✅ **Use consistent formatting**
✅ **Link related ideas**
✅ **Mark ideas with status tags**

### Don'ts

❌ **Don't skip idea references in commits**
❌ **Don't reuse idea IDs**
❌ **Don't leave ideas undocumented**
❌ **Don't forget to update last activity dates**
❌ **Don't create duplicate ideas**
❌ **Don't leave stale documentation**

---

## Tool Recommendations

### Recommended Tools

**For Idea Tracking:**
- GitHub Projects - Project board visualization
- GitHub Issues - Idea discussion and tracking
- GitHub Milestones - Group related ideas

**For Code Traceability:**
- GitHub CodeQL - Code scanning and analysis
- SonarQube - Code quality and traceability
- Conventional Commits - Commit message validation

**For Documentation:**
- Markdown linters - Consistent documentation
- Link checkers - Validate documentation links
- Auto-generation tools - Keep docs in sync

---

## Examples

### Complete Feature Implementation Example

**1. Create Issue:**
```
Title: [IDEA] Add real-time budget optimization
Labels: feature, ml, enhancement, priority:high
```

**2. Create Branch:**
```
git checkout -b feature/IDEA-048-real-time-budget-optimization
```

**3. Implement with Comments:**
```typescript
/**
 * IDEA-048: Real-time Budget Optimization
 * 
 * Automatically adjusts ad spend based on real-time performance.
 */
class BudgetOptimizer {
  // Implementation
}
```

**4. Commit:**
```
[IDEA-048] Add real-time budget optimization

Implements AI-powered real-time budget optimization that
automatically adjusts spending based on performance metrics.

Features:
- Real-time performance monitoring
- Automatic pause for underperformers
- Budget reallocation to winners

Implements: IDEA-048
Related: IDEA-029 (Thompson Sampling)
```

**5. Create PR:**
```
Title: [IDEA-048] Add real-time budget optimization
[Use PR template with full details]
```

**6. Update Documentation:**
- Add to IDEAS_CATALOG.md
- Add to TRACEABILITY_MAP.md
- Update WHERE_ARE_WE_NOW.md
- Create feature documentation

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-07 | 1.0.0 | Initial version |

---

## Questions and Support

For questions about these conventions:

1. Check existing documentation in `/docs/`
2. Review examples in git history
3. Open a discussion in GitHub Discussions
4. Contact repository maintainers

---

**Last Updated:** 2025-12-07  
**Version:** 1.0.0  
**Maintained By:** Repository maintainers  
**Next Review:** 2025-01-07  
