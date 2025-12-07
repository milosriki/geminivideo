# GitHub Projects - Quick Reference Card

Fast reference for using GitHub Projects to manage ideas in the Gemini Video repository.

## 🚀 Quick Links

- **Create New Idea**: [Submit Idea Form](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)
- **View All Issues**: [Issues Page](https://github.com/milosriki/geminivideo/issues)
- **Project Boards**: [Projects Tab](https://github.com/milosriki/geminivideo/projects)
- **Full Guide**: [GitHub Projects Guide](../GITHUB_PROJECTS_GUIDE.md)

## 📋 Common Tasks

### Submit an Idea
1. Click [New Issue](https://github.com/milosriki/geminivideo/issues/new)
2. Select "💡 Idea / Feature Request"
3. Fill out the form
4. Click "Submit new issue"

### Add Idea to Project
1. Open the issue
2. Click "Projects" in right sidebar
3. Select your project
4. Choose the column (e.g., "Ideas")

### Track Progress
1. Go to [Projects Tab](https://github.com/milosriki/geminivideo/projects)
2. View your board
3. Drag items between columns as they progress

### Link PR to Idea
In your PR description, add:
```markdown
Closes #123
```
(where 123 is the issue number)

### Search Ideas
Use GitHub search with filters:
```
is:issue label:idea is:open
is:issue label:idea label:high-priority
is:issue author:@me label:idea
```

## 🏷️ Label Guide

| Label | Use For |
|-------|---------|
| `idea` | New ideas and suggestions |
| `enhancement` | Improvements to existing features |
| `high-priority` | Urgent and important |
| `needs-review` | Awaiting team review |
| `approved` | Ready for development |
| `in-progress` | Currently being worked on |
| `on-hold` | Deferred for later |

## 🔄 Workflow States

```
💡 Ideas → 🔍 Review → ✅ Approved → 🚧 Development → ✨ Done
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `C` | Create new issue |
| `G` then `I` | Go to Issues |
| `G` then `P` | Go to Projects |
| `/` | Focus search |
| `?` | Show all shortcuts |

## 📊 Project Views

1. **Board**: Kanban-style columns
2. **Table**: Spreadsheet view with custom fields
3. **Roadmap**: Timeline view for planning

Switch views using the tabs at the top of your project.

## 🔍 Useful Filters

In your project, filter by:
- **Priority**: `priority:high`
- **Category**: `category:"AI/ML Features"`
- **Status**: `status:"In Progress"`
- **Assignee**: `assignee:@me`

## 💡 Pro Tips

1. **Use Draft Issues**: Quickly capture ideas, add details later
2. **Link Related Ideas**: Reference other issues with `#issue-number`
3. **Use Milestones**: Group ideas by release or sprint
4. **Add Reactions**: 👍 upvote ideas you like
5. **Subscribe**: Click "Subscribe" to get notifications on ideas you care about
6. **Use Templates**: Always use the idea template for consistency

## 🎯 Best Practices

✅ **Do:**
- Search before creating duplicate ideas
- Be specific and clear in titles
- Explain the "why" not just the "what"
- Add relevant labels and categories
- Link to related issues

❌ **Don't:**
- Create vague or overly broad ideas
- Skip the template fields
- Expect immediate implementation
- Mix multiple unrelated ideas in one issue

## 🆘 Need Help?

- **Full Documentation**: [GitHub Projects Guide](../GITHUB_PROJECTS_GUIDE.md)
- **Ask Questions**: Open a [Discussion](https://github.com/milosriki/geminivideo/discussions)
- **Report Issues**: Create an issue with `question` label

---

**Quick Start**: [Create your first idea now →](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)
