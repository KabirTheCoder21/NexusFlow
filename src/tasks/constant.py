from src.tasks.enums import TaskStatus


ALLOWED_TASK_STATUS_TRANSITIONS = {
    TaskStatus.TODO: [
        TaskStatus.IN_PROGRESS
    ],
    TaskStatus.IN_PROGRESS: [
        TaskStatus.COMPLETED
    ],
    TaskStatus.COMPLETED: [
        TaskStatus.IN_PROGRESS
    ]
}