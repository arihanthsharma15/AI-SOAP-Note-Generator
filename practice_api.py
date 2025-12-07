from fastapi import FastAPI
from pydantic import BaseModel
class ToDoItem(BaseModel):
   task:str

app = FastAPI()
@app.get("/")
def read_root():
  return {"message":"Welcome to my to do list"}


to_do_db = [
    {"id":1,"task":"Learn fast API"},
    {"id":2,"task":"Learning endpoints"},
    {"id": 3, "task": "Conquer the world"},
]
@app.get("/todos")
def get_all_to_dos():
    return to_do_db

@app.post("/todos")
def create_todo_item(item:ToDoItem):
   new_id = len(to_do_db)+1
   new_item_dict = {"id":new_id,"task":item.task}
   to_do_db.append(new_item_dict)
   return {"message": "To-do item added successfully!", "new_item": new_item_dict}