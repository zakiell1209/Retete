import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Категории и теги
CATEGORY_NAMES_EMOJI = {
    "body": "Тело",
    "toys": "Игрушки",
    "ethnicity": "Этнос",
    "furry": "Фури",
    "clothes": "Одежда",
    "poses": "Позы",
}

# Все теги по категориям
TAGS = {
    "body": [
        "loli", "milf", "age_21", "thin", "muscular", "curvy", "normal",
        "big_breast", "small_breast", "black_skin", "white_skin",
    ],
    "toys": [
        "anal_dildo", "piercing", "anal_beads", "plug",
    ],
    "ethnicity": [
        "asian", "european", "femboy", "futa",
    ],
    "furry": [
        "furry_queen", "furry_cat", "furry_dog", "furry_dragon", "furry_silveon",
        "cow_costume",
    ],
    "clothes": [
        "cow_bikini_tan_lines", "bikini_tan_lines", "cow_costume",
        "cow_costume",  # костюм коровы дважды для примера
    ],
    "poses": [
        "vertical_splits", "horizontal_splits", "lying_legs_apart",
        "side_one_leg_up", "face_to_viewer", "back_to_viewer",
        "bridge", "suspended_on_ropes",
    ],
}

# Названия тегов с эмодзи и галочками
TAG_NAMES_EMOJI = {
    "body": {
        "loli": "Лоли",
        "milf": "Милфа",
        "age_21": "Возраст 21 года",
        "thin": "Худое",
        "muscular": "Накачаное",
        "curvy": "Пышное",
        "normal": "Нормальное",
        "big_breast": "Большая грудь",
        "small_breast": "Маленькая грудь",
        "black_skin": "Чёрная кожа",
        "white_skin": "Белая кожа",
    },
    "toys": {
        "anal_dildo": "Анал с дилдо",
        "piercing": "Пирсинг",
        "anal_beads": "Анальные бусы",
        "plug": "Пробка",
    },
    "ethnicity": {
        "asian": "Азиатка",
        "european": "Европейка",
        "femboy": "Фембой",
        "futa": "Футанари",
    },
    "furry": {
        "furry_queen": "Фури королева",
        "furry_cat": "Фури кошка",
        "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон",
        "furry_silveon": "Фури сильвеон",
        "cow_costume": "Костюм коровы",
    },
    "clothes": {
        "cow_bikini_tan_lines": "Загар от бикини",
        "bikini_tan_lines": "Загар от бикини (тело)",
        "cow_costume": "Костюм коровы",
    },
    "poses": {
        "vertical_splits": "Шпагат вертикальный",
        "horizontal_splits": "Шпагат горизонтальный",
        "lying_legs_apart": "Лёжа ноги в стороны",
        "side_one_leg_up": "На боку с поднятой одной ногой",
        "face_to_viewer": "Лицом к зрителю",
        "back_to_viewer": "Спиной к зрителю",
        "bridge": "Мост",
        "suspended_on_ropes": "Подвешенная на верёвках",
    },
}

# Промты по тегам (корректные и по твоим правкам)
PROMPTS = {
    "body": {
        "loli": "cute loli girl, youthful face, petite body",
        "milf": "sexy milf woman, mature and attractive",
        "age_21": "young adult woman, age 21",
        "thin": "thin and slender body",
        "muscular": "well-toned muscular body",
        "curvy": "curvy body with full hips and chest",
        "normal": "normal body proportions",
        "big_breast": "large breasts",
        "small_breast": "small breasts",
        "black_skin": "black skin tone",
        "white_skin": "white skin tone",
    },
    "toys": {
        "anal_dildo": "anal dildo inserted",
        "piercing": "piercing on body",
        "anal_beads": "anal beads inserted",
        "plug": "anal plug inserted",
    },
    "ethnicity": {
        "asian": "asian ethnicity",
        "european": "european ethnicity",
        "femboy": "femboy character",
        "futa": "futa character",
    },
    "furry": {
        "furry_queen": "furry queen character",
        "furry_cat": "furry cat character",
        "furry_dog": "furry dog character",
        "furry_dragon": "furry dragon character",
        # Новый промт для сильвеона максимально похожий на известного персонажа:
        "furry_silveon": (
            "furry silveon anthro character, sleek purple and white fur, "
            "large blue eyes, elegant and graceful pose, anime style, "
            "detailed fur texture, fantasy creature, soft lighting"
        ),
        "cow_costume": (
            "girl in cow pattern stockings, wearing cow horns and tail, "
            "no underwear, no full cow figure, only the girl with cow accessories"
        ),
    },
    "clothes": {
        # Загар от бикини - тело смуглое, белые линии от бикини без самой одежды
        "bikini_tan_lines": (
            "tanned skin with white bikini tan lines, no bikini clothing, "
            "skin visible with tan lines on body"
        ),
        "cow_bikini_tan_lines": (
            "tanned skin with white bikini tan lines, no bikini clothing, "
            "skin visible with tan lines on body"
        ),
        "cow_costume": (
            "girl in cow pattern stockings, wearing cow horns and tail, "
            "no underwear, no full cow figure, only the girl with cow accessories"
        ),
    },
    "poses": {
        "vertical_splits": "vertical splits, full body stretch",
        "horizontal_splits": "horizontal splits, full body stretch",
        "lying_legs_apart": "lying on back with legs spread apart",
        "side_one_leg_up": "lying on side with one leg raised",
        "face_to_viewer": "posing facing the viewer",
        "back_to_viewer": "posing back to the viewer",
        "bridge": "body in bridge pose",
        "suspended_on_ropes": "body suspended on ropes, bondage style",
    },
}

# Хранилище выбора пользователя {user_id: {"category": str, "features": list}}
user_settings = {}

def tags_keyboard(category, selected_tags):
    """Создаём клавиатуру тегов с галочками"""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for tag in TAGS[category]:
        checked = "✅ " if tag in selected_tags else ""
        name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)
        btn = types.InlineKeyboardButton(
            text=checked + name,
            callback_data=f"tag_{tag}_{category}"
        )
        buttons.append(btn)
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("Назад", callback_data="back_to_categories"))
    return keyboard

def categories_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for cat, name in CATEGORY_NAMES_EMOJI.items():
        btn = types.InlineKeyboardButton(
            text=name,
            callback_data=f"category_{cat}"
        )
        buttons.append(btn)
    keyboard.add(*buttons)
    return keyboard

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    user_settings[message.from_user.id] = {"category": None, "features": []}
    await message.answer(
        "Выберите категорию тегов:",
        reply_markup=categories_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data)
async def process_callback(call: types.CallbackQuery):
    cid = call.from_user.id
    data = call.data

    if cid not in user_settings:
        user_settings[cid] = {"category": None, "features": []}

    if data.startswith("category_"):
        category = data[len("category_"):]
        user_settings[cid]["category"] = category
        selected_tags = user_settings[cid]["features"]
        # Фильтруем выбранные теги только для текущей категории
        selected_in_cat = [t for t in selected_tags if t in TAGS.get(category, [])]
        text = f"Выбери теги категории {CATEGORY_NAMES_EMOJI.get(category, category)}:\n\n"
        if selected_in_cat:
            selected_names = [TAG_NAMES_EMOJI.get(category, {}).get(t, t) for t in selected_in_cat]
            text += "Выбрано: " + ", ".join(selected_names) + "\n\n"
        else:
            text += "Теги не выбраны\n\n"
        text += "Нажми на тег чтобы выбрать/отменить."
        await bot.edit_message_text(
            text,
            cid,
            call.message.message_id,
            reply_markup=tags_keyboard(category, selected_in_cat)
        )
        await bot.answer_callback_query(call.id)

    elif data.startswith("tag_"):
        parts = data.split("_")
        tag = parts[1]
        category = "_".join(parts[2:])
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
            status = "удалён"
        else:
            tags.append(tag)
            status = "добавлен"
        user_settings[cid]["features"] = tags

        # Выводим только теги выбранной категории
        selected_in_cat = [t for t in tags if t in TAGS.get(category, [])]
        text = f"Выбери теги категории {CATEGORY_NAMES_EMOJI.get(category, category)}:\n\n"
        if selected_in_cat:
            selected_names = [TAG_NAMES_EMOJI.get(category, {}).get(t, t) for t in selected_in_cat]
            text += "Выбрано: " + ", ".join(selected_names) + "\n\n"
        else:
            text += "Теги не выбраны\n\n"
        text += "Нажми на тег чтобы выбрать/отменить."

        await bot.edit_message_text(
            text,
            cid,
            call.message.message_id,
            reply_markup=tags_keyboard(category, selected_in_cat)
        )
        await bot.answer_callback_query(call.id, f"{TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)} {status}")

    elif data == "back_to_categories":
        user_settings[cid]["category"] = None
        await bot.edit_message_text(
            "Выберите категорию тегов:",
            cid,
            call.message.message_id,
            reply_markup=categories_keyboard()
        )
        await bot.answer_callback_query(call.id)

    else:
        await bot.answer_callback_query(call.id, text="Неизвестная команда")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)