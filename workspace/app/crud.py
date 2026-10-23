from sqlalchemy.orm import Session
from app.models import TaskModel
from app.schemas import TaskCreate, TaskUpdate

def get_task(db: Session, task_id: int):
    return db.query(TaskModel).filter(TaskModel.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TaskModel).offset(skip).limit(limit).all()

def create_task(db: Session, task: TaskCreate):
    db_task = TaskModel(
        title=task.title.strip(),
        description=task.description.strip() if task.description else None
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: TaskUpdate):
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "title" and value is not None:
            value = value.strip()
        if key == "description" and value is not None:
            value = value.strip()
        setattr(db_task, key, value)
        
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    db.delete(db_task)
    db.commit()
    return db_task
