import sqlite3

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
from aiogram.types import ReplyKeyboardRemove

from configs.bot_configs import dp, main_menu_message

password = '1234'
conn = sqlite3.connect('interface/database/students_feedback.db')
cursor = conn.cursor()


class SignUpTeacher(StatesGroup):
    password = State()
    name_and_institution = State()


class SignUpStudent(StatesGroup):
    name_and_institution = State()


async def teacher_password_waiting(message: types.Message, state: FSMContext):
    await message.answer("🔐<b>Подтвердите, что вы учитель.</b>\n\n"
                         "Введите пароль:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SignUpTeacher.password)


@dp.message_handler(state=SignUpTeacher.password)
async def handle_teacher_password(message: types.Message, state: FSMContext):
    if message.text == password:
        await sign_up_teacher(message, state)
    else:
        await state.update_data(password=message.text)
        await teacher_password_waiting(message, state)
        await message.answer("❌<b>Неправильный пароль.</b> Попробуйте ещё раз.")


async def sign_up_teacher(message: types.Message, state: FSMContext):
    await message.answer('✅<b>Пароль введён верно.</b>\n\n'
                         '👤Введите вашу <b>Фамилию, Имя и Учебное учреждение</b> через пробел\n'
                         'Пример корректных данных: <b>Иванов Иван МФТИ</b>')
    await state.set_state(SignUpTeacher.name_and_institution)


@dp.message_handler(state=SignUpTeacher.name_and_institution)
async def teacher_su(message: types.Message, state: FSMContext):
    if len(message.text.split()) != 3:
        await message.answer(
            '❌<b>Фамилия, имя или учебное учреждение введены неверно.</b> Пример корректных данных: <b>Иванов Иван МФТИ</b>')
    else:
        first_name, last_name, educational_institution = message.text.split()
        cursor.execute(
            "INSERT INTO teachers (user_id, first_name, last_name, educational_institution) VALUES (?, ?, ?, ?)",
            (message.chat.id, first_name, last_name, educational_institution))
        conn.commit()
        await main_menu_message(message, f'👋Здравствуйте, {first_name} {last_name},\n Вы успешно зарегистрировались', 1)
        await state.finish()


async def sign_up_student(message: types.Message, state: FSMContext):
    await message.answer('👤Введите вашу <b>Фамилию, Имя, Учебное учреждение и группу</b> через пробел\n'
                         'Пример корректных данных: <b>Иванов Иван МФТИ 43</b>', reply_markup=ReplyKeyboardRemove())
    await state.set_state(SignUpStudent.name_and_institution)


@dp.message_handler(state=SignUpStudent.name_and_institution)
async def student_su(message: types.Message, state: FSMContext):
    if len(message.text.split()) != 4:
        await message.answer(
            '❌<b>Фамилия, имя, учебное учреждение или группа введены неверно.</b> Пример корректных данных: <b>Иванов Иван МФТИ 43</b>')
    else:
        first_name, last_name, educational_institution, group_name = message.text.split()
        cursor.execute(
            "INSERT INTO students (user_id, first_name, last_name, educational_institution, group_name) VALUES (?, ?, ?, ?, ?)",
            (message.chat.id, first_name, last_name, educational_institution, group_name))
        conn.commit()
        await main_menu_message(message, f'👏Здравствуйте, {first_name} {last_name},\n Вы успешно зарегистрировались', 0)
        await state.finish()
