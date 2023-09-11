from typing import Dict, List
import bcrypt
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    Depends,
    status,
)
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": True})


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# List to store connected websocket clients
clients: list[WebSocket] = []


@app.websocket("/ws/community_chat/{user_id}")
async def community_chat_endpoint(
    websocket: WebSocket, user_id: int, db: Session = Depends(get_db)
):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            message_db_resp = crud.create_community_chat_message(
                db=db,
                message=schemas.CommunityChatMessageCreate(
                    message_text=message, user_id=user_id
                ),
            )

            for client in clients:
                await client.send_json(
                    {
                        "user_id": str(message_db_resp.user_id),
                        "message": str(message_db_resp.message_text),
                        "created_at": str(message_db_resp.created_at),
                    }
                )

    except Exception:
        clients.remove(websocket)


ticket_chats: Dict[int, List[WebSocket]] = {}


@app.websocket("/ws/{ticket_id}/{user_id}")
async def ticket_chat_endpoint(
    websocket: WebSocket, ticket_id: int, user_id: int, db: Session = Depends(get_db)
):
    ticket = crud.get_ticket(db, ticket_id)
    # If ticket is closed or not available then just do nothing
    if ticket is None or bool(ticket.is_open) == False:
        return

    # If some user aside from the users in ticket tries to join the room then do nothing
    # Ugly type casting, is there really no better way to do this?
    if int(str(ticket.user_id)) != user_id and int(str(ticket.teacher_id)) != user_id:
        return

    await websocket.accept()
    ticket_chats[ticket_id].append(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            message_db_resp = crud.create_ticket_message(
                db=db,
                message=schemas.TicketChatMessageCreate(
                    ticket_id=ticket_id, message_text=message, user_id=user_id
                ),
            )
            for client in ticket_chats[ticket_id]:
                await client.send_json(
                    {
                        "ticket_id": str(message_db_resp.ticket_id),
                        "user_id": str(message_db_resp.user_id),
                        "message": str(message_db_resp.message_text),
                        "created_at": str(message_db_resp.created_at),
                    }
                )
    except Exception:
        ticket_chats[ticket_id].remove(websocket)


@app.post("/auth/register/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")

    if len(user.phone_number) != 10:
        raise HTTPException(status_code=400, detail="Phone Number invalid")

    return crud.create_user(db=db, user=user)


@app.post("/auth/login/", response_model=schemas.User)
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="User is not registered")
    if not bcrypt.checkpw(
        user.password.encode("utf-8"), bytes(str(db_user.hashed_password), "utf-8")
    ):
        raise HTTPException(status_code=400, detail="User credentials invalid")
    return db_user


@app.post("/tickets/create/")
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    teacher_id = crud.get_user_with_min_open_tickets(db)
    if teacher_id:
        return crud.create_ticket(db, ticket.user_id, teacher_id)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No teacher found to open ticket with",
    )


@app.patch("/tickets/close/{ticket_id}")
def close_ticket(ticket_id: int, db: Session = Depends(get_db)):
    # Remove the ticket_id from ticket_chats as well
    del ticket_chats[ticket_id]
    return crud.close_ticket(db, ticket_id)


@app.get(
    "/tickets/messages/{ticket_id}", response_model=list[schemas.TicketChatMessage]
)
def get_ticket_messages(ticket_id: int, db: Session = Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="TicketID invalid"
        )

    return crud.get_ticket_messages(db, ticket_id)


@app.get("/tickets/", response_model=list[schemas.Ticket])
def read_open_tickets(db: Session = Depends(get_db)):
    return crud.get_open_tickets(db)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users
