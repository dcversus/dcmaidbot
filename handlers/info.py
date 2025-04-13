from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services import pool_service, activity_service, selection_service

router = Router()

class PoolInfo(StatesGroup):
    waiting_for_pool_name = State()

@router.message(Command("pool_info"))
async def cmd_pool_info(message: Message, state: FSMContext):
    cmd_parts = message.text.split(maxsplit=1)
    
    if len(cmd_parts) > 1:
        # Pool name provided in command
        pool_name = cmd_parts[1].strip()
        await show_pool_info(message, pool_name)
    else:
        # Ask for pool name
        user_pools = pool_service.get_pools_by_participant(message.from_user.id)
        
        if not user_pools:
            await message.answer("Вы не являетесь участником ни одного пула.")
            return
        
        pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])
        
        await message.answer(f"Выберите пул (введите номер):\n{pool_list}")
        await state.set_state(PoolInfo.waiting_for_pool_name)
        await state.update_data(user_pools=user_pools)

@router.message(PoolInfo.waiting_for_pool_name)
async def process_pool_name(message: Message, state: FSMContext):
    data = await state.get_data()
    user_pools = data.get("user_pools", [])
    
    try:
        # Try to interpret as index
        if message.text.isdigit():
            index = int(message.text) - 1
            if 0 <= index < len(user_pools):
                pool_name = user_pools[index].name
                await show_pool_info(message, pool_name)
                await state.clear()
                return
        
        # Try to interpret as pool name
        pool_name = message.text.strip()
        pool = pool_service.get_pool(pool_name)
        
        if pool and any(p.user_id == message.from_user.id for p in pool.participants):
            await show_pool_info(message, pool_name)
        else:
            await message.answer("❌ Пул не найден или вы не являетесь его участником. Пожалуйста, попробуйте снова.")
    
    except (ValueError, IndexError):
        await message.answer("❌ Некорректный ввод. Пожалуйста, введите номер пула из списка или его название.")
    
    await state.clear()

async def show_pool_info(message: Message, pool_name: str):
    """Show detailed information about a pool"""
    pool = pool_service.get_pool(pool_name)
    
    if not pool:
        await message.answer(f"❌ Пул с названием '{pool_name}' не найден.")
        return
    
    # Check if user is a participant
    if not any(p.user_id == message.from_user.id for p in pool.participants):
        await message.answer(f"❌ Вы не являетесь участником пула '{pool_name}'.")
        return
    
    # Prepare pool info
    activities_count = len(pool.activities)
    participants_count = len(pool.participants)
    
    # Find creator name
    creator_name = "Неизвестно"
    for participant in pool.participants:
        if participant.user_id == pool.creator_id:
            creator_name = participant.username
            break
    
    # Get participant names
    participant_list = []
    for participant in pool.participants:
        user_penalty = pool.penalties.get(participant.user_id, 0.0)
        penalty_info = f" (штраф: {user_penalty:.2f})" if user_penalty > 0 else ""
        creator_mark = " 👑" if participant.user_id == pool.creator_id else ""
        participant_list.append(f"- {participant.username}{penalty_info}{creator_mark}")
    
    participants_text = "\n".join(participant_list)
    
    # Get activities info
    activities = activity_service.get_activities(pool_name)
    
    activities_info = ""
    if activities:
        top_activities = sorted(activities, key=lambda a: a.selection_count, reverse=True)[:5]
        
        if top_activities:
            activities_info = "\n\n<b>Самые популярные активности</b>:\n"
            for i, activity in enumerate(top_activities):
                activities_info += f"{i+1}. {activity.content} (выбрано: {activity.selection_count})\n"
    
    # Prepare response
    response = (
        f"📊 <b>Информация о пуле '{pool_name}'</b>\n\n"
        f"<b>Создатель</b>: {creator_name}\n"
        f"<b>Активностей</b>: {activities_count}\n"
        f"<b>Участников</b>: {participants_count}\n\n"
        f"<b>Участники</b>:\n{participants_text}"
        f"{activities_info}"
    )
    
    await message.answer(response, parse_mode="HTML")
