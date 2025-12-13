# Git Rebase Guide - Understanding and Using Rebase

This guide explains what rebase is, when to use it, and how to handle rebase situations in the geminivideo repository.

---

## 📚 What is Rebase?

**Simple Explanation:** A rebase is like rewriting history to make your commits appear as if they were made on top of the latest code, instead of having a messy merge history.

---

## 🎯 Visual Comparison: Rebase vs Merge

### Without Rebase (Merge):
```
Main branch:     A---B---C---D---E (latest)
                        \
Your branch:              F---G---H
                         
After merge:     A---B---C---D---E---M (merge commit)
                        \           /
                         F---G---H
```
- Creates a "merge commit" (M)
- History looks messy with branches
- Shows that you branched off at C

### With Rebase:
```
Main branch:     A---B---C---D---E (latest)
                        \
Your branch:              F---G---H

After rebase:    A---B---C---D---E---F'---G'---H'
```
- No merge commit
- Clean, linear history
- Looks like you started from E (latest)
- F', G', H' are "replayed" versions of your commits

---

## 🔄 How Rebase Works

1. **Takes your commits** (F, G, H)
2. **Temporarily removes them**
3. **Moves to the latest main branch** (E)
4. **Replays your commits one by one** on top (F', G', H')

**Result:** Your work appears as if it was always based on the latest code.

---

## 🆚 Rebase vs Merge

### **Merge:**
- ✅ Safe - doesn't change history
- ✅ Preserves exact timeline
- ✅ Good for shared branches
- ❌ Creates merge commits
- ❌ Messy history with branches

### **Rebase:**
- ✅ Clean, linear history
- ✅ No merge commits
- ✅ Easier to read and understand
- ✅ Professional-looking commit history
- ⚠️ Rewrites history (can be dangerous if shared)
- ⚠️ May require resolving conflicts

---

## 🚀 When to Use Rebase

### **Use Rebase When:**
- ✅ Working on a feature branch
- ✅ Want clean history
- ✅ Haven't shared your branch yet
- ✅ Working solo or on your own branch
- ✅ Updating your branch with latest main changes

### **Don't Use Rebase When:**
- ❌ Others are using your branch
- ❌ Branch is already merged
- ❌ Working on main/master branch with team
- ❌ You're not sure what you're doing

---

## 📋 Common Rebase Commands

### Starting a Rebase
```bash
# Rebase current branch onto main
git rebase main

# Rebase onto a specific branch
git rebase origin/main

# Interactive rebase (to edit/squash/reorder commits)
git rebase -i HEAD~3  # Last 3 commits
```

### During a Rebase
```bash
# After resolving conflicts, continue
git rebase --continue

# Skip the current commit (if it's already applied)
git rebase --skip

# Abort the rebase and return to original state
git rebase --abort
```

### After Successful Rebase
```bash
# Push to remote (if branch is new or you're alone)
git push origin branch-name

# Force push if you've already pushed this branch
# ⚠️ Use with caution - only if you're sure!
git push --force-with-lease origin branch-name
```

---

## 🔧 Handling Rebase Conflicts

### Step-by-Step Conflict Resolution

1. **Start the rebase:**
   ```bash
   git rebase main
   ```

2. **Git reports conflicts:**
   ```
   CONFLICT (content): Merge conflict in file.js
   error: could not apply abc123... commit message
   ```

3. **Check which files have conflicts:**
   ```bash
   git status
   ```

4. **Edit conflicted files:**
   - Look for conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`
   - Keep the code you want
   - Remove the conflict markers

5. **Mark conflicts as resolved:**
   ```bash
   git add file.js
   ```

6. **Continue the rebase:**
   ```bash
   git rebase --continue
   ```

7. **Repeat steps 3-6 for each commit with conflicts**

8. **If stuck, abort:**
   ```bash
   git rebase --abort
   ```

---

## ⚠️ Important Warnings

### 1. **Never Rebase Public/Shared Branches**
```bash
# ❌ DON'T DO THIS on shared branches
git checkout main
git rebase feature-branch  # BAD!

# ✅ DO THIS instead
git checkout feature-branch
git rebase main  # GOOD!
```

### 2. **Force Push Carefully**
```bash
# ❌ Dangerous - can overwrite others' work
git push --force

# ✅ Safer - fails if someone else pushed
git push --force-with-lease
```

### 3. **Rebase Changes Commit IDs**
- After rebase, your commits get new SHA hashes
- Old commits (F, G, H) become new commits (F', G', H')
- This is why you shouldn't rebase shared branches

---

## 📖 Example Workflow

### Scenario: Update Feature Branch with Latest Main

```bash
# 1. Make sure main is up to date
git checkout main
git pull origin main

# 2. Go to your feature branch
git checkout feature/my-feature

# 3. Rebase onto latest main
git rebase main

# 4a. If no conflicts
git push --force-with-lease origin feature/my-feature

# 4b. If there are conflicts
# - Resolve conflicts in files
# - git add <resolved-files>
# - git rebase --continue
# - Repeat until complete
# - git push --force-with-lease origin feature/my-feature
```

### Scenario: Clean Up Commits Before Merge

```bash
# Interactive rebase to squash/edit commits
git rebase -i HEAD~5  # Last 5 commits

# In the editor:
# - Change 'pick' to 'squash' to combine commits
# - Change 'pick' to 'reword' to edit commit message
# - Reorder lines to reorder commits
# - Delete lines to remove commits

# Save and close editor
# Follow prompts to edit commit messages
```

---

## 🎓 Best Practices

1. **Commit Often, Rebase Before Pushing**
   - Make many small commits locally
   - Rebase/squash them into logical units before pushing

2. **Keep Feature Branches Updated**
   - Regularly rebase onto main to avoid big conflicts later
   - Smaller, frequent rebases are easier than one big one

3. **Use Interactive Rebase for Cleanup**
   - Before submitting a PR, clean up your commits
   - Squash "fix typo" and "oops" commits
   - Make each commit a logical, complete change

4. **Communicate with Team**
   - If you must rebase a shared branch, tell your team
   - Consider using merge instead for collaborative branches

5. **Test After Rebase**
   - Always run tests after rebasing
   - Conflicts might have introduced bugs

---

## 🆘 Troubleshooting

### "I'm in the middle of a rebase and confused"
```bash
# See current status
git status

# Abort and start over
git rebase --abort
```

### "I rebased and now everything is broken"
```bash
# Find your old commit
git reflog

# Reset to it (replace abc123 with your commit)
git reset --hard abc123
```

### "I force-pushed and broke my teammate's work"
- Apologize 😅
- Ask them not to pull yet
- Reset to the commit before your force push
- Use merge instead of rebase this time
- Learn from it: don't rebase shared branches!

---

## 📚 Additional Resources

- [Git Rebase Documentation](https://git-scm.com/docs/git-rebase)
- [Atlassian Git Rebase Tutorial](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase)
- [Pro Git Book - Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)

---

## ✅ Quick Reference

```bash
# Common rebase commands
git rebase main                    # Rebase onto main
git rebase --continue              # Continue after resolving conflicts
git rebase --skip                  # Skip current commit
git rebase --abort                 # Cancel rebase
git rebase -i HEAD~3               # Interactive rebase last 3 commits
git push --force-with-lease        # Safely force push after rebase

# Check rebase status
git status                         # Current state
git rebase --show-current-patch    # See current commit being applied
git log --graph --oneline          # Visualize commit history
```

---

**Remember:** Rebase is a powerful tool. Use it to keep your history clean, but be careful with shared branches!
