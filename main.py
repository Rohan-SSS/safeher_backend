from typing import Dict, Set
import uvicorn
import bcrypt
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    Depends,
    status,
)
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, crud, chatBot, mapMarkers

from schemas import *

from database import SessionLocal, engine
import utils

models.Base.metadata.create_all(bind=engine)

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": True})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


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
    # Check if user exists
    user = crud.get_user(db, user_id)
    if not user:
        return

    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            chat_message, user = crud.create_community_chat_message(
                db=db,
                message=schemas.CommunityChatMessageCreate(
                    message_text=message, user_id=user_id
                ),
            )

            for client in clients:
                await client.send_json(
                    {
                        "user": {
                            "user_id": str(chat_message.user_id),
                            "name": str(user.name),
                        },
                        "message_id": str(chat_message.message_id),
                        "message_text": str(chat_message.message_text),
                        "created_at": str(chat_message.created_at),
                    }
                )

    except Exception:
        clients.remove(websocket)


ticket_chats: Dict[int, Set[WebSocket]] = {}


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
    ticket_chats.setdefault(ticket_id, set()).add(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            ticket_message, user = crud.create_ticket_message(
                db=db,
                message=schemas.TicketChatMessageCreate(
                    ticket_id=ticket_id, message_text=message, user_id=user_id
                ),
            )
            for client in ticket_chats[ticket_id]:
                await client.send_json(
                    {
                        "user": {
                            "user_id": str(ticket_message.user_id),
                            "name": str(user.name),
                        },
                        "message_id": str(ticket_message.message_id),
                        "message_text": str(ticket_message.message_text),
                        "created_at": str(ticket_message.created_at),
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

    # check if password matches
    if not bcrypt.checkpw(
        user.password.encode("utf-8"), str(db_user.hashed_password).encode("utf-8")
    ):
        raise HTTPException(status_code=400, detail="User credentials invalid")

    return db_user


@app.post("/tickets/create/", response_model=schemas.Ticket)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    teacher_id = crud.get_user_with_min_open_tickets(db)
    if teacher_id:
        return crud.create_ticket(db, ticket, teacher_id)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No teacher found to open ticket with",
    )


@app.patch("/tickets/close/{ticket_id}")
def close_ticket(ticket_id: int, db: Session = Depends(get_db)):
    # Remove the ticket_id from ticket_chats as well
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ticket not found",
        )

    ticket_chats.pop(ticket_id, None)
    return crud.close_ticket(db, ticket_id)


@app.get("/tickets/messages/{ticket_id}")
def get_ticket_messages(ticket_id: int, db: Session = Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="TicketID invalid"
        )

    return crud.get_ticket_messages(db, ticket_id)


@app.get("/tickets/{user_id}")
def read_open_user_tickets(user_id: int, db: Session = Depends(get_db)):
    return crud.get_open_user_tickets(db, user_id)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/community_chat/messages/", response_model=List[schemas.ChatMessageSchema])
def get_community_chat_messages(db: Session = Depends(get_db)):
    return crud.get_community_chat_messages(db)


@app.post("/chatbot/", response_model=ChatbotResponse)
def chat_with_bot(request: ChatbotRequest):
    response_message = chatBot.get_answer(request.message)
    return {"response": response_message}


@app.post("/sos/create")
async def create_sos(request: schemas.SOSRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=request.user_id)
    try:
        if user:
            name = str(user.name)
            phone_number = str(user.phone_number)
            map_link = f"https://www.google.com/maps/search/?api=1&query={request.lat},{request.long}"

            message = f"""
Urgent! Need Help Now 🆘

Hey everyone,

I'm in a tough spot and need assistance ASAP.

📍 Location: {map_link}

If anyone's nearby, please come to help.

Thanks,
{name}
{phone_number}
    """

            chat_message, _ = crud.create_community_chat_message(
                db,
                message=schemas.CommunityChatMessageCreate(
                    message_text=message, user_id=request.user_id
                ),
            )

            # Send Message to any connected clients to room
            for client in clients:
                await client.send_json(
                    {
                        "user": {
                            "user_id": str(chat_message.user_id),
                            "name": str(user.name),
                        },
                        "message_id": str(chat_message.message_id),
                        "message_text": str(chat_message.message_text),
                        "created_at": str(chat_message.created_at),
                    }
                )

            return crud.create_sos(db, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"some error happened: {exc}")


@app.patch("/sos/close/{user_id}")
def close_sos(user_id: int, db: Session = Depends(get_db)):
    id = crud.close_sos(db, user_id)
    return {"respone": f"success, updated id ${id}"}


@app.get("/sos/")
def get_sos(db: Session = Depends(get_db)):
    return crud.get_sos(db)


@app.get("/areas/", response_model=Markers)
async def get_areas(db: Session = Depends(get_db)):
    coords = crud.get_all_coords(db)
    return {"markers": utils.group_points(coords)}

if __name__ == "__main__":
    try:
        port = os.environ.get("PORT", "5000")
        port = int(port)
    except ValueError:
        port = 5000
    uvicorn.run("main:app", host='0.0.0.0', port=port, log_level="info")
