import telebot
import random
import json
import os
from telebot import types

token = "811111113:AAAAAAAAAAAAAAAAAA"
bot = telebot.TeleBot(token)
BALANCES_FILE = 'balances.json'
BETS_FILE = 'bets.json'
MIN_BET = 10
ADMIN_ID = '11111111111111'  # Ваш реальный ID

# Вероятности выигрыша
WIN_PROBABILITIES = {
    'user': {'jackpot': 1, 'pair': 15},
    'admin': {'jackpot': 5, 'pair': 30}
}

# Коэффициенты выигрыша
WIN_COEFFICIENTS = {
    'jackpot': 30,
    'pair': 3,
    'lose': 0
}

def load_data(filename, default={}):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return default

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

user_balances = load_data(BALANCES_FILE)
user_bets = load_data(BETS_FILE)

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("👥 Список пользователей"))
    markup.add(types.KeyboardButton("➕ Пополнить баланс"))
    markup.add(types.KeyboardButton("📊 Статистика"))
    markup.add(types.KeyboardButton("🎰 Крутить"))
    markup.add(types.KeyboardButton("💰 Баланс"))
    markup.add(types.KeyboardButton("🚪 Выйти из админки"))  # Новая кнопка
    return markup

def user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🎰 Крутить"), types.KeyboardButton("💰 Баланс"))
    markup.add(types.KeyboardButton("✏️ Изменить ставку"), types.KeyboardButton("ℹ️ Правила"))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = str(message.from_user.id)
    if user_id not in user_balances:
        user_balances[user_id] = 100
        save_data(BALANCES_FILE, user_balances)
    
    if user_id not in user_bets:
        user_bets[user_id] = MIN_BET
        save_data(BETS_FILE, user_bets)
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 Добро пожаловать в админ-панель!", reply_markup=admin_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            f'🎰 Добро пожаловать в казино-бот!\n'
            f'💰 Ваш баланс: {user_balances[user_id]} очков\n'
            f'💵 Текущая ставка: {user_bets[user_id]} очков\n\n'
            f'Нажмите "🎰 Крутить" для игры с текущей ставкой\n'
            f'Или "✏️ Изменить ставку" для изменения ставки',
            reply_markup=user_keyboard()
        )

# Выход из админ-панели
@bot.message_handler(func=lambda message: message.text == "🚪 Выйти из админки" and str(message.from_user.id) == ADMIN_ID)
def exit_admin(message):
    user_id = str(message.from_user.id)
    bot.send_message(message.chat.id, "Вы вышли из админ-панели", reply_markup=user_keyboard())

# Функция для определения результата вращения
def determine_win_result(user_id):
    is_admin = str(user_id) == ADMIN_ID
    prob = WIN_PROBABILITIES['admin'] if is_admin else WIN_PROBABILITIES['user']
    
    rand = random.randint(1, 100)
    
    if rand <= prob['jackpot']:
        return 'jackpot'
    elif rand <= prob['jackpot'] + prob['pair']:
        return 'pair'
    else:
        return 'lose'

# Обработчик кнопки "🎰 Крутить"
@bot.message_handler(func=lambda message: message.text == "🎰 Крутить")
def spin(message):
    user_id = str(message.from_user.id)
    current_bet = user_bets.get(user_id, MIN_BET)
    balance = user_balances.get(user_id, 0)
    
    if balance < current_bet:
        bot.send_message(message.chat.id, 
                        f"❌ Недостаточно средств! Ваш баланс: {balance}\n"
                        f"Текущая ставка: {current_bet}",
                        reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())
        return
    
    # Вычитаем ставку
    user_balances[user_id] -= current_bet
    save_data(BALANCES_FILE, user_balances)
    
    # Определяем результат
    win_type = determine_win_result(user_id)
    
    # Генерируем числа
    if win_type == 'jackpot':
        num = random.randint(1, 7)
        nums = [num, num, num]
    elif win_type == 'pair':
        num1 = random.randint(1, 7)
        num2 = random.choice([x for x in range(1, 8) if x != num1])
        nums = [num1, num1, num2]
    else:
        nums = random.sample(range(1, 8), 3)
    
    # Вычисляем выигрыш
    win_amount = current_bet * WIN_COEFFICIENTS[win_type]
    user_balances[user_id] += win_amount
    save_data(BALANCES_FILE, user_balances)
    
    # Формируем сообщение
    result_msg = f"🎰 Результат: {' '.join(map(str, nums))}\n"
    result_msg += f"💵 Ставка: {current_bet}\n"
    
    if win_type == 'jackpot':
        result_msg += f"🔥 ДЖЕКПОТ! Выигрыш: {win_amount} (x{WIN_COEFFICIENTS['jackpot']})"
    elif win_type == 'pair':
        result_msg += f"🎉 Пара! Выигрыш: {win_amount} (x{WIN_COEFFICIENTS['pair']})"
    else:
        result_msg += "😢 Вы проиграли"
    
    result_msg += f"\n💰 Новый баланс: {user_balances[user_id]}"
    bot.send_message(message.chat.id, result_msg, 
                    reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())

# Обработчик кнопки "✏️ Изменить ставку"
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить ставку")
def change_bet(message):
    user_id = str(message.from_user.id)
    msg = bot.send_message(message.chat.id, 
                          f"💰 Ваш баланс: {user_balances.get(user_id, 0)}\n"
                          f"💵 Текущая ставка: {user_bets.get(user_id, MIN_BET)}\n"
                          f"Введите новую ставку (мин. {MIN_BET}):",
                          reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_bet_change)

def process_bet_change(message):
    try:
        user_id = str(message.from_user.id)
        new_bet = int(message.text)
        
        if new_bet < MIN_BET:
            bot.send_message(message.chat.id, f"❌ Минимальная ставка: {MIN_BET}!",
                            reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())
            return
            
        if user_balances.get(user_id, 0) < new_bet:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для такой ставки!",
                            reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())
            return
            
        user_bets[user_id] = new_bet
        save_data(BETS_FILE, user_bets)
        
        bot.send_message(message.chat.id, 
                        f"✅ Ставка изменена на {new_bet}",
                        reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число!", 
                         reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())

# Обработчик кнопки "ℹ️ Правила"
@bot.message_handler(func=lambda message: message.text == "ℹ️ Правила")
def show_rules(message):
    rules = """
🎰 Правила игры:
1. Установите ставку (мин. 10)
2. Нажмите "Крутить"
3. Получите результат:
   - 3 одинаковых числа: x30
   - 2 одинаковых числа: x3
   - Все разные: проигрыш

💰 Ваш баланс сохраняется между сессиями
✏️ Вы можете изменить ставку в любой момент
"""
    user_id = str(message.from_user.id)
    bot.send_message(message.chat.id, rules, 
                    reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())

# Обработчик кнопки "💰 Баланс"
@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def show_balance(message):
    user_id = str(message.from_user.id)
    bot.send_message(message.chat.id,
                    f"💰 Ваш баланс: {user_balances.get(user_id, 0)}\n"
                    f"💵 Текущая ставка: {user_bets.get(user_id, MIN_BET)}",
                    reply_markup=admin_keyboard() if user_id == ADMIN_ID else user_keyboard())

# Админ-функции
@bot.message_handler(func=lambda message: message.text == "➕ Пополнить баланс" and str(message.from_user.id) == ADMIN_ID)
def add_balance_start(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя и сумму пополнения через пробел (например: 123456789 100):",
                          reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("Неверный формат")
            
        user_id = parts[0]
        amount = int(parts[1])
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма пополнения должна быть положительной!",
                            reply_markup=admin_keyboard())
            return
            
        if user_id not in user_balances:
            user_balances[user_id] = 0
        
        user_balances[user_id] += amount
        save_data(BALANCES_FILE, user_balances)
        
        bot.send_message(message.chat.id, 
                        f"✅ Баланс пользователя {user_id} пополнен на {amount} очков. Новый баланс: {user_balances[user_id]}",
                        reply_markup=admin_keyboard())
        
        # Пытаемся уведомить пользователя
        try:
            bot.send_message(user_id, f"🎉 Ваш баланс пополнен на {amount} очков!\nНовый баланс: {user_balances[user_id]}")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠ Не удалось уведомить пользователя: {e}",
                            reply_markup=admin_keyboard())
        
    except ValueError as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}\nИспользуйте формат: ID_пользователя Сумма",
                        reply_markup=admin_keyboard())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка: {e}",
                        reply_markup=admin_keyboard())

@bot.message_handler(func=lambda message: message.text == "👥 Список пользователей" and str(message.from_user.id) == ADMIN_ID)
def list_users(message):
    if not user_balances:
        bot.send_message(message.chat.id, "❌ В системе пока нет пользователей",
                        reply_markup=admin_keyboard())
        return
    
    users_list = []
    for user_id, balance in user_balances.items():
        bet = user_bets.get(user_id, MIN_BET)
        users_list.append(f"👤 ID: {user_id}\n💰 Баланс: {balance}\n💵 Ставка: {bet}\n")
    
    response = "📊 Список пользователей:\n\n" + "\n".join(users_list)
    bot.send_message(message.chat.id, response, reply_markup=admin_keyboard())

@bot.message_handler(func=lambda message: message.text == "📊 Статистика" and str(message.from_user.id) == ADMIN_ID)
def show_stats(message):
    total_users = len(user_balances)
    if total_users == 0:
        bot.send_message(message.chat.id, "❌ В системе пока нет пользователей",
                        reply_markup=admin_keyboard())
        return
    
    total_balance = sum(user_balances.values())
    total_bets = sum(user_bets.values())
    avg_balance = total_balance / total_users
    avg_bet = total_bets / total_users
    
    stats_message = (
        "📈 Статистика казино:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"💰 Общий баланс всех пользователей: {total_balance}\n"
        f"💵 Средний баланс: {avg_balance:.2f}\n"
        f"🎰 Средняя ставка: {avg_bet:.2f}\n"
        f"💸 Максимальный баланс: {max(user_balances.values())}\n"
        f"📉 Минимальный баланс: {min(user_balances.values())}"
    )
    
    bot.send_message(message.chat.id, stats_message, reply_markup=admin_keyboard())

bot.infinity_polling()