from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

class PoolInvitation(StatesGroup):
    waiting_for_pool_name = State()
    waiting_for_code = State()

# Start command and basic information
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handler for /start command"""
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"ヾ(≧▽≦*)o П-привет, {user_name}-сан! (◕‿◕✿)\n\n"
        f"Я ActivityBot-тян, твоя кавайная помощница в выборе активностей! (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧\n\n"
        f"Представь меня как волшебную коробочку с записками-идеями о том, что можно делать вместе с друзьями! "
        f"Больше никаких споров о том, чем заняться - доверь выбор мне! ✨\n\n"
        f"Для начала тебе нужно:\n"
        f"1️⃣ Создать свой пул активностей с помощью /create_pool\n"
        f"2️⃣ Добавить туда идеи через /add_activity\n"
        f"3️⃣ Пригласить друзей командой /invite\n"
        f"4️⃣ Когда друзья присоединятся, они тоже смогут добавлять свои идеи!\n"
        f"5️⃣ Используй /select для выбора случайной активности\n\n"
        f"❗ Небольшой секрет: когда выбирается чья-то активность, на автора накладывается штраф, "
        f"и в следующий раз его активности будут выпадать реже! Так всем будет интереснее~ (◠‿◠✿)\n\n"
        f"✧*。 Основные команды 。*✧\n"
        f"🌸 /create_pool - Создать новый пул активностей\n"
        f"🌸 /join_pool - Присоединиться к существующему пулу\n"
        f"🌸 /invite - Пригласить друзей (если ты создатель пула)\n"
        f"🌸 /add_activity - Добавить новую активность\n"
        f"🌸 /select - Выбрать случайную активность\n"
        f"🌸 /help - Подробная инструкция по использованию\n\n"
        f"Давай начнем с команды /create_pool и придумаем название для твоего первого пула активностей! (ﾉ´ヮ`)ﾉ*: ･ﾟ"
    )
    
    await message.answer(welcome_text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📚 <b>Справка по командам</b>\n\n"
        "<b>Управление пулами</b>:\n"
        "/create_pool - Создать новый пул активностей\n"
        "/join_pool - Присоединиться к существующему пулу\n"
        "/invite - Пригласить участника в пул\n"
        "/exit_pool - Выйти из пула\n"
        "/my_pools - Показать ваши пулы\n\n"
        "<b>Управление активностями</b>:\n"
        "/add_activity - Добавить активность в пул\n"
        "/select - Выбрать случайную активность\n\n"
        "<b>Информация</b>:\n"
        "/pool_info - Показать информацию о пуле\n"
        "/help - Показать эту справку"
    )
    await message.answer(help_text, parse_mode="HTML")

# Pool creation
@router.message(Command("create_pool"))
async def cmd_create_pool(message: Message, state: FSMContext):
    await message.answer("Введите название нового пула активностей:")
    await state.set_state(PoolCreation.waiting_for_name)

@router.message(PoolCreation.waiting_for_name)
async def process_pool_name(message: Message, state: FSMContext):
    pool_name = message.text.strip()
    
    # Check if name is valid
    if not pool_name:
        await message.answer("Название пула не может быть пустым. Пожалуйста, введите название:")
        return
    
    # Check if pool with this name already exists
    existing_pool = pool_service.get_pool(pool_name)
    if existing_pool:
        await message.answer(f"Пул с названием '{pool_name}' уже существует. Пожалуйста, выберите другое название:")
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
            f"✅ Пул '{pool_name}' успешно создан! Вы являетесь его первым участником и создателем.\n\n"
            f"Теперь вы можете добавлять активности командой /add_activity\n"
            f"Чтобы пригласить других участников, используйте команду /invite\n\n"
            f"Другие пользователи могут присоединиться только по вашему приглашению."
        )
    else:
        await message.answer("❌ Не удалось создать пул. Пожалуйста, попробуйте снова.")
    
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
    
    await message.answer(
        "Чтобы присоединиться к пулу, вам нужен код приглашения от создателя пула.\n"
        "Если у вас есть код, введите его:"
    )
    await state.set_state(PoolInvitation.waiting_for_code)

@router.message(PoolInvitation.waiting_for_code)
async def process_invitation_code(message: Message, state: FSMContext):
    code = message.text.strip()
    
    # Validate invitation code
    pool_name = pool_service.validate_invitation_code(code)
    
    if not pool_name:
        await message.answer("❌ Недействительный код приглашения. Пожалуйста, проверьте код и попробуйте снова.")
        await state.clear()
        return
    
    await process_join_with_code(message, state, pool_name, code)

async def process_join_with_code(message: Message, state: FSMContext, pool_name: str, code: str):
    # Check if pool exists
    pool = pool_service.get_pool(pool_name)
    if not pool:
        await message.answer(f"❌ Пул с названием '{pool_name}' не найден. Проверьте код приглашения и попробуйте снова.")
        await state.clear()
        return
    
    # Check if user is already a participant
    for participant in pool.participants:
        if participant.user_id == message.from_user.id:
            await message.answer(f"Вы уже являетесь участником пула '{pool_name}'.")
            await state.clear()
            return
    
    # Add user to the pool
    new_participant = Participant(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name
    )
    
    success = pool_service.add_participant(pool_name, new_participant)
    
    if success:
        await message.answer(f"✅ Вы успешно присоединились к пулу '{pool_name}'!")
        
        # Remove the used invitation code
        if hasattr(pool, 'invites') and code in pool.invites:
            storage = pool_service._get_storage()
            del storage.pools[pool_name].invites[code]
            pool_service._save_storage(storage)
    else:
        await message.answer("❌ Не удалось присоединиться к пулу. Пожалуйста, попробуйте снова.")
    
    await state.clear()

@router.message(PoolParticipant.waiting_for_pool_name)
async def process_join_pool(message: Message, state: FSMContext):
    pool_name = message.text.strip()
    
    # Check if pool exists
    pool = pool_service.get_pool(pool_name)
    if not pool:
        await message.answer(f"❌ Пул с названием '{pool_name}' не найден. Проверьте название и попробуйте снова.")
        await state.clear()
        return
    
    # Check if user is already a participant
    for participant in pool.participants:
        if participant.user_id == message.from_user.id:
            await message.answer(f"Вы уже являетесь участником пула '{pool_name}'.")
            await state.clear()
            return
    
    # Check if user is authorized to join (must be the creator or use invite code)
    if not pool_service.is_user_authorized_for_pool(pool_name, message.from_user.id):
        await message.answer(
            f"❌ Для присоединения к пулу '{pool_name}' требуется код приглашения от создателя пула.\n"
            f"Используйте команду /join_pool с кодом приглашения."
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
        await message.answer(f"✅ Вы успешно присоединились к пулу '{pool_name}'!")
    else:
        await message.answer("❌ Не удалось присоединиться к пулу. Пожалуйста, попробуйте снова.")
    
    await state.clear()

# Exit a pool
@router.message(Command("exit_pool"))
async def cmd_exit_pool(message: Message, state: FSMContext):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return
    
    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(user_pools)])
    
    await message.answer(f"Выберите пул, из которого хотите выйти (введите номер):\n{pool_list}")
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
                await message.answer(f"✅ Вы успешно вышли из пула '{selected_pool.name}'.")
            else:
                await message.answer("❌ Не удалось выйти из пула. Пожалуйста, попробуйте снова.")
        else:
            await message.answer("❌ Некорректный номер пула. Пожалуйста, выберите номер из списка.")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер пула из списка.")
    
    await state.clear()

# Show user's pools
@router.message(Command("my_pools"))
async def cmd_my_pools(message: Message):
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
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
    user_pools = pool_service.get_pools_by_participant(message.from_user.id)
    
    if not user_pools:
        await message.answer("Вы не являетесь участником ни одного пула.")
        return
    
    # Filter pools where user is the creator
    creator_pools = [pool for pool in user_pools if pool.creator_id == message.from_user.id]
    
    if not creator_pools:
        await message.answer("Вы не являетесь создателем ни одного пула. Только создатель пула может приглашать участников.")
        return
    
    pool_list = "\n".join([f"{i+1}. {pool.name}" for i, pool in enumerate(creator_pools)])
    
    await message.answer(f"Выберите пул, в который хотите пригласить участника (введите номер):\n{pool_list}")
    await state.set_state(PoolInvitation.waiting_for_pool_name)
    await state.update_data(creator_pools=creator_pools)

@router.message(F.text.regexp(r"^\d+$"), PoolInvitation.waiting_for_pool_name)
async def process_invite_pool_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    creator_pools = data.get("creator_pools", [])
    
    try:
        index = int(message.text) - 1
        if 0 <= index < len(creator_pools):
            selected_pool = creator_pools[index]
            
            # Generate invitation code
            invitation_code = pool_service.generate_invitation_code(selected_pool.name, message.from_user.id)
            
            if invitation_code:
                await message.answer(
                    f"✅ Код приглашения для пула '{selected_pool.name}':\n\n"
                    f"<code>{invitation_code}</code>\n\n"
                    f"Поделитесь этим кодом с тем, кого хотите пригласить. "
                    f"Они должны использовать команду /join_pool и ввести этот код."
                , parse_mode="HTML")
            else:
                await message.answer("❌ У вас нет прав для приглашения участников в этот пул. Только участники пула могут приглашать других.")
        else:
            await message.answer("❌ Некорректный номер пула. Пожалуйста, выберите номер из списка.")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер пула из списка.")
    
    await state.clear() 