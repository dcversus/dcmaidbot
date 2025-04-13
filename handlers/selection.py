from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models.data import Activity, Pool
from services import pool_service, selection_service

router = Router()

class ActivitySelection(StatesGroup):
    selecting_pools = State()

@router.message(Command("select"))
async def cmd_select(message: Message, state: FSMContext):
    cmd_parts = message.text.split(maxsplit=1)
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула. Сначала создайте или присоединитесь к пулу.")
        return
    
    valid_pools = []
    for pool in user_pools:
        if pool.activities:
            valid_pools.append(pool)
    
    if not valid_pools:
        await message.answer("В ваших пулах нет активностей. Сначала добавьте активности с помощью команды /add_activity.")
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
        f"Выберите пулы, из которых хотите выбрать активность (введите номера через запятую):\n{pool_list}\n\n"
        "Например: 1,3\n"
        "Совет: Вы можете использовать команду /select с номером пула (например: /select 2)"
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
    selection_result = selection_service.select_activity(selected_pools, message.from_user.id)
    
    if not selection_result:
        await message.answer("❌ Не удалось выбрать активность. Возможно, в выбранных пулах нет активностей.")
        await state.clear()
        return
    
    pool_name, activity, _ = selection_result
    
    # Format response
    pool = pool_service.get_pool(pool_name)
    creator_username = "Unknown"
    if pool:
        for participant in pool.participants:
            if participant.user_id == activity.added_by:
                creator_username = participant.username
                break
    
    response = (
        f"🎲 <b>Выбрана активность из пула '{pool_name}'</b>:\n\n"
        f"<b>{activity.content}</b>\n\n"
        f"Добавил: {creator_username}\n"
        f"Выбрано раз: {activity.selection_count}\n"
    )
    
    # Add penalty info if available
    user_penalty = pool.penalties.get(message.from_user.id, 0.0)
    if user_penalty > 0:
        response += f"\nВаш текущий штраф: {user_penalty:.2f}"
    
    await message.answer(response, parse_mode="HTML")
    await state.clear()

@router.message(ActivitySelection.selecting_pools)
async def process_pool_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    valid_pools = data.get("valid_pools", [])
    
    # Parse selection
    try:
        selected_indices = [int(idx.strip()) - 1 for idx in message.text.split(",")]
        
        # Validate indices
        if not all(0 <= idx < len(valid_pools) for idx in selected_indices):
            await message.answer("❌ Некорректные номера пулов. Пожалуйста, выберите из списка.")
            return
        
        await process_direct_selection(message, state, selected_indices)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номера пулов через запятую (например: 1,3)")
        await state.clear()

# Show penalty information
@router.message(Command("penalties"))
async def cmd_penalties(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return
    
    response = "📊 <b>Информация о штрафах</b>:\n\n"
    
    for pool in user_pools:
        response += f"<b>Пул: {pool.name}</b>\n"
        
        if not pool.penalties:
            response += "Нет активных штрафов\n\n"
            continue
        
        for user_id, penalty in pool.penalties.items():
            if penalty > 0:
                # Find username
                username = "Unknown"
                for participant in pool.participants:
                    if participant.user_id == user_id:
                        username = participant.username
                        break
                
                response += f"{username}: {penalty:.2f}\n"
        
        response += "\n"
    
    await message.answer(response, parse_mode="HTML") 