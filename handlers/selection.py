from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from services import pool_service, selection_service
import logging

router = Router()

class ActivitySelection(StatesGroup):
    selecting_pools = State()

@router.message(Command("select"))
async def cmd_select(message: Message, state: FSMContext):
    cmd_parts = message.text.split(maxsplit=1)
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer(
            "Вы не являетесь участником ни одного пула. "
            "Сначала создайте или присоединитесь к пулу."
        )
        return
    
    valid_pools = []
    for pool in user_pools:
        if pool.activities:
            valid_pools.append(pool)
    
    if not valid_pools:
        await message.answer(
            "В ваших пулах нет активностей. "
            "Сначала добавьте активности с помощью команды /add_activity."
        )
        return
    
    # Check if pool index was provided with command
    if len(cmd_parts) > 1 and cmd_parts[1].isdigit():
        index = int(cmd_parts[1]) - 1
        if 0 <= index < len(valid_pools):
            # If valid index provided, immediately select from that pool
            await state.update_data(valid_pools=valid_pools)
            await process_direct_selection(message, state, [index])
            return
        else:
            await message.answer("❌ Некорректный номер пула.")
            
    # Otherwise show pool selection
    pool_list = ""
    for i, pool in enumerate(valid_pools):
        activities_count = len(pool.activities)
        pool_list += f"{i+1}. {pool.name} ({activities_count} активностей)\n"
    
    await message.answer(
        f"Выберите пулы, из которых хотите выбрать активность "
        f"(введите номера через запятую):\n{pool_list}\n\n"
        "Например: 1,3\n"
        "Совет: Вы можете использовать команду /select с номером пула "
        "(например: /select 2)"
    )
    await state.set_state(ActivitySelection.selecting_pools)
    await state.update_data(valid_pools=valid_pools)

async def process_direct_selection(message: Message, state: FSMContext, indices: list):
    data = await state.get_data()
    valid_pools = data.get("valid_pools", [])
    
    # Get selected pool names
    selected_pools = [valid_pools[idx].name for idx in indices]
    
    if not selected_pools:
        await message.answer("❌ Вы не выбрали ни одного пула.")
        await state.clear()
        return
    
    pool_names = ", ".join(selected_pools)
    await message.answer(f"Выбираю случайную активность из пулов: {pool_names}...")
    
    # Select random activity with penalty logic
    selection_result = selection_service.select_activity(
        selected_pools, message.from_user.id
    )
    
    if not selection_result:
        await message.answer(
            "❌ Не удалось выбрать активность. "
            "Возможно, в выбранных пулах нет активностей."
        )
        await state.clear()
        return
    
    pool_name, activity, _ = selection_result
    
    # Format response
    pool = pool_service.get_pool(pool_name)
    creator_username = "Unknown"
    creator_id = activity.added_by
    
    if pool:
        for participant in pool.participants:
            if participant.user_id == creator_id:
                creator_username = participant.username
                break
    
    response = (
        f"🎲 <b>Выбрана активность из пула '{pool_name}'</b>:\n\n"
        f"<b>{activity.content}</b>\n\n"
        f"Добавил: {creator_username}\n"
        f"Выбрано раз: {activity.selection_count}\n"
    )
    
    # Add penalty info for the activity creator
    creator_penalty = pool.penalties.get(creator_id, 0.0)
    if creator_penalty > 0:
        response += f"\nШтраф автора активности: {creator_penalty:.2f}"
    
    # --- Send text response first ---
    await message.answer(response, parse_mode="HTML")
    # --------------------------------

    # --- Send associated media --- 
    if activity.media and len(activity.media) > 0:
        logging.info(f"Activity has {len(activity.media)} media items. Attempting to send.")
        for media_id in activity.media:
            try:
                # Attempt to send as photo first
                await message.answer_photo(photo=media_id)
                logging.info(f"Sent media (photo): {media_id}")
            except TelegramBadRequest as e:
                # Handle cases where it might not be a photo or file_id is bad
                logging.warning(f"Failed to send media {media_id} as photo: {e}. Maybe it's a document or invalid? Skipping.")
                # Optionally, try sending as document here if needed:
                try:
                    await message.answer_document(document=media_id)
                    logging.info(f"Sent media (document): {media_id}")
                except Exception as doc_e:
                    logging.error(f"Failed to send media {media_id} as document either: {doc_e}")
            except Exception as e:
                # Catch other potential errors
                logging.error(f"Unexpected error sending media {media_id}: {e}")
    # -----------------------------

    await state.clear()

@router.message(ActivitySelection.selecting_pools)
async def process_pool_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    valid_pools = data.get("valid_pools", [])
    
    # Parse selection
    try:
        selected_indices = [
            int(idx.strip()) - 1 for idx in message.text.split(",")
        ]
        
        # Validate indices
        if not all(0 <= idx < len(valid_pools) for idx in selected_indices):
            await message.answer(
                "❌ Некорректные номера пулов. Пожалуйста, выберите из списка."
            )
            return
        
        await process_direct_selection(message, state, selected_indices)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите номера пулов через запятую (например: 1,3)"
        )
        await state.clear()

# Show penalty information
@router.message(Command("penalties"))
async def cmd_penalties(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return
    
    response = "📊 <b>Информация о штрафах</b>:\n\n"
    response += (
        "<i>Штрафы накладываются на создателей активностей, "
        "когда их активности выбираются. "
    )
    response += (
        "Чем выше штраф, тем реже будут выбираться активности "
        "этого пользователя в будущем.</i>\n\n"
    )
    
    for pool in user_pools:
        response += f"<b>Пул: {pool.name}</b>\n"
        
        if not pool.penalties:
            response += "Нет активных штрафов\n\n"
            continue
        
        # Sort penalties by value descending
        sorted_penalties = sorted(
            pool.penalties.items(), key=lambda x: x[1], reverse=True
        )
        
        for user_id, penalty in sorted_penalties:
            if penalty > 0:
                # Find username
                username = "Unknown"
                for participant in pool.participants:
                    if participant.user_id == user_id:
                        username = participant.username
                        break
                
                # Mark the current user
                if user_id == message.from_user.id:
                    username += " (вы)"
                
                response += f"{username}: {penalty:.2f}\n"
        
        response += "\n"
    
    await message.answer(response, parse_mode="HTML") 