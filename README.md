# DSO-576-T5 Project

## Team Members

- tinyuxieUSC
- giselleluk
- leynanguyen0818
- gigizhuwq
- Zhongze Zhou

## Pull, Commit, Push, and Resolve Git Issues

Before starting work, open a terminal in the project folder and pull the latest
changes from GitHub:

```bash
git pull origin main
```

If you are working on a different branch, replace `main` with your branch name.

After editing and saving your files, check what changed:

```bash
git status
```

Stage your changes:

```bash
git add .
```

Commit the staged changes with a short, descriptive message:

```bash
git commit -m "Describe your changes"
```

Before pushing, pull once more in case a teammate pushed new work while you
were editing:

```bash
git pull origin main
```

If there are no conflicts, push your commit:

```bash
git push origin main
```

### Common Git and Merge Scenarios

#### 1. Merge conflict after `git pull`

A merge conflict happens when Git cannot automatically combine your changes
with a teammate's changes, usually because both people edited the same lines.

Check which files have conflicts:

```bash
git status
```

Open each conflicted file. Git will mark the conflicting area like this:

```text
<<<<<<< HEAD
your version
=======
teammate's version
>>>>>>> incoming-commit
```

Decide what the final version should be, edit the file, and remove the
`<<<<<<<`, `=======`, and `>>>>>>>` markers.

Then stage, commit, and push the resolved file:

```bash
git add <filename>
git commit -m "Resolve merge conflict"
git push origin main
```

Do not leave conflict markers in the final file.

#### 2. Push rejected because the remote branch has new commits

You may see an error such as `rejected`, `non-fast-forward`, or `fetch first`.
This usually means a teammate pushed before you.

Pull the latest changes first:

```bash
git pull origin main
```

If Git merges automatically, push again:

```bash
git push origin main
```

If a merge conflict appears, resolve it using the steps in Scenario 1.

#### 3. `git pull` is blocked because you have uncommitted changes

Git may refuse to pull if your local edits would be overwritten.

First check your changes:

```bash
git status
```

If the work is ready, commit it:

```bash
git add .
git commit -m "Save work before pulling"
git pull origin main
```

If the work is not ready to commit, temporarily save it with stash:

```bash
git stash
git pull origin main
git stash pop
```

If `git stash pop` creates a conflict, resolve it the same way as a normal
merge conflict.

#### 4. You accidentally staged a file

To remove one file from the staging area without deleting your edits:

```bash
git restore --staged <filename>
```

To unstage everything:

```bash
git restore --staged .
```

#### 5. You changed a file but want to discard those local changes

Use this only if you are sure you do not need the edits:

```bash
git restore <filename>
```

This replaces your local version with the last committed version.

#### 6. You committed locally but have not pushed yet and want to change the commit message

```bash
git commit --amend -m "New commit message"
```

Then push normally:

```bash
git push origin main
```

#### 7. You are not sure what Git is doing

Start with:

```bash
git status
```

`git status` usually tells you whether you are in the middle of a merge, have
uncommitted changes, have conflicts, or have commits waiting to be pushed.

### Recommended Team Workflow

To reduce merge conflicts:

1. Run `git pull origin main` before starting work.
2. Avoid having multiple teammates edit the same file at the same time when possible.
3. Make small commits with clear messages.
4. Pull again before pushing.
5. If Git reports a conflict, resolve it carefully instead of overwriting a teammate's work.
6. Run `git status` before and after resolving a problem to confirm the repository is clean.

