import sqlite3

import numpy
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from numpy import mean

from configs.bot_configs import bot, main_menu_message, dp
from configs.form_making_configs import questions
import random

conn = sqlite3.connect(r'interface/database/students_feedback.db')
cursor = conn.cursor()


async def get_analytics_text(message: (types.Message, types.CallbackQuery)):
    if isinstance(message, types.Message):
        teacher_id = message.from_user.id
    else:
        teacher_id = message.message.chat.id

    cursor.execute(
        f"SELECT lecture_id, lecture_name, group_name, evaluation_lecture_sum, evaluation_lecture_count from lectures WHERE teacher_id = teacher_id")
    result = cursor.fetchall()
    common_evaluation_lecture = []
    lectures_inline_menu_list = []
    for i in result:
        try:
            common_evaluation_lecture.append(i[3] / i[4])
        except ZeroDivisionError:
            common_evaluation_lecture.append('У данной лекции пока нет оценок')
        lectures_inline_menu_list.append(types.InlineKeyboardButton(text=f"Лекция: {i[1]}, Группа: {i[2]}",
                                                                    callback_data=f"ga_{i[0]}_{i[1]}_{i[2]}"))

    mean_common_evaluation_lecture = round(mean(
        [i for i in common_evaluation_lecture if i != 'У данной лекции пока нет оценок']), 2)
    if numpy.isnan(mean_common_evaluation_lecture):
        mean_common_evaluation_lecture = 'У ваших лекций пока нет оценок'

    lectures_menu = types.InlineKeyboardMarkup()
    for inline_button in lectures_inline_menu_list:
        lectures_menu.add(inline_button)

    text, keyboard = f"Средняя оценка ваших лекций: {mean_common_evaluation_lecture}\n\n Чтобы узнать отчёт по конкретной лекции, выберите её из списка ниже", lectures_menu

    return text, keyboard


async def get_analytics(message: types.Message):
    text, keyboard = await get_analytics_text(message)
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(text_contains="ga")
async def get_analytics_by_lecture(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    lecture_id, lecture_name, group_name = data[1], data[2], data[3]

    cursor.execute(
        f"SELECT lectures.evaluation_lecture_sum, evaluation_lecture_count, reviews from lectures WHERE lecture_id = {lecture_id}")
    result = cursor.fetchone()

    try:
        mean_common_evaluation_lecture = round(result[0] / result[1], 2)
    except ZeroDivisionError:
        mean_common_evaluation_lecture = 'У данной лекции пока нет оценок'

    rewiews = result[2]

    if len(rewiews.split('\n\n')) < 5:
        last_reviews = len(rewiews.split('\n\n')) - 1
    else:
        last_reviews = 5

    back_menu = types.InlineKeyboardMarkup()
    back_menu.add(types.InlineKeyboardButton(text="Назад", callback_data='back_get_analytics_menu'))

    await callback_query.message.edit_text(f"<b>Анкета лекции {lecture_name} для группы {group_name}</b>:\n\n"
                                           f"<b>Средняя оценка: {mean_common_evaluation_lecture}</b>\n"
                                           f"<b>Последние отзывы:</b> \n" + "\n\n".join(rewiews.split("\n\n")[:last_reviews+1]), reply_markup=back_menu)


@dp.callback_query_handler(text="back_get_analytics_menu")
async def back_get_analytics_menu(callback_query: types.CallbackQuery):
    text, keyboard = await get_analytics_text(callback_query)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# @dp.callback_query_handler(text_contains='__bam')
# async def handle_callback_query(callback_query: types.CallbackQuery):
#     print('ga_' + callback_query.data.split('__')[0])
#     cal = types.CallbackQuery(data='ga_' + callback_query.data.split('__')[0])
#     await get_analytics_by_lecture(cal)
