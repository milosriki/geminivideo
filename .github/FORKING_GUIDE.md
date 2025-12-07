# Forking This Repository - URL Update Guide

If you've forked this repository and want to use the GitHub Projects documentation and issue templates, you'll need to update some URLs to point to your fork.

## 🔄 Files That Need URL Updates

### Required Updates

These files contain hardcoded repository URLs that must be updated for full functionality:

#### 1. `.github/ISSUE_TEMPLATE/config.yml`

Update lines 4, 7, and 10:

```yaml
# Before (lines need updating):
url: https://github.com/milosriki/geminivideo/blob/main/GITHUB_PROJECTS_GUIDE.md
url: https://github.com/milosriki/geminivideo/discussions
url: https://github.com/milosriki/geminivideo/blob/main/README.md

# After (replace with your fork):
url: https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/blob/main/GITHUB_PROJECTS_GUIDE.md
url: https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/discussions
url: https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/blob/main/README.md
```

#### 2. `README.md`

Update line 266 (the "Submit a new idea" link):

```markdown
# Before:
[**Submit a new idea →**](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)

# After:
[**Submit a new idea →**](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/issues/new?template=idea.yml)
```

#### 3. `.github/README.md`

Update lines 50, 96, and 182:

```markdown
# Before:
[Use the Idea Template](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)
[Create Idea](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)
[Discussion](https://github.com/milosriki/geminivideo/discussions)

# After:
[Use the Idea Template](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/issues/new?template=idea.yml)
[Create Idea](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/issues/new?template=idea.yml)
[Discussion](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME/discussions)
```

## ✅ Files That Work Automatically

These files use relative paths and will work in your fork without changes:

- `.github/GITHUB_PROJECTS_INDEX.md` - Uses relative paths like `../issues`
- `.github/IDEA_WORKFLOW.md` - Uses relative paths
- `.github/PROJECTS_QUICK_REFERENCE.md` - Uses relative paths
- `.github/PROJECT_SETUP_EXAMPLE.md` - Uses relative paths
- `GITHUB_PROJECTS_GUIDE.md` - Generic instructions, no repository-specific URLs

## 🤖 Automated Update Script

You can use this script to automatically update URLs after forking:

```bash
#!/bin/bash
# update-fork-urls.sh

# Usage: ./update-fork-urls.sh YOUR-USERNAME YOUR-REPO-NAME

if [ $# -ne 2 ]; then
    echo "Usage: $0 YOUR-USERNAME YOUR-REPO-NAME"
    echo "Example: $0 johndoe my-video-project"
    exit 1
fi

USERNAME=$1
REPONAME=$2

echo "Updating URLs to point to $USERNAME/$REPONAME..."

# Update config.yml
sed -i "s|milosriki/geminivideo|$USERNAME/$REPONAME|g" .github/ISSUE_TEMPLATE/config.yml

# Update README.md
sed -i "s|milosriki/geminivideo|$USERNAME/$REPONAME|g" README.md

# Update .github/README.md
sed -i "s|milosriki/geminivideo|$USERNAME/$REPONAME|g" .github/README.md

echo "✅ URLs updated successfully!"
echo "Changed: milosriki/geminivideo → $USERNAME/$REPONAME"
echo ""
echo "Files updated:"
echo "  - .github/ISSUE_TEMPLATE/config.yml"
echo "  - README.md"
echo "  - .github/README.md"
```

### Using the Script

1. Save the script above as `update-fork-urls.sh`
2. Make it executable: `chmod +x update-fork-urls.sh`
3. Run it: `./update-fork-urls.sh your-username your-repo-name`
4. Commit the changes: `git commit -am "Update URLs for fork"`

## 🔍 Manual Update Guide

If you prefer to update manually:

### Step 1: Find and Replace

Use your editor's find-and-replace feature:

- **Find**: `milosriki/geminivideo`
- **Replace**: `your-username/your-repo-name`
- **Files**: 
  - `.github/ISSUE_TEMPLATE/config.yml`
  - `README.md`
  - `.github/README.md`

### Step 2: Verify Changes

After updating, verify the links work:

1. Go to your repository on GitHub
2. Click the "Submit a new idea" link in README.md
3. Check that the issue template form appears
4. Verify links in `.github/ISSUE_TEMPLATE/config.yml` work

### Step 3: Test Issue Templates

1. Navigate to your repository → Issues tab
2. Click "New issue"
3. Verify you see the "💡 Idea / Feature Request" template
4. Check that the contact links in the sidebar work

## 📋 Checklist

After forking, use this checklist:

- [ ] Update `.github/ISSUE_TEMPLATE/config.yml`
- [ ] Update `README.md` "Submit a new idea" link
- [ ] Update `.github/README.md` template and discussion links
- [ ] Test issue template functionality
- [ ] Verify all links in config.yml work
- [ ] Test "Submit a new idea" link from README
- [ ] Commit and push changes

## 💡 Why These Updates Are Needed

GitHub issue templates and some other features require absolute URLs because:

1. **Issue Template Links**: The `?template=` query parameter is a GitHub-specific feature that needs the full repository path
2. **Discussions**: GitHub Discussions don't support relative links in all contexts
3. **Config Links**: Issue template contact links require absolute URLs for the sidebar

Other documentation uses relative paths (like `../issues`) which automatically work in forks.

## 🆘 Troubleshooting

### Issue Template Not Showing

If the "💡 Idea / Feature Request" template doesn't appear:

1. Check that `.github/ISSUE_TEMPLATE/idea.yml` exists
2. Verify the YAML syntax is valid
3. Wait a few minutes - GitHub may need time to process
4. Clear your browser cache

### Links Not Working

If links return 404 errors:

1. Verify you updated all URLs to your fork
2. Check that you enabled Issues in your repository settings
3. Enable Discussions if using discussion links
4. Ensure the target files exist in your fork

### Need Help?

If you encounter issues after updating:

1. Compare your files with the original repository
2. Check GitHub's [issue template documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
3. Open an issue in the original repository for guidance

## 🔗 Additional Resources

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Issue Template Syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub Discussions](https://docs.github.com/en/discussions)

---

**Remember**: After making these updates, commit and push your changes so they're available to your collaborators!

```bash
git add .github/ISSUE_TEMPLATE/config.yml README.md .github/README.md
git commit -m "chore: Update repository URLs for fork"
git push origin main
```
