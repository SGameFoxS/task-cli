# Task manager

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)

## Features

- Add, Update, and Delete tasks

- Mark a task as in progress or done

- List all tasks

- List all tasks that are done

- List all tasks that are not done

- List all tasks that are in progress

## Example

The list of commands and their usage is given below:

```bash
# Adding a new task
task-cli add "Buy groceries"
# Output: Task added successfully (ID: 1)

# Updating and deleting tasks
task-cli update 1 "Buy groceries and cook dinner"
task-cli delete 1

# Marking a task as in progress or done
task-cli mark-in-progress 1
task-cli mark-done 1

# Listing all tasks
task-cli list

# Listing tasks by status
task-cli list done
task-cli list todo
task-cli list in-progress
```

## Task Properties

- `id`: A unique identifier for the task

- `description`: A short description of the task

- `status`: The status of the task (todo, in-progress, done)

- `createdAt`: The date and time when the task was created

- `updatedAt`: The date and time when the task was last updated

## Project structure

```bash
click-cli/
├─ app/                         # application source code
│  ├─ __init__.py               # app package
│  ├─ main.py                   # entry point / runner
│  ├─ cli.py                    # command implementations (add/update/delete/list/mark-*)
│  ├─ commands.py               # root Click group / CLI wiring
│  ├─ enums.py                  # enums (e.g., task statuses)
│  ├─ schemas.py                # data schemas/models (Task, etc.)
│  └─ repo.py                   # repository/storage layer (CRUD, file persistence)
├─ .gitignore
├─ .python-version
├─ pyproject.toml               # dependencies and console script entry point
├─ README.md                    # project description and usage examples
└─ uv.lock                      # dependency lockfile (uv)
```
