from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
import bcrypt

import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), salt)
    try:
        db_user = models.User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password.decode("utf-8"),
            phone_number=user.phone_number,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def create_community_chat_message(
    db: Session, message: schemas.CommunityChatMessageCreate
):
    try:
        chat_message = models.CommunityChatMessage(
            message_text=message.message_text, user_id=message.user_id
        )

        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)

        user = (
            db.query(models.User)
            .filter(models.User.user_id == chat_message.user_id)
            .one()
        )

        return chat_message, user
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def update_sos_chat_message(db: Session, message_id: int):
    return (
        db.query(models.CommunityChatMessage)
        .filter(models.CommunityChatMessage.message_id == message_id)
        .update({"message_text": "RESOLVED"})
    )


def get_community_chat_messages(db: Session):
    resp = []
    chats = db.query(models.CommunityChatMessage).all()
    for chat in chats:
        user = db.query(models.User).filter(models.User.user_id == chat.user_id).one()

        chat_details = {
            "user": {
                "user_id": str(chat.user_id),
                "name": str(user.name),
            },
            "message_id": str(chat.message_id),
            "message_text": str(chat.message_text),
            "created_at": str(chat.created_at),
        }
        resp.append(chat_details)
    return resp


def get_user_with_min_open_tickets(db: Session):
    result = (
        db.query(
            models.User.user_id,
            func.coalesce(func.count(models.Ticket.ticket_id), 0).label("ticket_count"),
        )
        .outerjoin(
            models.Ticket,
            and_(
                models.User.user_id == models.Ticket.teacher_id,
                models.Ticket.is_open == True,
            ),
        )
        .filter(models.User.is_teacher == True)
        .group_by(models.User.user_id)
        .order_by(func.coalesce(func.count(models.Ticket.ticket_id), 0).asc())
        .first()
    )
    if result:
        return int(result.user_id)
    else:
        return None


def create_ticket(db: Session, ticket: schemas.TicketCreate, teacher_id: int):
    try:
        ticket_model = models.Ticket(
            user_id=ticket.user_id,
            teacher_id=teacher_id,
            is_anonymous=ticket.is_anonymous,
            is_open=True,
        )
        db.add(ticket_model)
        db.commit()
        db.refresh(ticket_model)

        message = schemas.TicketChatMessageCreate(
            message_text=ticket.report_content,
            user_id=ticket.user_id,
            ticket_id=int(str(ticket_model.ticket_id)),
        )

        # Create a message by user with the report
        create_ticket_message(db, message)
        return ticket_model
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def close_ticket(db: Session, ticket_id: int):
    try:
        id = (
            db.query(models.Ticket)
            .filter(models.Ticket.ticket_id == ticket_id)
            .update({"is_open": False})
        )
        db.commit()
        return id
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()


def get_open_user_tickets(db: Session, user_id: int):
    return (
        db.query(models.Ticket)
        .filter(
            models.Ticket.is_open == True,
            (models.Ticket.user_id == user_id) | (models.Ticket.teacher_id == user_id),
        )
        .all()
    )


def get_ticket_messages(db: Session, ticket_id: int):
    return (
        db.query(models.TicketChatMessage)
        .filter(models.TicketChatMessage.ticket_id == ticket_id)
        .all()
    )


def create_ticket_message(db: Session, message: schemas.TicketChatMessageCreate):
    try:
        ticket_message = models.TicketChatMessage(
            ticket_id=message.ticket_id,
            message_text=message.message_text,
            user_id=message.user_id,
        )
        db.add(ticket_message)
        db.commit()
        db.refresh(ticket_message)

        user = (
            db.query(models.User)
            .filter(models.User.user_id == ticket_message.user_id)
            .one()
        )

        return ticket_message, user
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def create_sos(db: Session, sos: schemas.SOSRequest):
    try:
        sos = models.SOS(user_id=sos.user_id, lat=sos.lat, long=sos.long, is_open=True)
        db.add(sos)
        db.commit()
        db.refresh(sos)
        return sos
    except Exception as exc:
        # Handle any other unexpected errors
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


def close_sos(db: Session, user_id: int):
    sos = (
        db.query(models.SOS)
        .filter(models.SOS.user_id == user_id)
        .filter(models.SOS.is_open == True)
        .one_or_none()
    )
    if sos is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No Open SOS Found"
        )
    return (
        db.query(models.SOS)
        .filter(models.SOS.sos_id == sos.sos_id)
        .update({"is_open": False})
    )


def get_sos(db: Session):
    return db.query(models.SOS).filter(models.SOS.is_open == True).all()


def get_all_coords(db: Session):
    soss = db.query(models.SOS).all()
    reports = db.query(models.TicketReport).all()

    coords = []
    for sos in soss:
        coord = {"latitude": float(str(sos.lat)), "longitude": float(str(sos.long))}
        coords.append(coord)

    for report in reports:
        coord = {
            "latitude": float(str(report.lat)),
            "longitude": float(str(report.long)),
        }
        coords.append(coord)

    return coords
