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

# Start command and basic information
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handler for /start command"""
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"(っ◔◡◔)っ <b>Привет, {user_name}!</b> Вот что я умею~\n\n"
        
        f"<b>🎁 О боте</b>\n"
        f"Я как волшебная коробка с записками-идеями о том, что можно делать вместе с друзьями! "
        f"Создай свой пул активностей, добавь туда интересные идеи и пригласи друзей. "
        f"Каждый может дополнить вашу общую коллекцию своими идеями, а когда захотите чем-то заняться - "
        f"я случайным образом выберу одну из активностей! (つ✧ω✧)つ\n\n"
        
        f"<b>★.:*・°☆ Пошаговая инструкция ☆°・*:.★</b>\n\n"
        
        f"<b>Шаг 1: Создай свой пул активностей</b>\n"
        f"Используй команду /create_pool\n"
        f"Придумай название для своего пула (например, 'Выходные', 'Настолки', 'Фильмы')\n\n"
        
        f"<b>Шаг 2: Добавь активности в пул</b>\n"
        f"Используй команду /add_activity\n"
        f"Выбери свой пул и напиши, чем хотелось бы заняться (например, 'Поход в кино', 'Пикник в парке')\n\n"
        
        f"<b>Шаг 3: Пригласи друзей</b>\n"
        f"Используй команду /invite\n"
        f"Выбери пул, создателем которого ты являешься, и получи код приглашения\n"
        f"Отправь этот код друзьям - только ты как создатель пула можешь приглашать других!\n\n"
        
        f"<b>Шаг 4: Друзья присоединяются к пулу</b>\n"
        f"Твои друзья используют команду /join_pool [код]\n"
        f"Теперь они тоже могут добавлять свои идеи в общий пул!\n\n"
        
        f"<b>Шаг 5: Все вместе пополняете пул активностями</b>\n"
        f"Каждый участник может использовать /add_activity\n"
        f"Чем больше разных идей - тем интереснее!\n\n"
        
        f"<b>Шаг 6: Выбирайте случайную активность</b>\n"
        f"Когда не можете решить, чем заняться - используйте /select\n"
        f"Я выберу случайную активность с учетом истории и справедливости!\n\n"
        
        f"<b>❗ Важно: Система штрафов для справедливости</b>\n"
        f"Когда выбирается чья-то активность, на её автора накладывается небольшой штраф. "
        f"Это значит, что в следующий раз его активности будут выпадать реже. "
        f"Так всем будет интереснее, и активности будут разнообразнее! (◕‿◕✿)\n"
        f"Штрафы постепенно уменьшаются со временем, так что не переживай!\n\n"
        
        f"<b>★.:*・°☆ Все команды ☆°・*:.★</b>\n\n"
        
        f"🌟 <b>/start</b> - Начать работу с ботом и посмотреть краткий гайд\n\n"
        
        f"🌸 <b>/create_pool</b> - Создать новый пул активностей\n"
        f"   Создай свою категорию с активностями! Ты будешь создателем и сможешь приглашать других.\n\n"
        
        f"🌸 <b>/join_pool [код]</b> - Присоединиться к пулу\n"
        f"   Нужен код приглашения от создателя пула.\n\n"
        
        f"🌸 <b>/invite</b> - Пригласить в пул\n"
        f"   Только создатель пула может приглашать участников!\n\n"
        
        f"🌸 <b>/exit_pool</b> - Выйти из пула\n"
        f"   Покинуть пул, если больше не хочешь участвовать.\n\n"
        
        f"🌸 <b>/my_pools</b> - Показать твои пулы\n"
        f"   Список всех пулов, в которых ты участвуешь.\n\n"
        
        f"🍡 <b>/add_activity</b> - Добавить активность\n"
        f"   Добавь новую активность в пул для выбора.\n\n"
        
        f"🍡 <b>/list_activities</b> - Список активностей\n"
        f"   Покажет все активности в выбранном пуле.\n\n"
        
        f"🍡 <b>/select [номер_пула]</b> - Выбрать активность\n"
        f"   Выберет случайную активность с учетом справедливого распределения.\n\n"
        
        f"📝 <b>/pool_info [название_пула]</b> - Информация о пуле\n"
        f"   Подробная информация о пуле, участниках и активностях.\n\n"
        
        f"📝 <b>/penalties</b> - Информация о штрафах\n"
        f"   Покажет текущие штрафы всех участников во всех твоих пулах.\n\n"
        
        f"Напиши /start в любой момент, чтобы вернуться к краткому гайду! (๑˃ᴗ˂)ﻭ"
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
        else:
            await message.answer("❌ Недействительный код приглашения. Пожалуйста, введите корректный код:")
            await state.set_state(PoolInvitation.waiting_for_code)
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
        return  # Keep the state to allow retrying
    
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
    """Handle /invite command - allow pool creators to invite others to their pools"""
    user_id = message.from_user.id
    
    # Get pools where user is the creator
    user_pools = pool_service.get_pools_by_creator(user_id)
    
    if not user_pools:
        await message.answer("You haven't created any pools. Create a pool first with /create_pool")
        return
    
    # Create pool selection keyboard
    kb = []
    for pool in user_pools:
        kb.append([KeyboardButton(text=pool.name)])
    kb.append([KeyboardButton(text="Cancel")])
    
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Select a pool to invite someone to:", reply_markup=markup)
    await state.set_state(PoolParticipant.waiting_for_pool_to_invite)

@router.message(PoolParticipant.waiting_for_pool_to_invite)
async def process_invite_pool_selection(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
        return

    user_id = message.from_user.id
    pool_name = message.text
    
    # Get the pool by name and creator ID
    pool = pool_service.get_pool_by_name_and_creator(pool_name, user_id)
    
    if not pool:
        await message.answer("Pool not found or you are not the creator. Please try again.", 
                            reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
        
    # Generate invitation code
    try:
        invitation_code = pool_service.generate_invitation_code(user_id, pool.name)
        # Use HTML instead of Markdown for more reliable formatting
        await message.answer(
            f"Invitation code for pool '{pool.name}':\n\n"
            f"<code>{invitation_code}</code>\n\n"
            f"Share this code with the person you want to invite. "
            f"They can join using /join_pool command.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await message.answer(f"Error generating invitation code: {str(e)}", 
                            reply_markup=ReplyKeyboardRemove())
    
    await state.clear() 