# Get Git History Context

RUN:
!git ls-files
!git log --oneline --graph --decorate -20
!git log --stat -10

If you need additional information about specific commits please investigate further. 
