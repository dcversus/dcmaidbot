import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models.data import Activity
from services import pool_service, activity_service
from datetime import datetime

router = Router()


class ActivityManagement(StatesGroup):
    selecting_pool = State()
    entering_activity_content = State()  # State after pool selection
    selecting_activity_to_remove = State()
    # waiting_for_media = State() # Removed


# Add activity to a pool
@router.message(Command("add_activity"))
async def cmd_add_activity(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)

    if not user_pools:
        await message.answer(
            "Вы не являетесь участником ни одного пула. "
            "Сначала создайте или присоединитесь к пулу."
        )
        return

    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])

    await message.answer(
        f"Выберите пул, в который хотите добавить активность "
        f"(введите номер):\n{pool_list}"
    )
    await state.set_state(ActivityManagement.selecting_pool)
    await state.update_data(user_pools=user_pools, action="add")


@router.message(F.text.regexp(r"^\d+$"), ActivityManagement.selecting_pool)
async def process_pool_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    user_pools = data.get("user_pools", [])
    action = data.get("action")

    try:
        index = int(message.text) - 1
        if 0 <= index < len(user_pools):
            selected_pool = user_pools[index]

            if action == "remove":
                activities = activity_service.get_activities(selected_pool.name)

                if not activities:
                    await message.answer(
                        f"В пуле '{selected_pool.name}' нет активностей для удаления."
                    )
                    await state.clear()
                    return

                await state.update_data(
                    selected_pool=selected_pool.name, activities=activities
                )

                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=activity.content)]
                        for activity in activities
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )

                await message.answer(
                    f"Выберите активность для удаления из пула '{selected_pool.name}':",
                    reply_markup=keyboard,
                )
                await state.set_state(ActivityManagement.selecting_activity_to_remove)

            elif action == "list":
                activities = activity_service.get_activities(selected_pool.name)

                if not activities:
                    await message.answer(
                        f"В пуле '{selected_pool.name}' нет активностей."
                    )
                else:
                    response = (
                        f"📋 <b>Активности в пуле '{selected_pool.name}'</b>:\n\n"
                    )

                    for i, activity in enumerate(activities):
                        creator_username = "Unknown"
                        for participant in selected_pool.participants:
                            if participant.user_id == activity.added_by:
                                creator_username = participant.username
                                break
                        media_info = " 📷" if activity.media else ""
                        response += (
                            f"{i+1}. {activity.content}{media_info}\n"
                            f"   Добавил: {creator_username}\n"
                            f"   Выбрано раз: {activity.selection_count}\n\n"
                        )

                    await message.answer(response, parse_mode="HTML")
                await state.clear()

            else:  # action == "add"
                await state.update_data(selected_pool=selected_pool.name)
                await message.answer(
                    f"Выбран пул: {selected_pool.name}\n\n"
                    "Теперь отправьте текст активности или фото/файл:"
                )
                await state.set_state(ActivityManagement.entering_activity_content)
        else:
            await message.answer(
                "❌ Некорректный номер пула. Пожалуйста, выберите номер из списка."
            )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер пула из списка.")


# Combined handler for text and media activities
@router.message(
    ActivityManagement.entering_activity_content,
    F.content_type.in_({"text", "photo", "document"}),
)
async def process_activity_input(message: Message, state: FSMContext):
    data = await state.get_data()
    pool_name = data.get("selected_pool")

    if not pool_name:
        logging.error("State lost pool_name in entering_activity_content")
        await message.answer(
            "Произошла ошибка состояния. Пожалуйста, начните заново /add_activity"
        )
        await state.clear()
        return

    content = ""
    media_ids = []
    success_message = ""

    if message.text:
        content = message.text.strip()
        if not content:
            await message.answer(
                "Текст активности не может быть пустым. "
                "Пожалуйста, введите текст или отправьте медиа:"
            )
            return  # Remain in the same state
        success_message = (
            f"✅ Текстовая активность успешно добавлена в пул '{pool_name}'!"
        )

    elif message.photo:
        photo = message.photo[-1]  # Get the largest photo
        media_ids.append(photo.file_id)
        # Use caption or default
        content = (
            message.caption.strip()
            if message.caption
            else f"Фото ({photo.file_unique_id})"
        )
        success_message = f"✅ Активность с фото успешно добавлена в пул '{pool_name}'!"

    elif message.document:  # Optional: Handle documents
        document = message.document
        media_ids.append(document.file_id)
        # Use caption or filename
        content = message.caption.strip() if message.caption else document.file_name
        success_message = (
            f"✅ Активность с документом успешно добавлена в пул '{pool_name}'!"
        )

    else:
        # Should not happen due to F.content_type filter, but as a safeguard
        await message.answer("Пожалуйста, отправьте текст, фото или документ.")
        return

    # Create activity object
    new_activity = Activity(
        content=content,
        added_by=message.from_user.id,
        added_at=datetime.now(),
        media=media_ids,  # Will be empty list if only text was sent
    )

    # Add activity to the pool
    success = activity_service.add_activity(pool_name, new_activity)

    if success:
        await message.answer(success_message)
    else:
        await message.answer(
            "❌ Не удалось добавить активность. Пожалуйста, попробуйте снова."
        )

    await state.clear()


@router.message(ActivityManagement.entering_activity_content)
async def invalid_activity_input(message: Message):
    # Catch any other content types not handled above
    await message.answer(
        "Неподдерживаемый тип контента. "
        "Пожалуйста, отправьте текст, фото или документ."
    )


# --- Removing obsolete waiting_for_media handlers ---
# @router.message(ActivityManagement.waiting_for_media, F.text == "Нет, без медиа") ...
# @router.message(
#    ActivityManagement.waiting_for_media,
#    F.text == "Да, добавить изображение"
# ) ...
# @router.message(ActivityManagement.waiting_for_media, F.photo) ...
# @router.message(ActivityManagement.waiting_for_media) ...


# List activities in a pool
@router.message(Command("list_activities"))
async def cmd_list_activities(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)

    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return

    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])

    await message.answer(
        f"Выберите пул, активности которого хотите просмотреть "
        f"(введите номер):\n{pool_list}"
    )
    await state.set_state(ActivityManagement.selecting_pool)
    await state.update_data(user_pools=user_pools, action="list")


# Remove activity from a pool
@router.message(Command("remove_activity"))
async def cmd_remove_activity(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)

    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return

    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])

    await message.answer(
        f"Выберите пул, из которого хотите удалить активность "
        f"(введите номер):\n{pool_list}"
    )
    await state.set_state(ActivityManagement.selecting_pool)
    await state.update_data(user_pools=user_pools, action="remove")


@router.message(ActivityManagement.selecting_activity_to_remove)
async def process_activity_removal(message: Message, state: FSMContext):
    data = await state.get_data()
    activities = data.get("activities", [])
    pool_name = data.get("selected_pool")

    # Find activity by content
    activity_to_remove = next(
        (activity for activity in activities if activity.content == message.text),
        None,
    )

    if activity_to_remove:
        # Remove the activity
        success = activity_service.remove_activity(
            pool_name, activity_to_remove.content
        )

        if success:
            await message.answer(
                f"✅ Активность успешно удалена из пула '{pool_name}'!",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await message.answer(
                "❌ Не удалось удалить активность. Пожалуйста, попробуйте снова."
            )
    else:
        await message.answer(
            "❌ Выбранная активность не найдена. "
            "Пожалуйста, выберите активность из списка."
        )

    await state.clear()
