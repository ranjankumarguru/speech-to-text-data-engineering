\# Git \& GitHub — Reusable Project Setup Guide



\## Purpose



This document is a reusable reference for taking a completed local project, putting it under Git version control, and publishing it to GitHub.



The goal is that the next project can be published independently without needing to remember every Git command.



\---



\# PART 1 — Understand the Git Workflow



Before running commands, understand the basic flow:



```text

PROJECT FILES

&#x20;    │

&#x20;    ▼

Working Directory

&#x20;    │

&#x20;    │ git add

&#x20;    ▼

Staging Area

&#x20;    │

&#x20;    │ git commit

&#x20;    ▼

Local Git Repository

&#x20;    │

&#x20;    │ git push

&#x20;    ▼

GitHub Repository

```



There are therefore two different things involved:



\### Git



Git is the version-control system running on your computer.



It tracks:



\* file changes

\* commits

\* branches

\* project history



\### GitHub



GitHub is the remote hosting service.



It stores a copy of your Git repository online and allows you to:



\* showcase projects

\* collaborate

\* access project history

\* share code with recruiters/interviewers

\* maintain remote backups



\---



\# PART 2 — One-Time Git Installation and Configuration



These steps normally need to be done only once on a computer.



\## Step 1 — Check whether Git is installed



\### Command



```cmd

git --version

```



\### What does it do?



Checks whether Git is installed and available from the Windows command line.



\### Expected result



Something similar to:



```text

git version 2.55.0.windows.5

```



If a Git version is displayed, Git is installed correctly.



\---



\## Step 2 — Find where Git is installed



\### Command



```cmd

where git

```



\### What does it do?



Shows the location of the Git executable that Windows is using.



\### Example



```text

C:\\Program Files\\Git\\cmd\\git.exe

```



\### Why are we doing this?



It confirms that Windows can find Git through PATH.



\---



\## Step 3 — Configure your Git name



\### Command



```cmd

git config --global user.name "Your Name"

```



\### What does it do?



Sets the name Git will associate with commits created on this computer.



\### Why are we doing this?



Every Git commit records an author.



\---



\## Step 4 — Configure your Git email



\### Command



```cmd

git config --global user.email "your-email@example.com"

```



\### What does it do?



Sets the email Git associates with your commits.



\### Why are we doing this?



Git uses the name and email to identify the author of commits.



\---



\## Step 5 — Verify the configuration



\### Command



```cmd

git config --global --list

```



\### What does it do?



Displays your global Git configuration.



\### Why are we doing this?



Always verify the configuration instead of assuming it worked.



Look for:



```text

user.name=Your Name

user.email=your-email@example.com

```



\---



\# PART 3 — Prepare a New Project Before Using Git



Assume the project is located at:



```text

C:\\YourProject

```



\## Step 6 — Move into the project directory



\### Command



```cmd

cd C:\\YourProject

```



\### What does it do?



Changes the current Command Prompt location to the project directory.



\### Why are we doing this?



Git commands should normally be executed from the project's root directory.



\---



\# PART 4 — Create .gitignore



\## Step 7 — Understand .gitignore



`.gitignore` tells Git:



> "Do not track these files or folders."



This is extremely important.



A project should generally NOT commit things such as:



```text

.venv/

\_\_pycache\_\_/

\*.pyc

.env

logs/

temporary files

generated output

large local datasets

```



\### Why are we doing this?



Some files are:



\* machine-specific

\* automatically generated

\* unnecessary in source control

\* potentially sensitive

\* too large

\* temporary development artifacts



For this Speech-to-Text project, the following were intentionally excluded:



```text

.venv/

\_\_pycache\_\_/

\*.pyc

data/

output/

logs/

\*.log

.env

```



The exact `.gitignore` depends on the project.



\---



\# PART 5 — Initialize Git



\## Step 8 — Initialize the repository



\### Command



```cmd

git init

```



\### What does it do?



Creates a hidden `.git` directory inside the project.



That `.git` directory contains Git's internal repository information.



\### Important



`git init` does NOT:



\* upload anything

\* create a GitHub repository

\* commit files



It only tells Git:



> "Start managing this directory as a Git repository."



\---



\# PART 6 — Inspect the Project



\## Step 9 — Check Git status



\### Command



```cmd

git status

```



\### What does it do?



Shows the current state of the repository.



It tells you things such as:



\* current branch

\* untracked files

\* modified files

\* staged files

\* whether the working tree is clean



\### Why is this important?



`git status` is one of the most important Git commands.



When unsure about what Git is going to do:



```text

STOP → git status → inspect → continue

```



Do not blindly continue with Git commands.



\---



\# PART 7 — Stage the Files



\## Step 10 — Add files to the staging area



\### Command



```cmd

git add .

```



\### What does it do?



Moves eligible changes from the working directory into the staging area.



The `.` means:



> Add changes from the current directory and its subdirectories.



Files excluded by `.gitignore` are not staged.



\### Why are we doing this?



Git uses the staging area to decide exactly what will become part of the next commit.



Think:



```text

Working Directory

&#x20;      │

&#x20;      │ git add .

&#x20;      ▼

Staging Area

```



\### Important



`git add .` does NOT:



\* commit the files

\* upload the files to GitHub



\---



\# PART 8 — Verify What Will Be Committed



\## Step 11 — Check status again



\### Command



```cmd

git status

```



\### What does it do?



Shows which files are now staged.



\### Why are we doing this?



This is an important safety checkpoint.



Before committing, make sure you do NOT see things such as:



```text

.env

password files

API keys

.venv/

large datasets

temporary files

```



For the Speech-to-Text project, the intended tracked files were:



```text

.gitignore

docs/PROJECT\_DOCUMENTATION.md

pyspark\_pipeline.py

test\_sql\_connection.py

transcribe.py

```



\---



\# PART 9 — Create the First Commit



\## Step 12 — Create a commit



\### Command



```cmd

git commit -m "Initial project commit"

```



\### What does it do?



Creates a permanent snapshot of the staged files in the local Git repository.



The message:



```text

Initial project commit

```



describes what this commit represents.



\### Why are we doing this?



A commit is the fundamental unit of Git history.



Think:



```text

Staging Area

&#x20;    │

&#x20;    │ git commit

&#x20;    ▼

Local Git Repository

```



The commit receives a unique identifier called a commit hash.



Example:



```text

bbf1c11

```



\---



\# PART 10 — Rename the Main Branch



\## Step 13 — Rename the current branch to main



\### Command



```cmd

git branch -M main

```



\### What does it do?



Renames the current branch to:



```text

main

```



\### Why are we doing this?



`main` is the conventional primary branch name used by most modern GitHub repositories.



\### Important



This command does NOT:



\* modify project files

\* create a new commit

\* upload anything



It only changes the branch name.



\---



\# PART 11 — Create the GitHub Repository



\## Step 14 — Create a new repository on GitHub



Go to GitHub and choose:



```text

New repository

```



Choose a project name.



For this project:



```text

speech-to-text-data-engineering

```



\### Important



Because the local project already contains:



\* Git history

\* a commit

\* `.gitignore`

\* project files



create the GitHub repository as an \*\*empty repository\*\*.



Normally do NOT initialize it with:



```text

README

.gitignore

License

```



unless you specifically intend to merge those files later.



\### Why?



We already have the local project and its Git history.



Starting with an empty remote avoids unnecessary merge/reconciliation work during the first push.



\---



\# PART 12 — Connect the Local Repository to GitHub



\## Step 15 — Add the GitHub remote



\### Command



```cmd

git remote add origin https://github.com/USERNAME/REPOSITORY.git

```



Example:



```cmd

git remote add origin https://github.com/yourusername/yourproject.git

```



\### What does it do?



Associates the local Git repository with the GitHub repository.



`origin` is the conventional name given to the main remote repository.



Think:



```text

LOCAL GIT REPOSITORY

&#x20;       │

&#x20;       │ origin

&#x20;       ▼

GITHUB REPOSITORY

```



\### Important



This command does NOT upload files yet.



It only establishes the connection information.



\---



\# PART 13 — Verify the Remote



\## Step 16 — Check the remote



\### Command



```cmd

git remote -v

```



\### What does it do?



Displays the remote repository URLs configured for the project.



\### Expected result



Something similar to:



```text

origin  https://github.com/USERNAME/REPOSITORY.git (fetch)

origin  https://github.com/USERNAME/REPOSITORY.git (push)

```



\### Why are we doing this?



It is much better to catch a wrong repository URL before pushing.



\---



\# PART 14 — First Push to GitHub



\## Step 17 — Push the main branch



\### Command



```cmd

git push -u origin main

```



\### What does it do?



Uploads the local `main` branch and its commits to GitHub.



Break the command down:



```text

git

&#x20;   → use Git



push

&#x20;   → send local commits to a remote



\-u

&#x20;   → set the upstream branch



origin

&#x20;   → remote GitHub repository



main

&#x20;   → branch being pushed

```



\### Why are we using `-u`?



It establishes:



```text

local main

&#x20;    ↕

origin/main

```



After this, future pushes can normally be done with:



```cmd

git push

```



instead of:



```cmd

git push origin main

```



\---



\# PART 15 — Final Verification



\## Step 18 — Check Git status



\### Command



```cmd

git status

```



\### What does it do?



Checks the final state of the local repository.



\### Healthy result



You want something similar to:



```text

On branch main

Your branch is up to date with 'origin/main'.



nothing to commit, working tree clean

```



\### Why are we doing this?



This confirms:



1\. You are on `main`.

2\. Your local branch is synchronized with GitHub.

3\. There are no uncommitted changes.



\---



\# PART 16 — Inspect GitHub



Open the GitHub repository in a browser.



Check:



```text

Repository

│

├── .gitignore

├── docs/

│   └── PROJECT\_DOCUMENTATION.md

├── pyspark\_pipeline.py

├── test\_sql\_connection.py

└── transcribe.py

```



Also verify that unwanted local files are NOT visible.



For example:



```text

.venv/

data/

output/

logs/

\_\_pycache\_\_/

```



should not appear if they are correctly ignored.



\---



\# PART 17 — Everyday Git Workflow



Once the repository already exists, you normally do NOT repeat:



```cmd

git init

git remote add origin ...

git push -u origin main

```



Those are mainly initial setup operations.



For normal development, use:



```text

Modify files

&#x20;    │

&#x20;    ▼

git status

&#x20;    │

&#x20;    ▼

git add .

&#x20;    │

&#x20;    ▼

git commit -m "Describe the change"

&#x20;    │

&#x20;    ▼

git push

&#x20;    │

&#x20;    ▼

git status

```



\---



\# PART 18 — Everyday Commands



\## Check repository status



```cmd

git status

```



\### Purpose



See what has changed and what is staged.



\---



\## Stage changes



```cmd

git add .

```



\### Purpose



Prepare changes for the next commit.



\---



\## Commit changes



```cmd

git commit -m "Describe the change"

```



\### Purpose



Create a local snapshot of the staged changes.



Example:



```cmd

git commit -m "Add word level comparison"

```



\---



\## Push changes



```cmd

git push

```



\### Purpose



Send committed changes to GitHub.



\---



\## View commit history



```cmd

git log --oneline

```



\### Purpose



Show a compact history of commits.



Example:



```text

a123456 Add retry handling

bbf1c11 Initial project commit

```



\---



\## View branches



```cmd

git branch

```



\### Purpose



Show local branches and identify the current branch.



The current branch is marked with:



```text

\*

```



\---



\## View remote repository



```cmd

git remote -v

```



\### Purpose



Show where the local repository connects for fetch and push.



\---



\## See unstaged changes



```cmd

git diff

```



\### Purpose



Show changes that have been made but have not yet been staged.



\---



\## See staged changes



```cmd

git diff --staged

```



\### Purpose



Show exactly what is currently staged for the next commit.



\---



\# PART 19 — Safe Working Habit



Before important Git operations:



```cmd

git status

```



After staging:



```cmd

git status

```



After committing:



```cmd

git status

```



After pushing:



```cmd

git status

```



The habit is:



```text

STATUS

&#x20; ↓

ACTION

&#x20; ↓

STATUS

```



This prevents many accidental Git operations.



\---



\# PART 20 — GitHub Authentication and Security



Never put the following into source code:



```text

GitHub password

Personal access token

Database password

API key

Connection secret

.env secrets

```



Do not commit them.



If a secret is accidentally committed, assume that it has been exposed and rotate/revoke it.



Use GitHub's supported authentication mechanisms or a credential manager instead of putting credentials directly into commands or source files.



\---



\# PART 21 — Complete First-Project Checklist



Use this checklist whenever publishing a completely new project.



```text

\[ ] Git installed

\[ ] Git name configured

\[ ] Git email configured



\[ ] Project directory opened

\[ ] Temporary files cleaned

\[ ] .gitignore created/updated



\[ ] git init

\[ ] git status

\[ ] git add .

\[ ] git status



\[ ] git commit -m "Initial project commit"



\[ ] git branch -M main



\[ ] Empty GitHub repository created



\[ ] git remote add origin <GitHub URL>

\[ ] git remote -v



\[ ] git push -u origin main

\[ ] git status



\[ ] GitHub repository inspected

\[ ] No secrets committed

\[ ] No unnecessary generated/local files committed

```



\---



\# PART 22 — The Entire First-Time Workflow in One Place



When you already understand the process, the complete workflow becomes:



```cmd

cd C:\\YourProject



git init



git status



git add .



git status



git commit -m "Initial project commit"



git branch -M main



git remote add origin https://github.com/USERNAME/REPOSITORY.git



git remote -v



git push -u origin main



git status

```



Do not blindly paste all commands.



The important sequence is:



```text

INIT

&#x20;↓

STATUS

&#x20;↓

ADD

&#x20;↓

STATUS

&#x20;↓

COMMIT

&#x20;↓

MAIN

&#x20;↓

REMOTE

&#x20;↓

PUSH

&#x20;↓

STATUS

```



\---



\# PART 23 — The Mental Shortcut



Remember this:



```text

CLEAN

&#x20; ↓

IGNORE

&#x20; ↓

INIT

&#x20; ↓

STATUS

&#x20; ↓

ADD

&#x20; ↓

STATUS

&#x20; ↓

COMMIT

&#x20; ↓

MAIN

&#x20; ↓

REMOTE

&#x20; ↓

PUSH

&#x20; ↓

STATUS

```



Or simply:



> \*\*Prepare → Inspect → Stage → Inspect → Commit → Connect → Push → Verify\*\*



That is the reusable Git/GitHub process.



\---



\# PART 24 — What We Did in the Speech-to-Text Project



For this project, the actual sequence was:



```text

C:\\SpeechToTextDE

&#x20;       │

&#x20;       ▼

Cleaned project

&#x20;       │

&#x20;       ▼

Updated .gitignore

&#x20;       │

&#x20;       ▼

git init

&#x20;       │

&#x20;       ▼

git status

&#x20;       │

&#x20;       ▼

git add .

&#x20;       │

&#x20;       ▼

git status

&#x20;       │

&#x20;       ▼

Initial project commit

&#x20;       │

&#x20;       ▼

Renamed branch to main

&#x20;       │

&#x20;       ▼

Created GitHub repository

&#x20;       │

&#x20;       ▼

Added origin

&#x20;       │

&#x20;       ▼

git push -u origin main

&#x20;       │

&#x20;       ▼

git status

&#x20;       │

&#x20;       ▼

Working tree clean

```



The initial commit contained the project source code and documentation while local/generated material was excluded through `.gitignore`.



\---



\# PART 25 — Future Project Example



Suppose the next project is:



```text

C:\\CustomerAnalyticsDE

```



The process is the same.



First:



```cmd

cd C:\\CustomerAnalyticsDE

```



Then:



```cmd

git init

git status

```



Create/check `.gitignore`.



Then:



```cmd

git add .

git status

git commit -m "Initial project commit"

git branch -M main

```



Create an empty GitHub repository, then:



```cmd

git remote add origin https://github.com/USERNAME/customer-analytics-de.git

git remote -v

git push -u origin main

git status

```



After that, normal development uses:



```cmd

git status

git add .

git commit -m "Describe the change"

git push

```



\---



\# Final Principle



Git becomes much easier once you stop thinking of the commands as separate magic commands.



Think in terms of four places:



```text

1\. Working Directory

&#x20;      ↓ git add



2\. Staging Area

&#x20;      ↓ git commit



3\. Local Repository

&#x20;      ↓ git push



4\. GitHub Repository

```



And remember:



```text

git add      = prepare changes

git commit   = save a snapshot locally

git push     = send commits to GitHub

git status   = inspect what is happening

```



If these four concepts are clear, the rest of the Git workflow becomes much easier to remember and reproduce.



