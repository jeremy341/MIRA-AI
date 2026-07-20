# Memory for opencode

## Actions to take later
- Remove `.freebuff/` from local tracking — already added to `.gitignore`, but files may still be cached locally. Run `git rm -r --cached .freebuff` if needed.
- Clean up test datasets created during merge testing (e.g., `datasets/mira_test/`)
- Benchmark gianlucasposito_yolov8n.pt against mira_exp017.pt on the mira_all validation set
- After testing, remove temporary VS Code launch test artifacts if any
