from dataclasses import dataclass
from enum import Enum

from loguru import logger
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import Admin, Base, LateCatcher, User

LATE_CATCHER_ADDED_RESULT = "Пользователь добавлен в дежурные по опозданиям"
LATE_CATCHER_REMOVED_RESULT = "Пользователь удален из дежурных по опозданиям"


class UserRoles(str, Enum):
    REGULAR = "regular"
    LATE_CATCHER = "late_catcher"
    NOT_FOUND = "not_found"
    ADMIN = "admin"


@dataclass(frozen=True)
class UserMessengerIds:
    chat_id: int | None
    vk_id: int | None


def get_user_roles(
    chat_id: int,
    matcher_messenger_tag: int,
    default_role: UserRoles = UserRoles.REGULAR,
) -> set[UserRoles]:
    with get_session() as session:
        try:
            user = (
                session.query(User).filter(matcher_messenger_tag == chat_id).first()
            )  # one_or_none()?
            if not user:
                logger.warning(f"User with {matcher_messenger_tag} {chat_id} not found")
                return {UserRoles.NOT_FOUND}

            roles = set()

            if session.get(Admin, user.id):
                roles.add(UserRoles.ADMIN)

            if session.get(LateCatcher, user.id):
                roles.add(UserRoles.LATE_CATCHER)

            if not roles:
                roles.add(UserRoles.REGULAR)

            return roles

        except (OperationalError, SQLAlchemyError) as e:
            logger.error(f"Database error for user {chat_id}: {e}")
            return {default_role}

        except Exception as e:
            logger.exception(f"Error for user {chat_id}: {e}")
            raise  # Do not hide unexpected errors.


def is_admin(chat_id: int, matcher_messenger_tag) -> bool:
    return UserRoles.ADMIN in get_user_roles(chat_id, matcher_messenger_tag)


def parse_full_name_for_role_action(full_name: str) -> tuple[str, str, str] | str:
    full_name_parts = full_name.split()

    if len(full_name_parts) not in [2, 3]:
        return "Введите ФИО в формате: Иванов Иван Иванович или Иванов Иван"

    surname = full_name_parts[0].lower()
    name = full_name_parts[1].lower()
    by_father_name = full_name_parts[2].lower() if len(full_name_parts) == 3 else ""

    return surname, name, by_father_name


def add_late_catcher_by_full_name(full_name: str) -> str:
    parsed_full_name = parse_full_name_for_role_action(full_name)

    if isinstance(parsed_full_name, str):
        return parsed_full_name

    surname, name, by_father_name = parsed_full_name

    with get_session() as session:
        user = (
            session.query(User)
            .filter(
                User.surname == surname,
                User.name == name,
                User.by_father_name == by_father_name,
            )
            .one_or_none()
        )

        if not user:
            return "Пользователь с таким ФИО не найден"

        existing_late_catcher = session.get(LateCatcher, user.id)
        if existing_late_catcher:
            return "Этот пользователь уже есть в дежурных по опозданиям"

        late_catcher = LateCatcher()
        late_catcher.id = user.id
        session.add(late_catcher)
        session.commit()

    return LATE_CATCHER_ADDED_RESULT


def get_user_messenger_ids_by_full_name(full_name: str) -> UserMessengerIds | None:
    parsed_full_name = parse_full_name_for_role_action(full_name)

    if isinstance(parsed_full_name, str):
        return None

    surname, name, by_father_name = parsed_full_name

    with get_session() as session:
        user = (
            session.query(User)
            .filter(
                User.surname == surname,
                User.name == name,
                User.by_father_name == by_father_name,
            )
            .one_or_none()
        )

        if not user:
            return None

        return UserMessengerIds(chat_id=user.chat_id, vk_id=user.vk_id)


def get_late_catchers_list() -> str:
    with get_session() as session:
        late_catchers = (
            session.query(User)
            .join(LateCatcher, LateCatcher.id == User.id)
            .order_by(User.surname, User.name, User.by_father_name)
            .all()
        )

        if not late_catchers:
            return "Список дежурных по опозданиям пуст"

        return "\n".join(
            f"{user.surname} {user.name} {user.by_father_name}".strip()
            for user in late_catchers
        )


def remove_late_catcher_by_full_name(full_name: str) -> str:
    parsed_full_name = parse_full_name_for_role_action(full_name)

    if isinstance(parsed_full_name, str):
        return parsed_full_name

    surname, name, by_father_name = parsed_full_name

    with get_session() as session:
        user = (
            session.query(User)
            .filter(
                User.surname == surname,
                User.name == name,
                User.by_father_name == by_father_name,
            )
            .one_or_none()
        )

        if not user:
            return "Пользователь с таким ФИО не найден"

        late_catcher = session.get(LateCatcher, user.id)
        if not late_catcher:
            return "Этого пользователя нет в дежурных по опозданиям"

        session.delete(late_catcher)
        session.commit()

    return LATE_CATCHER_REMOVED_RESULT


def add_user_to_certain_db_model(
    model: Base, chat_ids: list[int]
):  # TODO this func should be replaced by secret commands (for late_catchers)
    with get_session() as session:
        for chat_id in chat_ids:
            user = session.query(User).filter(User.chat_id == chat_id).one_or_none()
            if not user:
                logger.warning("User not found")
                continue

                # Check whether the user is already a member.
            existing = session.get(model, user.id)
            if existing:
                logger.info(f"User is already a member of {model}")
                continue  # Already exists; treat it as success.
            # noinspection PyArgumentList
            # Create a new record in the target model.
            new_member = model(
                id=user.id,  # Same id as in users.
            )
            session.add(new_member)
            session.commit()

            logger.info(f"User added to members of {model}")
            continue


def get_user_id_by_messenger_id(
    messenger_id: int,
    messenger_id_tag,
) -> int | None:
    with get_session() as session:
        user = (
            session.query(User).filter(messenger_id_tag == messenger_id).one_or_none()
        )

        if user is None:
            return None

        return user.id
