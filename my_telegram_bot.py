import asyncio
import logging
import random
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, FSInputFile, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


# Токен вашего бота
API_TOKEN = '7038474586:AAH2O_IiqfE9muSnWV0kztjg26bzT0UUlpg'


bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


class Test(StatesGroup):
    # Определение состояний (шагов) для машины состояний
    name = State()
    question = State()


# Вопросы для пользователя
questions = [
    "Мне больше нравятся гуманитарные дисциплины, чем технические.",
    "Мне нравится работа, связанная с общением с людьми.",
    "Я бы предпочел прочитать книжку в свободное время, чем порешать головоломку.",
    "Я бы предпочел больше работать в команде, чем в одиночку.",
    "Я бы предпочел пойти на спектакль вместо музея.",
    "Я хорошо нахожу контакт с другими людьми.",
    "Мне в школе больше нравилось писать сочинения, чем решать задачки.",
    "Для меня лучший отдых это встретиться с друзьями.",
    "Я бы предпочел работу, где требуется больше творческие способности и импровизация, чем внимательность и усидчивость.",
    "Я больше энергичный и активный человек, чем сдержанный и тихий."
]

# Ответы на вопросы, 'а' или 'б', увеличивают соответствующий счетчик
answer_scores = {
    0: ('a', 1),
    1: ('b', 1),
    2: ('a', 1),
    3: ('b', 1),
    4: ('a', 1),
    5: ('b', 1),
    6: ('a', 1),
    7: ('b', 1),
    8: ('a', 1),
    9: ('b', 1)
}

# Возможные профессии в зависимости от результатов
professions = {
    'гуманитарные интроверт': ["переводчик", "архитектор", "художник"],
    'гуманитарные экстраверт': ["психолог", "журналист", "актер"],
    'технические интроверт': ["программист", "инженер", "биоинформатик"],
    'технические экстраверт': ["интернет-маркетолог", "UX-дизайнер", "сетевой администратор"]
}

# Создание кнопок для ответов
reply_keyboard = ['Да', 'Нет']


def make_row_keyboard(items: list[str]):
    # Создание клавиатуры для ответов
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


@dp.message(Command("start"))
async def start_test(msg: Message, state: FSMContext):
    # Начало теста, запрос имени пользователя
    await state.clear()  # Очистка предыдущего состояния
    await state.set_state(Test.name)  # Установка состояния ввода имени

    # Приветственное сообщение с описанием возможностей бота
    greeting_text = (
        "Привет! Я тестовый бот, который поможет тебе узнать больше о себе.\n\n"
        "Я задам тебе несколько вопросов, а на основе твоих ответов определю, "
        "к какой группе ты относишься и предложу подходящие профессии.\n\n"
        "Для начала, как тебя зовут?\n\n"
        "Пожалуйста, введи своё имя текстом."
    )
    await msg.answer(greeting_text)  # Запрос имени


@dp.message(Test.name)
async def enter_name(msg: Message, state: FSMContext):
    # Получение и сохранение имени пользователя
    name = msg.text
    await state.update_data(name=name)
    # Переход к вопросам
    await state.set_state(Test.question)
    await state.update_data(question_idx=0, a_score=0, b_score=0, user_answers=[])
    await msg.answer(questions[0], reply_markup=make_row_keyboard(reply_keyboard))


@dp.message(lambda msg: msg.text.lower() in ['да', 'нет'], Test.question)
async def answer_question(msg: Message, state: FSMContext):
    # Обработка ответов на вопросы теста
    user_data = await state.get_data()
    question_idx = user_data['question_idx']
    answer = msg.text.lower()
    a_score, b_score = user_data.get('a_score', 0), user_data.get('b_score', 0)

    # Логика подсчета очков
    score_type, score_value = answer_scores[question_idx]
    if answer == 'да':
        if score_type == 'a':
            a_score += score_value
        else:
            b_score += score_value

    user_answers = user_data.get('user_answers', [])
    user_answers.append((questions[question_idx], answer))
    await state.update_data(user_answers=user_answers)

    # Переход к следующему вопросу или завершение теста
    if question_idx + 1 < len(questions):
        await state.update_data(question_idx=question_idx + 1, a_score=a_score, b_score=b_score)
        await msg.answer(questions[question_idx + 1], reply_markup=make_row_keyboard(reply_keyboard))
    else:
        # Завершение теста и вывод результатов
        await finish_test(msg, a_score, b_score, user_data['name'], user_answers, state)


@dp.message(Test.question)
async def wrong_input(msg: Message):
    # Обработка некорректного ввода (не "Да" или "Нет")
    await msg.answer("Пожалуйста, выбери 'Да' или 'Нет'.")


async def finish_test(msg: Message, a_score: int, b_score: int, name: str, user_answers: list, state: FSMContext):
    # Формирование и отправка результатов теста
    personality = "интроверт" if b_score < 3 else "экстраверт"
    specialty = "технические" if a_score < 3 else "гуманитарные"
    key = f"{specialty} {personality}"
    profession = random.choice(professions[key])

    # Сохранение ответов и результатов в файл
    filename = f"{name}_answers.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        for question, answer in user_answers:
            file.write(f"{question}: {answer}\n")
        file.write(f"\nРезультат: {profession}")

    # Отправка файла пользователю
    document = FSInputFile(filename)
    await msg.answer("Спасибо за ответы!", reply_markup=ReplyKeyboardRemove())
    await bot.send_document(
        chat_id=msg.chat.id,
        document=document,
        caption=f"{name}, тебе может подойти профессия: {profession}"
    )

    await state.clear()  # Очистка состояния пользователя


async def main():
    # Основная функция для запуска бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    # Настройка логирования и запуск бота
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
