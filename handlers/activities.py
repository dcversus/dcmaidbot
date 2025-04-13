from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models.data import Activity
from services import pool_service, activity_service
from datetime import datetime

router = Router()

class ActivityManagement(StatesGroup):
    selecting_pool = State()
    entering_activity_content = State()
    selecting_activity_to_remove = State()

# Add activity to a pool
@router.message(Command("add_activity"))
async def cmd_add_activity(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула. Сначала создайте или присоединитесь к пулу.")
        return
    
    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])
    
    await message.answer(f"Выберите пул, в который хотите добавить активность (введите номер):\n{pool_list}")
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
                    await message.answer(f"В пуле '{selected_pool.name}' нет активностей для удаления.")
                    await state.clear()
                    return
                
                # Store activities in state for later use
                await state.update_data(selected_pool=selected_pool.name, activities=activities)
                
                # Create activity list for user to choose from
                activity_list = "\n".join([f"{i+1}. {activity.content}" for i, activity in enumerate(activities)])
                
                await message.answer(
                    f"Выберите активность для удаления из пула '{selected_pool.name}' (введите номер):\n\n{activity_list}"
                )
                await state.set_state(ActivityManagement.selecting_activity_to_remove)
            elif action == "list":
                activities = activity_service.get_activities(selected_pool.name)
                
                if not activities:
                    await message.answer(f"В пуле '{selected_pool.name}' нет активностей.")
                else:
                    response = f"📋 <b>Активности в пуле '{selected_pool.name}'</b>:\n\n"
                    
                    for i, activity in enumerate(activities):
                        # Find username of activity creator
                        creator_username = "Unknown"
                        for participant in selected_pool.participants:
                            if participant.user_id == activity.added_by:
                                creator_username = participant.username
                                break
                        
                        response += (
                            f"{i+1}. {activity.content}\n"
                            f"   Добавил: {creator_username}\n"
                            f"   Выбрано раз: {activity.selection_count}\n\n"
                        )
                    
                    await message.answer(response, parse_mode="HTML")
                await state.clear()
            else:  # action == "add"
                await state.update_data(selected_pool=selected_pool.name)
                await message.answer(
                    f"Выбран пул: {selected_pool.name}\n\n"
                    "Введите текст активности, которую хотите добавить:"
                )
                await state.set_state(ActivityManagement.entering_activity_content)
        else:
            await message.answer("❌ Некорректный номер пула. Пожалуйста, выберите номер из списка.")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер пула из списка.")

@router.message(ActivityManagement.entering_activity_content)
async def process_activity_content(message: Message, state: FSMContext):
    content = message.text.strip()
    
    if not content:
        await message.answer("Текст активности не может быть пустым. Пожалуйста, введите текст:")
        return
    
    data = await state.get_data()
    pool_name = data.get("selected_pool")
    
    # Create activity object
    new_activity = Activity(
        content=content,
        added_by=message.from_user.id,
        added_at=datetime.now()
    )
    
    # Add activity to the pool
    success = activity_service.add_activity(pool_name, new_activity)
    
    if success:
        await message.answer(f"✅ Активность успешно добавлена в пул '{pool_name}'!")
    else:
        await message.answer("❌ Не удалось добавить активность. Пожалуйста, попробуйте снова.")
    
    await state.clear()

# List activities in a pool
@router.message(Command("list_activities"))
async def cmd_list_activities(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return
    
    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])
    
    await message.answer(f"Выберите пул, активности которого хотите просмотреть (введите номер):\n{pool_list}")
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
    
    await message.answer(f"Выберите пул, из которого хотите удалить активность (введите номер):\n{pool_list}")
    await state.set_state(ActivityManagement.selecting_pool)
    await state.update_data(user_pools=user_pools, action="remove")

@router.message(F.text.regexp(r"^\d+$"), ActivityManagement.selecting_activity_to_remove)
async def process_activity_removal(message: Message, state: FSMContext):
    data = await state.get_data()
    activities = data.get("activities", [])
    pool_name = data.get("selected_pool")
    
    try:
        index = int(message.text) - 1
        if 0 <= index < len(activities):
            activity_to_remove = activities[index]
            
            # Remove the activity
            success = activity_service.remove_activity(pool_name, activity_to_remove.content)
            
            if success:
                await message.answer(f"✅ Активность успешно удалена из пула '{pool_name}'!")
            else:
                await message.answer("❌ Не удалось удалить активность. Пожалуйста, попробуйте снова.")
        else:
            await message.answer("❌ Некорректный номер активности. Пожалуйста, выберите номер из списка.")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер активности из списка.")
    
    await state.clear() 