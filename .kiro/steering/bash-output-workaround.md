---
inclusion: always
---

# Bash Command Output Workaround

## Issue
Direct bash command stdout is not being captured properly via `executeBash` tool. Only the shell prompt and exit code are returned.

## SOLUTION: Use Wrapper Script

**DEFAULT BEHAVIOR**: Whenever you use `executeBash` and need to see the output, use the `.kiro_exec.sh` wrapper script.

### The Pattern (Simple!)
```bash
./.kiro_exec.sh your_command arg1 arg2 ...
```

**Then IMMEDIATELY read**: `.kiro_command_output.txt`

⚠️ **CRITICAL**: The output file is **overwritten on every execution**. Always read it before running another command!

---

## What the Script Does Automatically

- ✅ Captures both stdout and stderr merged
- ✅ Strips ANSI color codes (saves tokens, improves readability)
- ✅ Limits output to 1000 lines (prevents token waste on huge logs)
- ✅ Adds truncation notice if output was limited (at the top)
- ✅ **Preserves original command exit code** (check with `echo $?` after script runs)
- ✅ **ALWAYS writes to `.kiro_command_output.txt` in workspace root** (regardless of where command runs)
- ✅ Handles edge cases: missing commands, empty output, files without trailing newlines

---

## Common Usage Examples

### Basic Commands
```bash
# List files with details
./.kiro_exec.sh ls -la

# Check git status
./.kiro_exec.sh git status

# Read file contents
./.kiro_exec.sh cat package.json

# Search in files
./.kiro_exec.sh grep -r "TODO" src/
```

### Running Tests & Scripts
```bash
# Run npm tests
./.kiro_exec.sh npm test

# Run Python script
./.kiro_exec.sh python script.py --arg value

# Execute Node script
./.kiro_exec.sh node index.js
```

### Commands with Pipes or Special Characters
**Quote them in a subshell:**
```bash
# Single pipe
./.kiro_exec.sh bash -c "cat file.txt | grep pattern"

# Multiple pipes
./.kiro_exec.sh bash -c "ps aux | grep node | wc -l"

# With redirections (if you need to see intermediate output)
./.kiro_exec.sh bash -c "make build 2>&1 | tee build.log"
```

### Checking Exit Codes
```bash
# Run command
./.kiro_exec.sh npm test

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo "Tests passed!"
else
    echo "Tests failed! Check .kiro_command_output.txt"
fi
```

---

## When to Apply

### ✅ ALWAYS Use the Wrapper When:
- You need to see command output (99% of cases)
- Running diagnostic commands: `ls`, `cat`, `echo`, `grep`, `find`, `ps`, `df`
- Running version checks: `node -v`, `python --version`, `git --version`
- Checking status: `git status`, `npm ls`, `docker ps`
- Running builds, tests, or scripts: `npm test`, `pytest`, `make`
- Any command where you need to inspect what happened

### ⛔ SKIP the Wrapper Only When:
- **Pure file operations** where you only need exit code:
  - `mkdir -p dir/` (you just need to know if it succeeded)
  - `touch newfile.txt` (creating empty file)
  - `rm -f oldfile.txt` (deleting file)
  - `cp src.txt dest.txt` (copying file)
  - `mv old.txt new.txt` (renaming file)
- You genuinely don't care about the output (very rare!)

**Rule of Thumb**: If you might need to debug the command later, use the wrapper!

---

## Running in Subdirectories

When using the `path` parameter in `executeBash`:

```bash
# Example: Running tests in a subdirectory
# executeBash with path="./backend"
../.kiro_exec.sh npm test

# Output is ALWAYS at workspace root!
# Read from: .kiro_command_output.txt (workspace root)
```

**Key Points**:
- Use `../.kiro_exec.sh` (go up one level) from subdirectories
- Use `../../.kiro_exec.sh` from nested subdirectories, etc.
- Output file location is **ALWAYS** `.kiro_command_output.txt` in workspace root
- No need to track different paths based on working directory!

---

## Workflow Pattern

```bash
# 1. Run command with wrapper
./.kiro_exec.sh npm run build

# 2. IMMEDIATELY read output (before running anything else!)
cat .kiro_command_output.txt

# 3. Check exit code if needed
if [ $? -ne 0 ]; then
    echo "Build failed!"
fi

# 4. Take action based on results
# ... your logic here ...
```

---

## Troubleshooting

### Problem: Output file is empty
**Causes:**
- Command genuinely produced no output
- Command name is wrong (check for typos)
- File not found (check `.kiro_command_output.txt` exists in workspace root)

**Debug:**
```bash
# Check if script ran
ls -la .kiro_command_output.txt

# Try a simple command
./.kiro_exec.sh echo "test"
cat .kiro_command_output.txt
# Should show: test
```

### Problem: "Command not found" error
**Solution:**
```bash
# Make sure script is executable
chmod +x .kiro_exec.sh

# Use full path if needed
/workspace/.kiro_exec.sh your_command
```

### Problem: Exit code is always 0 even when command fails
**Cause:** Your shell may have `set -e` or is swallowing errors.

**Solution:** The improved script uses `set -o pipefail` and captures exit codes correctly. Update to latest version.

### Problem: Special characters in command are breaking
**Solution:** Wrap in bash -c with proper quoting:
```bash
# Wrong
./.kiro_exec.sh echo "test" > file.txt  # Redirects wrapper output!

# Correct
./.kiro_exec.sh bash -c "echo 'test' > file.txt"
```

### Problem: Output is truncated but I need everything
**Solution:** The script limits to 1000 lines by default. If you need more:

```bash
# Temporarily modify MAX_LINES in .kiro_exec.sh
# Or run command directly and redirect to file:
your_command > full_output.txt 2>&1
cat full_output.txt  # Read in chunks
```

---

## Advanced: Debug Mode

Enable verbose debugging:
```bash
# Set debug flag before running
export KIRO_DEBUG=1
./.kiro_exec.sh your_command

# Output will include debug info at the end:
# [DEBUG] Command: your_command
# [DEBUG] Exit code: 0
# [DEBUG] Original lines: 42
```

---

## Important Notes

- 📝 The output file is **overwritten** on each run - always read before next execution!
- 🔢 Exit codes are preserved - check `$?` immediately after wrapper runs
- 📏 Output auto-limited to 1000 lines - check for truncation notice
- 🎨 ANSI codes are stripped automatically - colors removed but readability improved
- 🗑️ `.kiro_command_output.txt` is in `.gitignore` - won't be committed
- ⏰ This is a **TEMPORARY** workaround until the underlying `executeBash` bug is fixed

---

## Quick Reference Card

```bash
# Basic pattern
./.kiro_exec.sh COMMAND [ARGS...]

# Read output
cat .kiro_command_output.txt

# From subdirectory
../.kiro_exec.sh COMMAND

# With pipes (quote it!)
./.kiro_exec.sh bash -c "cmd1 | cmd2"

# Check exit code
echo $?  # Run immediately after wrapper
```

**Remember**: Output file is at workspace root ALWAYS, and is overwritten EVERY TIME!