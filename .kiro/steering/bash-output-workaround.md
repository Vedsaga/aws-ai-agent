---
inclusion: always
---

---
inclusion: always
---

# Bash Command Output Capture

## Core Rule

When using `executeBash` and you need to see command output, use the wrapper script:

```bash
./.kiro_exec.sh your_command args...
```

Then immediately read `.kiro_command_output.txt` before running any other command.

## Critical Behaviors

- Output file is **overwritten on every execution** - read it immediately
- Output is **always** written to `.kiro_command_output.txt` in workspace root
- Exit codes are preserved - check with `echo $?` after wrapper runs
- Output limited to 1000 lines (truncation notice added if exceeded)
- ANSI color codes are automatically stripped

## When to Use

**Use wrapper for (99% of cases):**
- Any command where you need to see output
- Diagnostics: `ls`, `cat`, `grep`, `find`, `ps`, `df`
- Version checks: `node -v`, `python --version`
- Status checks: `git status`, `npm ls`
- Running tests/builds: `npm test`, `pytest`, `make`

**Skip wrapper only for:**
- Pure file operations where only exit code matters: `mkdir`, `touch`, `rm`, `cp`, `mv`

## Usage Patterns

### Basic Commands
```bash
./.kiro_exec.sh ls -la
./.kiro_exec.sh npm test
./.kiro_exec.sh python script.py --arg value
```

### Commands with Pipes/Special Characters
Wrap in bash -c with quotes:
```bash
./.kiro_exec.sh bash -c "cat file.txt | grep pattern"
./.kiro_exec.sh bash -c "ps aux | grep node | wc -l"
```

### From Subdirectories
When using `path` parameter in executeBash:
```bash
# From ./backend directory
../.kiro_exec.sh npm test

# From ./backend/src directory  
../../.kiro_exec.sh npm test

# Output is ALWAYS at workspace root: .kiro_command_output.txt
```

## Standard Workflow

```bash
# 1. Run command
./.kiro_exec.sh npm run build

# 2. Read output immediately
cat .kiro_command_output.txt

# 3. Check exit code if needed
echo $?
```

## Common Issues

**Empty output file:**
- Command produced no output, or command not found
- Verify: `./.kiro_exec.sh echo "test"` then `cat .kiro_command_output.txt`

**Special characters breaking:**
- Wrong: `./.kiro_exec.sh echo "test" > file.txt` (redirects wrapper output)
- Correct: `./.kiro_exec.sh bash -c "echo 'test' > file.txt"`

**Need more than 1000 lines:**
- Redirect directly: `your_command > output.txt 2>&1` then read file