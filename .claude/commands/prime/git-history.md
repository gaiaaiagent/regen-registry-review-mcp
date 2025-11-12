# Get Git History Context

RUN:
    git ls-files
    git log --oneline --graph --decorate -20
    git log --stat -5
    git log -p -2
