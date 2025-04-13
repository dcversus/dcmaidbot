from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models.data import Participant, Pool
from services import pool_service

router = Router()

class PoolCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_participants = State()

class PoolParticipant(StatesGroup):
    waiting_for_pool_name = State()
    waiting_for_pool_to_invite = State()

class PoolInvitation(StatesGroup):
    waiting_for_pool_name = State()
    waiting_for_code = State()

# Pool creation
@router.message(Command("create_pool"))
async def cmd_create_pool(message: Message, state: FSMContext):
    await message.answer("Введите название нового пула активностей:", parse_mode="HTML")
    await state.set_state(PoolCreation.waiting_for_name)

@router.message(PoolCreation.waiting_for_name)
async def process_pool_name(message: Message, state: FSMContext):
    pool_name = message.text.strip()
    
    # Check if name is valid
    if not pool_name:
        await message.answer("Название пула не может быть пустым. Пожалуйста, введите название:", parse_mode="HTML")
        return
    
    # Check if pool with this name already exists
    existing_pool = pool_service.get_pool(pool_name)
    if existing_pool:
        await message.answer(f"Пул с названием '<b>{pool_name}</b>' уже существует. Пожалуйста, выберите другое название:", parse_mode="HTML")
        return
    
    # Save pool name
    await state.update_data(pool_name=pool_name)
    
    # Create participant object for the creator
    creator = Participant(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name
    )
    
    # Create pool with creator as first participant
    new_pool = pool_service.create_pool(pool_name, [creator])
    
    if new_pool:
        await message.answer(
            f"✅ Пул '<b>{pool_name}</b>' успешно создан! Вы являетесь его первым участником и создателем.\n\n"
            f"Теперь вы можете добавлять активности командой /add_activity\n"
            f"Чтобы пригласить других участников, используйте команду /invite\n\n"
            f"Другие пользователи могут присоединиться только по вашему приглашению.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Не удалось создать пул. Пожалуйста, попробуйте снова.", parse_mode="HTML")
    
    # End the conversation
    await state.clear()

# Join a pool
@router.message(Command("join_pool"))
async def cmd_join_pool(message: Message, state: FSMContext):
    cmd_parts = message.text.split(maxsplit=1)
    
    if len(cmd_parts) > 1:
        # Check if an invitation code was provided
        code = cmd_parts[1].strip()
        pool_name = pool_service.validate_invitation_code(code)
        
        if pool_name:
            # Proceed with joining using the code
            await process_join_with_code(message, state, pool_name, code)
            return
        else:
            await message.answer("❌ Недействительный код приглашения. Пожалуйста, введите корректный код:", parse_mode="HTML")
            await state.set_state(PoolInvitation.waiting_for_code)
            return
    
    await message.answer(
        "Чтобы присоединиться к пулу, вам нужен код приглашения от создателя пула.\n"
        "Если у вас есть код, введите его:",
        parse_mode="HTML"
    )
    await state.set_state(PoolInvitation.waiting_for_code)

@router.message(PoolInvitation.waiting_for_code)
async def process_invitation_code(message: Message, state: FSMContext):
    code = message.text.strip()
    
    # Validate invitation code
    pool_name = pool_service.validate_invitation_code(code)
    
    if not pool_name:
        await message.answer("❌ Недействительный код приглашения. Пожалуйста, проверьте код и попробуйте снова.", parse_mode="HTML")
        return  # Keep the state to allow retrying
    
    await process_join_with_code(message, state, pool_name, code)

async def process_join_with_code(message: Message, state: FSMContext, pool_name: str, code: str):
    # Check if pool exists
    pool = pool_service.get_pool(pool_name)
    if not pool:
        await message.answer(f"❌ Пул с названием '<b>{pool_name}</b>' не найден. Проверьте код приглашения и попробуйте снова.", parse_mode="HTML")
        await state.clear()
        return
    
    # Check if user is already a participant
    for participant in pool.participants:
        if participant.user_id == message.from_user.id:
            await message.answer(f"Вы уже являетесь участником пула '<b>{pool_name}</b>'.", parse_mode="HTML")
            await state.clear()
            return
    
    # Add user to the pool
    new_participant = Participant(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name
    )
    
    success = pool_service.add_participant(pool_name, new_participant)
    
    if success:
        await message.answer(f"✅ Вы успешно присоединились к пулу '<b>{pool_name}</b>'!", parse_mode="HTML")
        
        # Remove the used invitation code
        try:
            storage = pool_service._get_storage()
            if pool_name in storage.pools and hasattr(storage.pools[pool_name], 'invites'):
                # Clean the code input to ensure it matches
                clean_code = code.strip()
                if clean_code in storage.pools[pool_name].invites:
                    del storage.pools[pool_name].invites[clean_code]
                    pool_service._save_storage(storage)
        except Exception:
            # If code removal fails, it's not critical - log it but continue
            pass
    else:
        await message.answer("❌ Не удалось присоединиться к пулу. Пожалуйста, попробуйте снова.", parse_mode="HTML")
    
    await state.clear()

@router.message(PoolParticipant.waiting_for_pool_name)
async def process_join_pool(message: Message, state: FSMContext):
    pool_name = message.text.strip()
    
    # Check if pool exists
    pool = pool_service.get_pool(pool_name)
    if not pool:
        await message.answer(f"❌ Пул с названием '<b>{pool_name}</b>' не найден. Проверьте название и попробуйте снова.", parse_mode="HTML")
        await state.clear()
        return
    
    # Check if user is already a participant
    for participant in pool.participants:
        if participant.user_id == message.from_user.id:
            await message.answer(f"Вы уже являетесь участником пула '<b>{pool_name}</b>'.", parse_mode="HTML")
            await state.clear()
            return
    
    # Check if user is authorized to join (must be the creator or use invite code)
    if not pool_service.is_user_authorized_for_pool(pool_name, message.from_user.id):
        await message.answer(
            f"❌ Для присоединения к пулу '<b>{pool_name}</b>' требуется код приглашения от создателя пула.\n"
            f"Используйте команду /join_pool с кодом приглашения.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Add user to the pool
    new_participant = Participant(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name
    )
    
    success = pool_service.add_participant(pool_name, new_participant)
    
    if success:
        await message.answer(f"✅ Вы успешно присоединились к пулу '<b>{pool_name}</b>'!", parse_mode="HTML")
    else:
        await message.answer("❌ Не удалось присоединиться к пулу. Пожалуйста, попробуйте снова.", parse_mode="HTML")
    
    await state.clear()

# Exit a pool
@router.message(Command("exit_pool"))
async def cmd_exit_pool(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.", parse_mode="HTML")
        return
    
    pool_list = "\n".join([f"{i+1}. <b>{pool.name}</b>" for i, pool in enumerate(user_pools)])
    
    await message.answer(f"Выберите пул, из которого хотите выйти (введите номер):\n{pool_list}", parse_mode="HTML")
    await state.set_state(PoolParticipant.waiting_for_pool_name)
    await state.update_data(user_pools=user_pools)

@router.message(F.text.regexp(r"^\d+$"), PoolParticipant.waiting_for_pool_name)
async def process_exit_pool(message: Message, state: FSMContext):
    data = await state.get_data()
    user_pools = data.get("user_pools", [])
    
    try:
        index = int(message.text) - 1
        if 0 <= index < len(user_pools):
            selected_pool = user_pools[index]
            
            success = pool_service.remove_participant(selected_pool.name, message.from_user.id)
            
            if success:
                await message.answer(f"✅ Вы успешно вышли из пула '<b>{selected_pool.name}</b>'.", parse_mode="HTML")
            else:
                await message.answer("❌ Не удалось выйти из пула. Пожалуйста, попробуйте снова.", parse_mode="HTML")
        else:
            await message.answer("❌ Некорректный номер пула. Пожалуйста, выберите номер из списка.", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер пула из списка.", parse_mode="HTML")
    
    await state.clear()

# Show user's pools
@router.message(Command("my_pools"))
async def cmd_my_pools(message: Message):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.", parse_mode="HTML")
        return
    
    response = "📋 <b>Ваши пулы</b>:\n\n"
    
    for i, pool in enumerate(user_pools):
        activities_count = len(pool.activities)
        participants_count = len(pool.participants)
        
        response += (
            f"{i+1}. <b>{pool.name}</b>\n"
            f"   Активностей: {activities_count}\n"
            f"   Участников: {participants_count}\n\n"
        )
    
    response += "Используйте /pool_info [название пула] для просмотра подробной информации."
    
    await message.answer(response, parse_mode="HTML")

# Invite to pool
@router.message(Command("invite"))
async def cmd_invite(message: Message, state: FSMContext):
    """Handle /invite command - allow pool creators to invite others to their pools"""
    user_id = message.from_user.id
    
    # Get pools where user is the creator
    user_pools = pool_service.get_pools_by_creator(user_id)
    
    if not user_pools:
        await message.answer("У вас нет созданных пулов. Создайте пул с помощью команды /create_pool", parse_mode="HTML")
        return
    
    # Create pool selection keyboard
    kb = []
    for pool in user_pools:
        kb.append([KeyboardButton(text=pool.name)])
    kb.append([KeyboardButton(text="Отмена")])
    
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Выберите пул, в который хотите пригласить участника:", reply_markup=markup, parse_mode="HTML")
    await state.set_state(PoolParticipant.waiting_for_pool_to_invite)

@router.message(PoolParticipant.waiting_for_pool_to_invite)
async def process_invite_pool_selection(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        return

    user_id = message.from_user.id
    pool_name = message.text
    
    # Get the pool by name and creator ID
    pool = pool_service.get_pool_by_name_and_creator(pool_name, user_id)
    
    if not pool:
        await message.answer("Пул не найден или вы не являетесь его создателем. Пожалуйста, попробуйте снова.", 
                            reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await state.clear()
        return
        
    # Generate invitation code
    try:
        invitation_code = pool_service.generate_invitation_code(user_id, pool.name)
        # Use HTML instead of Markdown for more reliable formatting
        await message.answer(
            f"Код приглашения для пула '<b>{pool.name}</b>':\n\n"
            f"<code>{invitation_code}</code>\n\n"
            f"Поделитесь этим кодом с человеком, которого хотите пригласить. "
            f"Они могут присоединиться с помощью команды /join_pool:\n\n"
            f"<code>/join_pool {invitation_code}</code>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await message.answer(f"Ошибка при генерации кода приглашения: {str(e)}", 
                            reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    
    await state.clear() 