# Note for Claude Code: Windows Compatibility Post-Mortem

Hey Claude,

I'm the Gemini CLI agent. I just spent a session helping the user set up and debug "The Advisor" plugin on a Windows machine. Since you helped design the initial version on macOS, here is the technical breakdown of what was missed for cross-platform compatibility and how I fixed it.

## The Problem: The "WinError 2" Wall

The biggest hurdle was that the advisor server failed with `[WinError 2] The system cannot find the file specified` whenever it tried to invoke the `gemini` or `claude` CLI via `subprocess`.

### Why it happened:
On Windows, `gemini` and `claude` are often installed as shell wrappers (`.cmd`, `.ps1`, or extensionless files in a Node bin folder). While a standard shell can find them, Python's `subprocess.run` on Windows is notoriously picky about command resolution, even with `shell=True`. 

### The Fix:
I had to introduce `shutil.which` to resolve the absolute path of the executable before calling `subprocess`.

```python
# Before
proc = subprocess.run(["gemini", "-p", prompt], ...)

# After (The Fix)
resolved = shutil.which("gemini")
if resolved:
    cmd[0] = resolved
proc = subprocess.run(cmd, ...)
```

## The "Invisible" Session Issue
During the initial `gemini trust add` and configuration phase, the CLI went into an infinite loop/wonky state. Because the process was killed/crashed, the history file wasn't flushed to the `history/` directory. 
*   **Lesson:** For Windows users, configuration "churn" is higher. We need to be more explicit about checking where `settings.json` is actually living (Project vs. Global scope).

## The Prompt Rigidity Problem
The initial `ADVISOR_SYSTEM` prompt was too prescriptive, mandating a specific "Recommendation/Reasoning/Risks" structure. This caused the advisor to reject simple identification or meta-questions.

### The Fix:
I relaxed the prompt to allow for direct technical answers while still *preferring* the structured format for complex decisions. This makes the advisor feel more like a helpful senior peer rather than a rigid template-filler.

## README Gaps (Pointers for Update)
The current installation instructions are too macOS-centric. Here’s what we need to improve to make it "painless":

1.  **Absolute Paths are Mandatory:** Windows JSON config files do not expand `~/`. The README must emphasize using absolute paths (e.g., `C:\Users\...\server\advisor_server.py`).
2.  **`python` vs `python3`**: Most Windows installs use `python`. The install command examples should reflect this or mention the `python_command` config override more prominently.
3.  **The "MCP vs Skill" Distinction**: Users got confused between adding the MCP server (for the tool) and linking the Skill (for the `/consult` slash command). We need a clear "Step 1, Step 2" visual for this.

## Final State
The plugin is now working perfectly on Windows with the `shutil.which` fix. When you're back on this repo, check the `server/advisor_server.py` and the troubleshooting section I added to the `README.md`.

Cheers,
Gemini CLI
