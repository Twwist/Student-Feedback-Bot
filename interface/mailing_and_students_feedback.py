import sqlite3

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
from aiogram.types import ReplyKeyboardRemove

from configs.bot_configs import bot, main_menu_message, dp
from configs.form_making_configs import questions
import random

from configs.models.checking_for_information.checking_for_information import is_informative
from configs.models.emotionality_emotionality.assessment_emotionality import assessment_emotionality

conn = sqlite3.connect(r'interface/database/students_feedback.db')
cursor = conn.cursor()

temporarily_dict = {}
temporarily_dict_feedback = {}


class Mailing(StatesGroup):
    lecture_name = State()
    group = State()
    form = State()


class Form(StatesGroup):
    questions_count = State()


class Feedback(StatesGroup):
    evaluation = State()
    review = State()


async def random_form_making(message: types.Message):
    questions_count = int(message.text)
    random_form = [random.choice(questions) for _ in range(questions_count)]
    return random_form


@dp.message_handler(state=Mailing.lecture_name)
async def handle_lecture_name(message: types.Message, state: FSMContext):
    if message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Создание анкеты отменено\n"
                                         "Вы в главном меню", 1)
    else:
        cursor.execute("SELECT MAX(lecture_id) FROM lectures")
        row = cursor.fetchone()

        if row[0] is not None:
            latest_lecture_id = int(row[0]) + 1
        else:
            latest_lecture_id = 1

        temporarily_dict[message.from_user.id] = [latest_lecture_id, message.text]
        await message.answer(f"✅Лекция <b>{message.text}</b> зарегистрирована.\n"
                             f"Теперь выберите <b>группу</b>, которой будет отправлена рассылка")
        await state.update_data(lecture_id=latest_lecture_id)
        await state.set_state(Mailing.group)


@dp.message_handler(state=Mailing.group)
async def handle_group(message: types.Message, state: FSMContext):
    if message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Создание анкеты отменено\n"
                                         "Вы в главном меню", 1)
    else:
        form_setting_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["🎲Создать случайную форму", "✍️Создать форму в ручную"]
        form_setting_menu.add(*buttons)
        form_setting_menu.add("🏠Вернуться в главное меню")

        temporarily_dict[message.from_user.id].append(message.text)
        await message.answer(f"📨Рассылка будет отправлена в группе <b>{message.text}</b>.\n"
                             f"Теперь нужно <b>создать форму</b>. Выберите один из вариантов формы",
                             reply_markup=form_setting_menu)
        await state.set_state(Mailing.form)


@dp.message_handler(state=Mailing.form)
async def handle_group(message: types.Message, state: FSMContext):
    back_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_menu.add("🏠Вернуться в главное меню")

    if message.text == "🎲Создать случайную форму":
        await message.answer(f"🔢Сколько вопросов будет в форме? <b>Минимум 1, максимум {len(questions)}</b>",
                             reply_markup=back_menu)
        await state.set_state(Form.questions_count)
    elif message.text == "✍️Создать форму в ручную":
        await manual_form_making()
    elif message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Создание анкеты отменено\n"
                                         "Вы в главном меню", 1)
    else:
        await message.answer("❌<b>Нет такого варианта ответа.</b> Выберите один из предложенных вариантов")


@dp.message_handler(state=Form.questions_count)
async def handle_questions_count(message: types.Message, state: FSMContext):
    if message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Создание анкеты отменено\n"
                                         "Вы в главном меню", 1)
        return
    else:
        try:
            questions_count = int(message.text)
            if questions_count < 1 or questions_count > len(questions):
                raise ValueError
        except ValueError:
            await message.answer("❌<b>Неправильное число вопросов.</b> Попробуйте ещё раз.")
            return

        cursor.execute(f"SELECT user_id, first_name, last_name FROM teachers WHERE user_id = {message.from_user.id}")
        result_t = cursor.fetchone()

        if result_t:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="📤Отправить форму", callback_data="send_form"))
            keyboard.add(types.InlineKeyboardButton(text="Удалить форму и вернуться в главное меню", callback_data="delete_form_and_return_to_main_menu"))

            random_form = await random_form_making(message)
            form = (f'📋<b>Форма от {result_t[1]} {result_t[2]}</b>\n'
                    f'Посвященная лекции: <b>{temporarily_dict[message.from_user.id][1]}</b>\n')
            for i in random_form:
                form += f'🔹{i}\n'

            temporarily_dict[message.from_user.id].append(form)

            await message.answer(form, reply_markup=keyboard)
            await state.finish()
        else:
            await main_menu_message(message, "❌Вы не являетесь преподавателем.", 0)


@dp.callback_query_handler(text="send_form")
async def send_form(call: types.CallbackQuery):
    lecture_id, lecture_name, group_name, form = temporarily_dict[call.from_user.id]
    teacher_id = call.from_user.id
    form = f'ID лекции: {lecture_id}\n' + form

    educational_institution_name = \
        cursor.execute(f"SELECT educational_institution FROM teachers WHERE user_id = {call.from_user.id}").fetchone()[
            0]

    student_list = cursor.execute("SELECT user_id, group_name, educational_institution FROM students").fetchall()

    feedback_menu = types.InlineKeyboardMarkup()
    feedback_menu.add(types.InlineKeyboardButton(text="Оставить отзыв", callback_data="leave_review"))
    for student in student_list:
        if student[2] == educational_institution_name and student[1] == group_name:
            await bot.send_message(student[0], form, reply_markup=feedback_menu, parse_mode="HTML")

    cursor.execute(
        "INSERT INTO lectures (lecture_name, teacher_id, group_name, lecture_form, evaluation_lecture_sum, evaluation_lecture_count, reviews) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (lecture_name, teacher_id, group_name, form, 0, 0, ""))
    conn.commit()

    await main_menu_message(call, "✅Рассылка успешно отправлена.", 1)


@dp.callback_query_handler(text="delete_form_and_return_to_main_menu")
async def delete_form_and_return_to_main_menu(call: types.CallbackQuery):
    await call.message.delete()
    await main_menu_message(call, "Форма не сохранена.\nВы в главном меню", 1)


@dp.callback_query_handler(text='leave_review')
async def leave_review(call: types.CallbackQuery, state: FSMContext):
    back_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_menu.add("🏠Вернуться в главное меню")

    lecture_id = call.message.text.split()[2]
    await call.message.answer("На сколько звёзд от 1 до 10 вы бы оценили данную лекцию?", reply_markup=back_menu)
    await state.set_state(Feedback.evaluation)
    await state.update_data(lecture_id=lecture_id)


@dp.message_handler(state=Feedback.evaluation)
async def handle_evaluation(message: types.Message, state: FSMContext):
    if message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Вы вернулись в главное меню\n"
                                         "Заполнение формы отменено", 1)
    else:
        try:
            evaluation = int(message.text)
            if evaluation < 1 or evaluation > 10:
                raise ValueError
        except ValueError:
            await message.answer("❌Пожалуйста, введите число от 1 до 10")
            return
        temporarily_dict_feedback[message.from_user.id] = [evaluation]

        await message.answer(f"Ваша оценка: {evaluation} принята. Теперь напишите свой отзыв\n\n"
                             f"Можете воспользоваться вопросами из выше отправленной формы")
        await state.set_state(Feedback.review)


@dp.message_handler(state=Feedback.review)
async def handle_review(message: types.Message, state: FSMContext):
    if message.text == "🏠Вернуться в главное меню":
        await state.finish()
        await main_menu_message(message, "Вы вернулись в главное меню\n"
                                         "Заполнение формы отменено", 1)
    else:
        data = await state.get_data()
        lecture_id = data.get('lecture_id')

        if lecture_id is None:
            return

        review, evaluation = message.text, temporarily_dict_feedback[message.from_user.id][0]
        emotionality = await assessment_emotionality(review)

        if is_informative(review):
            cursor.execute(
                "SELECT evaluation_lecture_sum, evaluation_lecture_count, reviews FROM lectures WHERE lecture_id = ?",
                (lecture_id,))

            row = cursor.fetchone()
            if row is not None:
                current_evaluation_sum, current_evaluation_counter, current_review = float(row[0]), int(row[1]), str(row[2])
                new_evaluation = current_evaluation_sum + evaluation
                new_current_evaluation_counter = current_evaluation_counter + 1
                new_review = current_review + emotionality + review + "\n\n"

                cursor.execute(
                    "UPDATE lectures SET evaluation_lecture_sum = ?, evaluation_lecture_count = ?, reviews = ? WHERE lecture_id = ?",
                    (new_evaluation, new_current_evaluation_counter, new_review, lecture_id))
                conn.commit()

                await main_menu_message(message, f"Ваш отзыв: {review} принят. Спасибо.", 0)
                await state.finish()
            else:
                await main_menu_message(message, 'Произошла какая то ошибка', 0)
        else:
            await message.answer('<b>Отзыв недостаточно информативен.</b>\n\n'
                                 'Попытайтесь ввести свой отзыв еще раз.\n\n')
