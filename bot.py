import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

# --- Глобальные переменные и конфигурация ---
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

# ID новой модели Replicate, которую вы используете
REPLICATE_MODEL = "80441e2c32a55f2fcf9b77fa0a74c6c86ad7deac51eed722b9faedb253265cb1" # Убедился, что это строка

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей, включая выбранные теги

# --- Категории для меню ---
CATEGORY_NAMES = {
    "holes": "🕳️ Отверстия",
    "toys": "🧸 Игрушки",
    "poses": "🧘 Позы",
    "clothes": "👗 Одежда",
    "body": "💪 Тело",
    "ethnos": "🌍 Этнос",
    "furry": "🐾 Фури",
    "characters": "🦸 Персонажи",
    "head": "🤯 Голова",
    "fetish": "🔗 Фетиши",
    "pokemon": "⚡ Покемоны"
}

# --- Теги с новыми добавлениями ---
TAGS = {
    "holes": {
        "vagina": "Вагина",
        "anus": "Анус",
        "both": "Вагина и анус",
        "dilated_anus": "Расширенный анус",
        "dilated_vagina": "Расширенная киска",
        "prolapsed_uterus": "Выпавшая матка",
        "prolapsed_anus": "Выпавший анус",
        "dilated_nipples": "Расширенные соски",
        "anus_spreader_ring": "Расширительное кольцо в анусе",
        "vagina_spreader_ring": "Расширительное кольцо в вагине"
    },
    "toys": {
        "dildo": "Дилдо",
        "huge_dildo": "Большое дилдо",
        "horse_dildo": "Конский дилдо",
        "anal_beads": "Анальные шарики",
        "anal_plug": "Анальная пробка",
        "long_dildo_path": "Дилдо сквозь все тело",
        "urethral_dildo": "Дилдо в уретре",
        "two_dildos_anus_vagina": "Два дилдо в анусе и вагине",
        "two_dildos_one_hole": "Два дилдо в одно отверстие",
    },
    "poses": {
        "doggy": "На четвереньках",
        "standing": "Стоя",
        "squat": "Приседание",
        "lying": "Лежа",
        "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат",
        "on_back_legs_behind_head": "На спине ноги за головой",
        "on_side_leg_up": "На боку нога вверх",
        "suspended": "Подвешена",
        "front_facing": "Вид спереди",
        "back_facing": "Вид сзади",
        "top_down_view": "Вид сверху",
        "bottom_up_view": "Вид снизу",
        "hands_spreading_vagina": "Руки раздвигают влагалище",
        "lotus_pose": "Поза лотоса",
        "scissors_pose": "Поза ножницы (две девушки)",
        "inverted_extreme_bridge": "Экстремальный мост/стойка на плечах с инверсией",
        "leaning_forward_wall": "Наклон вперёд у стены",
        "standing_vertical_split_supported": "Вертикальный шпагат стоя с поддержкой",
        "boat_pose_double_split_up": "Поза лодки / двойной шпагат вверх",
        "deep_sumo_squat": "Глубокий присед (сумо-поза)",
        "standing_horizontal_split_balanced": "Горизонтальный шпагат стоя с балансом",
        "classic_bridge": "Мостик",
        "sitting_horizontal_split_supported": "Горизонтальный шпагат сидя с опорой",
        # Новые позы
        "prone_frog_stretch": "Пролёт вперёд, плечевой растяг",
        "standing_deep_forward_bend": "Стоячий глубокий прогиб с опорой на руки",
        "forward_bow_forearms_clasped": "Наклон со сведёнными предплечьями",
        "top_down_voluminous_bow": "Объёмный поклон сверху (вид сверху)",
        "inverted_leg_over_shoulder": "Перевёрнутый сгиб с коленом над плечом",
        "casual_seated_open_knees": "Лёгкая поза сидя, колени разведены",
    },
    "clothes": {
        "stockings": "Чулки", # Subcategory trigger
        "bikini_tan_lines": "Линии от загара в бикини",
        "shibari": "Шибари",
        "cow_costume": "Костюм коровы"
    },
    "body": {
        "big_breasts": "Большая грудь",
        "small_breasts": "Маленькая грудь",
        "body_fit": "Подтянутое тело",
        "body_fat": "Пышное тело",
        "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли",
        "age_milf": "Милфа",
        "age_21": "21 год",
        "cum": "Вся в сперме",
        "belly_bloat": "Вздутие живота (похоже на беременность)",
        "succubus_tattoo": "Татуировка суккуба"
    },
    "ethnos": {
        "futanari": "Футанари",
        "femboy": "Фембой",
        "ethnicity_asian": "Азиатка",
        "ethnicity_european": "Европейка"
    },
    "furry": {
        "furry_cow": "Фури корова",
        "furry_cat": "Фури кошка",
        "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон",
        "furry_sylveon": "Фури сильвеон",
        "furry_fox": "Фури лисица",
        "furry_bunny": "Фури кролик",
        "furry_wolf": "Фури волчица",
        "furry_bear": "Фури медведь",
        "furry_bird": "Фури птица",
        "furry_mouse": "Фури мышь",
        "furry_deer": "Фури олень",
        "furry_tiger": "Фури тигр",
        "furry_lion": "Фури лев",
        "furry_snake": "Фури змея",
        "furry_lizard": "Фури ящерица"
    },
    "characters": {
        # Демоны старшей школы
        "dxd_rias": "Риас Грегори",
        "dxd_akeno": "Акено Химеджима",
        "dxd_xenovia_quarta": "Ксеновия Кварта",
        "dxd_serafall_leviathan": "Серафалл Левиафан",
        "dxd_asia_argento": "Азия Ардженто",
        "dxd_koneko_toujou": "Конеко Тодзё",
        "dxd_shidou_irina": "Шидо Ирина",
        "dxd_gasper_vladi": "Гаспер Влади",
        "dxd_rossweisse": "Россвайссе",
        "dxd_yasaka": "Ясака",
        "dxd_grayfia_lucifuge": "Грейфия Люцифуг",
        
        # Genshin Impact
        "genshin_eula": "Еола",
        "genshin_mona": "Мона",
        "genshin_klee": "Кли",
        "genshin_raiden_shogun": "Райден",
        "genshin_paimon": "Паймон",
        "genshin_amber": "Эмбер",
        "genshin_barbara": "Барбара",
        "genshin_beidou": "Бэй Доу",
        "genshin_collei": "Коллеи",
        "genshin_dehya": "Дэхья",
        "genshin_diluc_f": "Дилюк (F)",
        "genshin_diona": "Диона",
        "genshin_fischl": "Фишль",
        "genshin_ganyu": "Гань Юй",
        "genshin_hutao": "Ху Тао",
        "genshin_jean": "Джинн",
        "genshin_kazuha_f": "Кадзуха (F)",
        "genshin_keqing": "Кэ Цин",
        "genshin_kuki_shinobu": "Куки Синобу",
        "genshin_lisa": "Лиза",
        "genshin_nahida": "Нахида",
        "genshin_ningguang": "Нин Гуан",
        "genshin_noelle": "Ноэлль",
        "genshin_rosaria": "Розария",
        "genshin_sara": "Кудзё Сара",
        "genshin_sayu": "Саю",
        "genshin_shenhe": "Шэнь Хэ",
        "genshin_sucrose": "Сахароза",
        "genshin_venti_f": "Венти (F)",
        "genshin_xiangling": "Сян Лин",
        "genshin_xinyan": "Синь Янь",
        "genshin_yaemiko": "Яэ Мико",
        "genshin_yanfei": "Янь Фэй",
        "genshin_yoimiya": "Ёимия",
        "genshin_yelan": "Е Лань",
        "genshin_zhongli_f": "Чжун Ли (F)",
        "genshin_furina": "Фурина",
        "genshin_navia": "Навия",
        "genshin_chevreuse": "Шеврёз",
        "genshin_clorinde": "Клоринда",
        "genshin_ar_traveler_f": "Аether (F)",
        "genshin_lumine": "Люмин",
        "genshin_signora": "Синьора",
        "genshin_arlecchino": "Арлекино",
        "genshin_snezhnaya_fatui_harbinger": "Предвестник Фатуи",

        # Honkai Star Rail
        "hsr_kafka": "Кафка",
        "hsr_fu_xuan": "Фу Сюань",
        "hsr_sparkle": "Искорка",
        "hsr_acheron": "Геоцина",
        "hsr_march_7th": "Март 7",
        "hsr_himeko": "Химеко",
        "hsr_bronya": "Броня",
        "hsr_seele": "Зеле",
        "hsr_jingliu": "Цзинлю",
        "hsr_stelle": "Стелла (F)",
        "hsr_herta": "Герта",
        "hsr_silver_wolf": "Серебряный Волк",
        "hsr_tingyun": "Тинъюнь",
        "hsr_asta": "Аста",
        "hsr_clara": "Клара",
        "hsr_peia": "Пэйя",
        "hsr_sushang": "Сушан",
        "hsr_natasha": "Наташа",
        "hsr_hook": "Хук",
        "hsr_pela": "Пела",
        "hsr_qingque": "Цинцюэ",
        "hsr_yukong": "Юйкун",
        "hsr_guinaifen": "Гуйнайфэнь",
        "hsr_huohuo": "Хохо",
        "hsr_xueyi": "Сюэи",
        "hsr_hanabi": "Ханами",
        "hsr_robin": "Робин",
        "hsr_aventurine_f": "Авантюрин (F)",

        # NieR Automata
        "nier_2b": "2B",

        # Spy x Family
        "spyxfamily_yor_forger": "Йор Форджер",

        # Akame ga Kill
        "akamegakill_esdeath": "Есдес",

        # Azur Lane
        "azurlane_formidable": "Formidable",

        # Fate Series
        "fate_castoria": "Кастория",
        "fate_saber": "Сейбер",
        "fate_astolfo": "Астольфо",

        # Resident Evil
        "residentevil_lady_dimitrescu": "Леди Димитреску",

        # Street Fighter
        "streetfighter_chun_li": "Чун Ли",
        "streetfighter_cammy": "Кэмми",
        "streetfighter_balrog_f": "Балрог (женская версия)",
        "streetfighter_juri": "Джури",
        "streetfighter_menat": "Менат",
        "streetfighter_laura": "Лаура",
        "streetfighter_poison": "Пойсон",
        "streetfighter_maki": "Маки",
        "streetfighter_rose": "Роуз",
        "streetfighter_r_mika": "Р. Мика",
        "streetfighter_ibuki": "Ибуки",
        "streetfighter_karin": "Карин",
        "streetfighter_ed": "Эд",
        "streetfighter_fang": "Фалькон",
        "streetfighter_e_honda_f": "Иви",

        # Atomic Heart
        "atomicheart_twins": "Близняшки",

        # Bleach - НОВЫЕ ПЕРСОНАЖИ
        "bleach_renji_f": "Ренджи Абарай (F)",
        "bleach_rukia_kuchiki": "Рукия Кучики",
        "bleach_orihime_inoue": "Орихиме Иноуэ",
        "bleach_yoruichi_shihoin": "Йоруичи Шихоин",
        "bleach_rangiku_matsumoto": "Рангику Мацумото",
        "bleach_nemu_kurotsuchi": "Нему Куроцучи",
        "bleach_nelliel_tu_odelschwanck": "Неллиэль Ту Одельшванк",
        "bleach_tier_harribel": "Тиа Харрибел",
        "bleach_retsu_unohana": "Ретсу Унохана",
        "bleach_soi_fon": "Сой Фон",
        "bleach_hiyori_sarugaki": "Хиёри Саругаки",
        "bleach_lisa_yadomaru": "Лиза Ядомару",
        "bleach_mashiro_kuna": "Маширо Куна",
        "bleach_nanao_ise": "Нанао Исе",
        "bleach_isane_kotetsu": "Исане Котецу",
        "bleach_momo_hinamori": "Момо Хинамири",
        "bleach_candice_catnipp": "Кэндис Катнипп",
        "bleach_bambietta_basterbine": "Бамбиетта Бастербайн",
        "bleach_giselle_gewelle": "Гизель Жевелль",
        "bleach_meninas_mcallon": "Менинас МакАллон",
        "bleach_liltotto_lamperd": "Лилттото Ламперд",

        # Danmachi
        "danmachi_hestia": "Гестия",
        "danmachi_freya": "Фрея",

        # Повесть о конце света (Record of Ragnarok)
        "ragnarok_aphrodite": "Афродита",

        # Naruto
        "naruto_hinata": "Хината",
        "naruto_tsunade": "Цунаде",

        # Overlord
        "overlord_albedo": "Альбедо",
        "overlord_shalltear": "Шалтир",

        # Безумный азарт (Kakegurui)
        "kakegurui_yumeko": "Юмеко Джабами",
        "kakegurui_kirari": "Кирари Момобами",
        "kakegurui_mary": "Мэри Саотомэ",

        # Магическая битва (Jujutsu Kaisen)
        "jujutsukaisen_mei_mei": "Мэй Мэй",

        # Герой Щита (The Rising of the Shield Hero)
        "shieldhero_mirelia_melromarc": "Мирелия К. Мелромарк",
        "shieldhero_malty_melromarc": "Малти С. Мелромарк",
        
        # Helltaker
        "helltaker_lucifer": "Люцифер",

        # Zenless Zone Zero
        "zzz_ellen_joe": "Эллен Джо",
        "zzz_koleda": "Коледа",
        "zzz_lycaon": "Ликаон (F)",
        "zzz_nicole": "Николь",
        "zzz_anby": "Энби",
        "zzz_nekomiya": "Нэкомия",
        "zzz_aisha": "Айша",
        "zzz_haruka": "Харука",
        "zzz_corin": "Корин",
        "zzz_grace": "Грейс",
        "zzz_hoshimi": "Хосими",
        "zzz_rory": "Рори",
        "zzz_bonnie": "Бонни",
        "zzz_elize": "Элиза",
        "zzz_fubuki": "Фубуки",
        "zzz_sana": "Сана",
        "zzz_yuki": "Юки",
        
        # League of Legends
        "lol_qiyana": "Киана",
        "lol_aurora": "Аврора",
        "lol_katarina": "Катарина",
        "lol_akali": "Акали",
        "lol_irelia": "Ирелия",
        "lol_caitlyn": "Кейтлин",
        "lol_briar": "Брайер",
        "lol_kaisa": "Кай'Са",
        "lol_evelynn": "Эвелинн",
        "lol_ahri": "Ари",
        "lol_belveth": "Бел'Вет",
        "lol_fiora": "Фиора",
        "lol_gwen": "Гвен",
        "lol_zoe": "Зои",
        "lol_missfortune": "Мисс Фортуна",
        "lol_neeko": "Нико",
        "lol_samira": "Самира",
        "lol_sona": "Сона",
        "lol_elise": "Элиза",

        # My Little Pony
        "mlp_twilight_sparkle": "Сумеречная Искорка",
        "mlp_applejack": "Эпплджек",
        "mlp_rainbow_dash": "Радуга Дэш",
        "mlp_rarity": "Рарити",
        "mlp_fluttershy": "Флаттершай",
        "mlp_pinkie_pie": "Пинки Пай",
        "mlp_spike": "Спайк",
        "mlp_princess_celestia": "Принцесса Селестия",
        "mlp_princess_luna": "Принцесса Луна",
        "mlp_princess_cadence": "Принцесса Каденс",
        "mlp_discord": "Дискорд",
        "mlp_apple_bloom": "Эппл Блум",
        "mlp_scootaloo": "Скуталу",
        "mlp_sweetie_belle": "Крошка Бель",

        # Dislyte
        "dislyte_li_ling_f": "Ли Лин (F)",
        "dislyte_sally": "Салли",
        "dislyte_clara": "Клара",
        "dislyte_gabrielle": "Габриэль",
        "dislyte_chloe": "Хлоя",
        "dislyte_odette": "Одетта",
        "dislyte_meredith": "Мередит",
        "dislyte_jiang_man": "Цзян Мань",
        "dislyte_eira": "Эйра",
        "dislyte_drew": "Дрю",
        "dislyte_pritzker_f": "Притцкер (F)",
        "dislyte_fatima": "Фатима",
        "dislyte_brewster_f": "Брюстер (F)",
        "dislyte_yun_chuan_f": "Юнь Чуань (F)",
        "dislyte_hyde_f": "Хайд (F)",
        "dislyte_leora": "Леора",
        "dislyte_tevor_f": "Тевор (F)",
        "dislyte_zora": "Зора",
        "dislyte_embla": "Эмбла",
        "dislyte_ophilia": "Офелия",
        "dislyte_ahmed_f": "Ахмед (F)",
        "dislyte_everett_f": "Эверетт (F)",
        "dislyte_ollie_f": "Олли (F)",
        "dislyte_jin_hee": "Джин Хи",
        "dislyte_ifrit_f": "Ифрит (F)",
        "dislyte_sienna": "Сиенна",
        "dislyte_valeria": "Валерия",
        "dislyte_ashley": "Эшли",
        "dislyte_triki_f": "Трики (F)",
        "dislyte_narmer_f": "Нармер (F)",
        "dislyte_tye": "Тай",
        "dislyte_biondina": "Биондина",
        "dislyte_dhalia": "Далия",
        "dislyte_elaine": "Элейн",
        "dislyte_cecilia": "Сесилия",
        "dislyte_intisar": "Интисар",
        "dislyte_kaylee": "Кейли",
        "dislyte_layla": "Лейла",
        "dislyte_lynn": "Линн",
        "dislyte_melanie": "Мелани",
        "dislyte_mona": "Мона",
        "dislyte_nicole": "Николь",
        "dislyte_q": "Кью",
        "dislyte_ren_si": "Жэнь Си",
        "dislyte_stewart_f": "Стюарт (F)",
        "dislyte_tang_xuan_f": "Тан Сюань (F)",
        "dislyte_unaky": "Унаки",
        "dislyte_victoria": "Виктория",
        "dislyte_xiao_yin": "Сяо Инь",
        "dislyte_ye_suhua": "Е Сухуа",
        "dislyte_zhong_nan": "Чжун Нань",
        "dislyte_anadora": "Анадора",
        "dislyte_bernice": "Бернис",
        "dislyte_brynn": "Бринн",
        "dislyte_catherine": "Катерина",
        "dislyte_chang_pu": "Чан Пу",
        "dislyte_eugene_f": "Юджин (F)",
        "dislyte_freddy_f": "Фредди (F)",
        "dislyte_hall_f": "Холл (F)",
        "dislyte_helena": "Хелена",
        "dislyte_jacob_f": "Джейкоб (F)",
        "dislyte_jeanne": "Жанна",
        "dislyte_li_ao_f": "Ли Ао (F)",
        "dislyte_lu_yi_f": "Лу И (F)",
        "dislyte_mark_f": "Марк (F)",
        "dislyte_olivia": "Оливия",
        "dislyte_sander_f": "Сандер (F)",
        "dislyte_stella": "Стелла",
        "dislyte_alice": "Алиса",
        "dislyte_arcana": "Аркана",
        "dislyte_aurelius_f": "Аурелиус (F)",
        "dislyte_bette": "Бетте",
        "dislyte_bonnie": "Бонни",
        "dislyte_celine": "Селин",
        "dislyte_corbin_f": "Корбин (F)",
    },
    "head": {
        "ahegao": "Ахегао",
        "pain_face": "Лицо в боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "fetish": {
        "nipple_piercing": "Пирсинг сосков",
        "clitoral_piercing": "Пирсинг клитора",
        "foot_fetish": "Фетиш стоп",
        "footjob": "Футджоб",
        "mouth_nipples": "Рты вместо сосков",
        "nipple_hole": "Отверстие в соске",
        "anus_piercing": "Пирсинг ануса",
        "vagina_piercing": "Пирсинг вагины",
        "gag": "Кляп",
        "blindfold": "Повязка на глаза",
        "horse_sex": "Секс с конем"
    },
    "pokemon": {
        "reshiram": "Реширам",
        "mew": "Мю",
        "mewtwo": "Мюту",
        "gardevoir": "Гардевуар",
        "umbreon": "Эмбреон",
        "lugia": "Лугия",
        "shadow_lugia": "Шадоу Лугия",
        "lopunny": "Лопанни",
        "goodra": "Гудра",
        "pokemon_jessie": "Джесси",
        "pokemon_lusamine": "Лусамине",
    }
}

# Категории для персонажей (для вкладок)
CHARACTER_CATEGORIES = {
    "dxd": "📺 Демоны старшей школы",
    "genshin": "🎮 Genshin Impact",
    "hsr": "🎮 Honkai Star Rail",
    "nier": "🎮 NieR Automata",
    "spyxfamily": "📺 Spy x Family",
    "akamegakill": "📺 Akame ga Kill",
    "azurlane": "🎮 Azur Lane",
    "fate": "📺 Fate Series",
    "residentevil": "🎮 Resident Evil",
    "streetfighter": "🎮 Street Fighter",
    "atomicheart": "🎮 Atomic Heart",
    "bleach": "📺 Bleach",
    "danmachi": "📺 Danmachi",
    "ragnarok": "📺 Повесть о конце света",
    "naruto": "📺 Naruto",
    "overlord": "📺 Overlord",
    "kakegurui": "📺 Безумный азарт",
    "jujutsukaisen": "📺 Магическая битва",
    "shieldhero": "📺 Герой Щита",
    "helltaker": "🎮 Helltaker",
    "zzz": "🎮 Zenless Zone Zero",
    "lol": "🎮 League of Legends",
    "mlp": "📺 My Little Pony",
    "dislyte": "🎮 Dislyte"
}

# --- Промпты для персонажей (если они требуют специфичных описаний, отличных от их имен) ---
CHARACTER_PROMPTS = {
    "dxd_rias": "Rias Gremory, long red hair, large breasts, demon, school uniform, cleavage",
    "dxd_akeno": "Akeno Himejima, black hair, large breasts, demon, school uniform, glasses",
    "dxd_xenovia_quarta": "Xenovia Quarta, blue hair, church uniform, sword",
    "dxd_serafall_leviathan": "Serafall Leviathan, pink hair, maid outfit, playful",
    "dxd_asia_argento": "Asia Argento, blonde hair, nun outfit, innocent",
    "dxd_koneko_toujou": "Koneko Toujou, white hair, small body, school uniform, neko ears",
    "dxd_shidou_irina": "Shidou Irina, blonde pigtails, angel, church uniform",
    "dxd_gasper_vladi": "Gasper Vladi, male, femboy, vampire, crossdresser, gothic lolita",
    "dxd_rossweisse": "Rossweisse, valkyrie, long silver hair, glasses",
    "dxd_yasaka": "Yasaka, nine-tailed fox, kimono, mature woman",
    "dxd_grayfia_lucifuge": "Grayfia Lucifuge, maid, silver hair, powerful",

    "genshin_eula": "Eula, Genshin Impact, pale skin, blue hair, noble, icy, elegant dress",
    "genshin_mona": "Mona Megistus, Genshin Impact, astrologist, dark leotard, hat, long dark hair",
    "genshin_klee": "Klee, Genshin Impact, small girl, blonde hair, red dress, bombs, elf ears",
    "genshin_raiden_shogun": "Raiden Shogun, Genshin Impact, purple kimono, long purple hair, electro archon",
    "genshin_paimon": "Paimon, Genshin Impact, fairy, small size, white hair",
    "genshin_amber": "Amber, Genshin Impact, outrider, bow, red scarf, brown hair",
    "genshin_barbara": "Barbara, Genshin Impact, idol, healer, blue dress, blonde hair",
    "genshin_beidou": "Beidou, Genshin Impact, pirate captain, dark clothes, eyepatch, strong woman",
    "genshin_collei": "Collei, Genshin Impact, forest ranger, green outfit, short green hair",
    "genshin_dehya": "Dehya, Genshin Impact, mercenary, desert warrior, dark skin, red hair",
    "genshin_diluc_f": "Diluc (female), Genshin Impact, female version of Diluc, red hair, elegant dress, noble",
    "genshin_diona": "Diona, Genshin Impact, cat girl, bartender, twin tails, cat ears, cat tail",
    "genshin_fischl": "Fischl, Genshin Impact, princess, gothic lolita, eyepatch, raven companion",
    "genshin_ganyu": "Ganyu, Genshin Impact, qilin, blue hair, horns, tight suit, ice powers",
    "genshin_hutao": "Hu Tao, Genshin Impact, funeral parlor director, brown hair, flower in hair, ghost companion",
    "genshin_jean": "Jean Gunnhildr, Genshin Impact, acting grand master, blonde hair, blue uniform",
    "genshin_kazuha_f": "Kaedehara Kazuha (female), Genshin Impact, female version of Kazuha, red streak in hair, samurai",
    "genshin_keqing": "Keqing, Genshin Impact, electro, purple hair, cat ear-like buns",
    "genshin_kuki_shinobu": "Kuki Shinobu, Genshin Impact, ninja, mask, green hair",
    "genshin_lisa": "Lisa Minci, Genshin Impact, librarian, purple dress, witch hat",
    "genshin_nahida": "Nahida, Genshin Impact, dendro archon, small girl, white hair, green dress",
    "genshin_ningguang": "Ningguang, Genshin Impact, geo, elegant dress, long white hair, floating jade screen",
    "genshin_noelle": "Noelle, Genshin Impact, maid, knight, blonde hair, armor",
    "genshin_rosaria": "Rosaria, Genshin Impact, nun, dark clothing, fishnets, pale skin, red eyes",
    "genshin_sara": "Kujou Sara, Genshin Impact, tengu, black wings, dark uniform",
    "genshin_sayu": "Sayu, Genshin Impact, ninja, small, tanuki hoodie",
    "genshin_shenhe": "Shenhe, Genshin Impact, adepti disciple, white hair, long sleeves, frosty",
    "genshin_sucrose": "Sucrose, Genshin Impact, alchemist, glasses, green hair, cat ears",
    "genshin_venti_f": "Venti (female), Genshin Impact, female version of Venti, green clothes, bard",
    "genshin_xiangling": "Xiangling, Genshin Impact, chef, panda companion, braided hair",
    "genshin_xinyan": "Xinyan, Genshin Impact, rock 'n' roll musician, dark skin, punk outfit",
    "genshin_yaemiko": "Yae Miko, Genshin Impact, kitsune, pink hair, fox ears, shrine maiden",
    "genshin_yanfei": "Yanfei, Genshin Impact, legal advisor, deer horns, red and white outfit",
    "genshin_yoimiya": "Yoimiya, Genshin Impact, fireworks master, blonde hair, summer outfit, playful",
    "genshin_yelan": "Yelan, Genshin Impact, spy, short blue hair, dark suit, confident",
    "genshin_zhongli_f": "Zhongli (female), Genshin Impact, female version of Zhongli, brown hair, geo archon",
    "genshin_furina": "Furina, Genshin Impact, hydro archon, elegant white and blue dress, long white hair",
    "genshin_navia": "Navia, Genshin Impact, elegant yellow dress, large hat, blonde hair, umbrella",
    "genshin_chevreuse": "Chevreuse, Genshin Impact, police officer, red uniform, short dark hair",
    "genshin_clorinde": "Clorinde, Genshin Impact, duelist, dark uniform, long dark hair, elegant",
    "genshin_ar_traveler_f": "Aether (female), Genshin Impact, blonde hair, white and brown outfit",
    "genshin_lumine": "Lumine, Genshin Impact, blonde hair, white and gold outfit",
    "genshin_signora": "Signora, Genshin Impact, Fatui Harbinger, elegant gothic dress, masked",
    "genshin_arlecchino": "Arlecchino, Genshin Impact, Fatui Harbinger, black and white outfit, serious, long dark hair",
    "genshin_snezhnaya_fatui_harbinger": "Snezhnaya Fatui Harbinger, Genshin Impact, masked, dark uniform",

    "hsr_kafka": "Kafka, Honkai Star Rail, long pink hair, elegant dark clothes, seductive",
    "hsr_fu_xuan": "Fu Xuan, Honkai Star Rail, pink hair, traditional outfit, small body, wise",
    "hsr_sparkle": "Sparkle, Honkai Star Rail, mask, pink hair, playful, jester",
    "hsr_acheron": "Acheron, Honkai Star Rail, purple hair, dark uniform, samurai, elegant",
    "hsr_march_7th": "March 7th, Honkai Star Rail, pink and blue hair, camera, cheerful, winter jacket",
    "hsr_himeko": "Himeko, Honkai Star Rail, long red hair, elegant red dress, coffee",
    "hsr_bronya": "Bronya Zaychik, Honkai Star Rail, silver hair, elegant military uniform",
    "hsr_seele": "Seele, Honkai Star Rail, blue hair, butterfly motif, scythe",
    "hsr_jingliu": "Jingliu, Honkai Star Rail, blindfolded, white hair, elegant swordswoman",
    "hsr_stelle": "Stelle, Honkai Star Rail, female Trailblazer, short brown hair, unique outfit",
    "hsr_herta": "Herta, Honkai Star Rail, scientist, puppet, blue hair",
    "hsr_silver_wolf": "Silver Wolf, Honkai Star Rail, hacker, short blue hair, gamer headset",
    "hsr_tingyun": "Tingyun, Honkai Star Rail, foxian, elegant dress, fox ears, fan",
    "hsr_asta": "Asta, Honkai Star Rail, researcher, red hair, glasses, cheerful",
    "hsr_clara": "Clara, Honkai Star Rail, small girl, robot companion, red hood",
    "hsr_peia": "Pela, Honkai Star Rail, researcher, glasses, uniform, short blue hair",
    "hsr_sushang": "Sushang, Honkai Star Rail, martial artist, long brown hair, bird companion",
    "hsr_natasha": "Natasha, Honkai Star Rail, doctor, blonde hair, medical uniform",
    "hsr_hook": "Hook, Honkai Star Rail, small girl, mining outfit, pickaxe",
    "hsr_pela": "Pela, Honkai Star Rail, glasses, dark uniform, short blue hair",
    "hsr_qingque": "Qingque, Honkai Star Rail, mahjong player, green hair, casual outfit",
    "hsr_yukong": "Yukong, Honkai Star Rail, foxian, pilot, elegant uniform, long dark hair",
    "hsr_guinaifen": "Guinaifen, Honkai Star Rail, street performer, red hair, fire cracker",
    "hsr_huohuo": "Huohuo, Honkai Star Rail, ghost, green hair, tail, timid",
    "hsr_xueyi": "Xueyi, Honkai Star Rail, puppet, pink hair, elegant dress, cold",
    "hsr_hanabi": "Sparkle, Honkai Star Rail, mask, pink hair, playful, jester",
    "hsr_robin": "Robin, Honkai Star Rail, singer, elegant white dress, wings, blonde hair",
    "hsr_aventurine_f": "Aventurine (female), Honkai Star Rail, female version of Aventurine, gambler, confident",

    "nier_2b": "2B, Nier Automata, white hair, blindfold, black gothic dress, sword",

    "spyxfamily_yor_forger": "Yor Forger, Spy x Family, assassin, black dress, long black hair, elegant",

    "akamegakill_esdeath": "Esdeath, Akame ga Kill, ice powers, military uniform, long blue hair, sadistic",

    "azurlane_formidable": "Formidable, Azur Lane, aircraft carrier, long blonde hair, elegant dress, large breasts",

    "fate_castoria": "Castoria, Fate Grand Order, Saber, long blonde hair, blue dress, a bit shy",
    "fate_saber": "Saber, Fate Series, blonde hair, blue and white armor, sword, brave",
    "fate_astolfo": "Astolfo, Fate Grand Order, male, femboy, pink hair, rider, school uniform",

    "residentevil_lady_dimitrescu": "Lady Dimitrescu, Resident Evil Village, tall, vampire, white dress, large hat, seductive",

    "streetfighter_chun_li": "Chun-Li, Street Fighter, strong legs, blue qipao, spike bracelets, buns hair",
    "streetfighter_cammy": "Cammy White, Street Fighter, braided blonde hair, green leotard, muscular legs",
    "streetfighter_balrog_f": "Balrog (female), Street Fighter, female version of Balrog, boxer, muscular body",
    "streetfighter_juri": "Juri Han, Street Fighter, purple hair, sadistic, martial artist, unique eyes",
    "streetfighter_menat": "Menat, Street Fighter, fortune teller, egyptian outfit, orb",
    "streetfighter_laura": "Laura Matsuda, Street Fighter, brazilian fighter, green and yellow outfit, electric powers",
    "streetfighter_poison": "Poison, Street Fighter, crossdresser, pink hair, short shorts, handcuffs",
    "streetfighter_maki": "Maki Genryusai, Street Fighter, ninja, black uniform, short hair",
    "streetfighter_rose": "Rose, Street Fighter, red scarf, elegant dress",
    "streetfighter_r_mika": "R. Mika, Street Fighter, wrestler, blue leotard, energetic",
    "streetfighter_ibuki": "Ibuki, Street Fighter, ninja, school uniform, mask",
    "streetfighter_karin": "Karin Kanzuki, Street Fighter, rich girl, elegant dress, blonde hair",
    "streetfighter_ed": "Ed (female), Street Fighter, female version of Ed, boxer, psychic powers",
    "streetfighter_fang": "F.A.N.G. (female), Street Fighter, female version of F.A.N.G., poisonous attacks",
    "streetfighter_e_honda_f": "E. Honda (female), Street Fighter, female version of E. Honda, sumo wrestler, large body",

    "atomicheart_twins": "Atomic Heart Twins, robot, ballet dancer, red suit, metallic body, seductive",

    "bleach_renji_f": "Renji Abarai (female), Bleach, female version of Renji, red hair, tattoos, zanpakuto",
    "bleach_rukia_kuchiki": "Rukia Kuchiki, Bleach, small, black hair, shinigami uniform",
    "bleach_orihime_inoue": "Orihime Inoue, Bleach, long orange hair, cheerful, healing powers",
    "bleach_yoruichi_shihoin": "Yoruichi Shihouin, Bleach, dark skin, purple hair, cat form, agile",
    "bleach_rangiku_matsumoto": "Rangiku Matsumoto, Bleach, large breasts, blonde hair, shinigami uniform",
    "bleach_nemu_kurotsuchi": "Nemu Kurotsuchi, Bleach, artificial human, dark hair, quiet",
    "bleach_nelliel_tu_odelschwanck": "Nelliel Tu Odelschwanck, Bleach, green hair, mask fragments, child form, adult form",
    "bleach_tier_harribel": "Tier Harribel, Bleach, arrancar, blonde hair, shark-like features, serious",
    "bleach_retsu_unohana": "Retsu Unohana, Bleach, long black hair, kind appearance, secretly strong",
    "bleach_soi_fon": "Soi Fon, Bleach, short dark hair, assassin, shinigami uniform",
    "bleach_hiyori_sarugaki": "Hiyori Sarugaki, Bleach, blonde pigtails, foul-mouthed, hollow mask",
    "bleach_lisa_yadomaru": "Lisa Yadomaru, Bleach, glasses, long dark hair, vizored",
    "bleach_mashiro_kuna": "Mashiro Kuna, Bleach, green hair, energetic, vizored",
    "bleach_nanao_ise": "Nanao Ise, Bleach, glasses, dark hair, vice-captain",
    "bleach_isane_kotetsu": "Isane Kotetsu, Bleach, tall, blue hair, healer",
    "bleach_momo_hinamori": "Momo Hinamori, Bleach, brown hair, kind, shinigami uniform",
    "bleach_candice_catnipp": "Candice Catnipp, Bleach, sternritter, blonde pigtails, lightning powers",
    "bleach_bambietta_basterbine": "Bambietta Basterbine, Bleach, sternritter, short dark hair, explosive powers",
    "bleach_giselle_gewelle": "Giselle Gewelle, Bleach, sternritter, zombie, pink hair",
    "bleach_meninas_mcallon": "Meninas Mcallon, Bleach, sternritter, muscular, blonde hair",
    "bleach_liltotto_lamperd": "Liltotto Lamperd, Bleach, sternritter, small girl, dark hair, glasses",

    "danmachi_hestia": "Hestia, Danmachi, small breasts, blue ribbons, goddess, black hair",
    "danmachi_freya": "Freya, Danmachi, goddess, long blonde hair, seductive, elegant dress",

    "ragnarok_aphrodite": "Aphrodite, Record of Ragnarok, goddess, large breasts, two small attendants on shoulders",

    "naruto_hinata": "Hinata Hyuga, Naruto, long dark hair, gentle, byakugan, shy",
    "naruto_tsunade": "Tsunade, Naruto, large breasts, blonde hair, strong, medic ninja",

    "overlord_albedo": "Albedo, Overlord, succubus, black wings, white dress, horns, devoted",
    "overlord_shalltear": "Shalltear Bloodfallen, Overlord, vampire, gothic lolita dress, blonde hair",

    "kakegurui_yumeko": "Yumeko Jabami, Kakegurui, crazy smile, black hair, school uniform, gambling addict",
    "kakegurui_kirari": "Kirari Momobami, Kakegurui, student council president, white hair, unique eyes",
    "kakegurui_mary": "Mary Saotome, Kakegurui, blonde hair, school uniform, ambitious",

    "jujutsukaisen_mei_mei": "Mei Mei, Jujutsu Kaisen, black hair, braid, axe user, confident",

    "shieldhero_mirelia_melromarc": "Mirelia Q. Melromarc, The Rising of the Shield Hero, queen, elegant dress, blonde hair",
    "shieldhero_malty_melromarc": "Malty S. Melromarc, The Rising of the Shield Hero, red hair, princess, evil smile",
    
    "helltaker_lucifer": "Lucifer, Helltaker, demon, suit, queen of hell, elegant",

    "zzz_ellen_joe": "Ellen Joe, Zenless Zone Zero, silver hair, dual guns, mercenary",
    "zzz_koleda": "Koleda, Zenless Zone Zero, ice axe, strong, red hair",
    "zzz_lycaon": "Lycaon (female), Zenless Zone Zero, female version of Lycaon, wolf ears, claws",
    "zzz_nicole": "Nicole Demara, Zenless Zone Zero, fox ears, stylish outfit, tech expert",
    "zzz_anby": "Anby Demara, Zenless Zone Zero, short white hair, black hoodie, casual",
    "zzz_nekomiya": "Nekomya, Zenless Zone Zero, cat girl, maid outfit, cute",
    "zzz_aisha": "Aisha, Zenless Zone Zero, short dark hair, casual outfit",
    "zzz_haruka": "Haruka, Zenless Zone Zero, long blonde hair, school uniform",
    "zzz_corin": "Corin, Zenless Zone Zero, police uniform, short blonde hair",
    "zzz_grace": "Grace, Zenless Zone Zero, elegant black dress, mysterious",
    "zzz_hoshimi": "Hoshimi, Zenless Zone Zero, idol, pink hair, stage outfit",
    "zzz_rory": "Rory, Zenless Zone Zero, punk style, green hair",
    "zzz_bonnie": "Bonnie, Zenless Zone Zero, casual, short brown hair",
    "zzz_elize": "Elize, Zenless Zone Zero, glasses, elegant, long hair",
    "zzz_fubuki": "Fubuki, Zenless Zone Zero, swordswoman, white kimono",
    "zzz_sana": "Sana, Zenless Zone Zero, small girl, animal ears, playful",
    "zzz_yuki": "Yuki, Zenless Zone Zero, short blue hair, innocent",
    
    "lol_qiyana": "Qiyana, League of Legends, elementalist, large golden weapon, confident",
    "lol_aurora": "Aurora, League of Legends, spirit walker, blue hair, elegant, mystical",
    "lol_katarina": "Katarina, League of Legends, assassin, red hair, daggers",
    "lol_akali": "Akali, League of Legends, ninja, mask, tattoos, agile",
    "lol_irelia": "Irelia, League of Legends, dancer, floating blades, elegant",
    "lol_caitlyn": "Caitlyn, League of Legends, sheriff, sniper, long blue hair, hat",
    "lol_briar": "Briar, League of Legends, berserker, straitjacket, red eyes, sharp teeth",
    "lol_kaisa": "Kai'Sa, League of Legends, void, purple suit, cannons on shoulders",
    "lol_evelynn": "Evelynn, League of Legends, demon, succubus, shadow powers, seductive",
    "lol_ahri": "Ahri, League of Legends, vastaya, nine-tailed fox, charming",
    "lol_belveth": "Bel'Veth, League of Legends, empress of the void, manta ray form",
    "lol_fiora": "Fiora, League of Legends, duelist, elegant, swordswoman",
    "lol_gwen": "Gwen, League of Legends, doll, scissors, cheerful",
    "lol_zoe": "Zoe, League of Legends, aspect of twilight, playful, colorful hair",
    "lol_missfortune": "Miss Fortune, League of Legends, bounty hunter, red hair, guns",
    "lol_neeko": "Neeko, League of Legends, chameleon, shapeshifter",
    "lol_samira": "Samira, League of Legends, mercenary, stylish, gunslinger",
    "lol_sona": "Sona, League of Legends, mute musician, ethereal instrument",
    "lol_elise": "Elise, League of Legends, spider queen, dark, seductive",

    "mlp_twilight_sparkle": "Twilight Sparkle, My Little Pony, alicorn, purple body, dark purple mane, star cutie mark",
    "mlp_applejack": "Applejack, My Little Pony, earth pony, orange body, blonde mane, apple cutie mark, cowboy hat",
    "mlp_rainbow_dash": "Rainbow Dash, My Little Pony, pegasus, blue body, rainbow mane, cloud cutie mark, athletic",
    "mlp_rarity": "Rarity, My Little Pony, unicorn, white body, purple mane, diamond cutie mark, fashionista",
    "mlp_fluttershy": "Fluttershy, My Little Pony, pegasus, yellow body, pink mane, butterfly cutie mark, shy",
    "mlp_pinkie_pie": "Pinkie Pie, My Little Pony, earth pony, pink body, dark pink curly mane, balloons cutie mark, cheerful",
    "mlp_spike": "Spike, My Little Pony, dragon, small, purple and green",
    "mlp_princess_celestia": "Princess Celestia, My Little Pony, alicorn, white body, long rainbow mane, sun cutie mark, ruler",
    "mlp_princess_luna": "Princess Luna, My Little Pony, alicorn, dark blue body, translucent mane, moon cutie mark, night ruler",
    "mlp_princess_cadence": "Princess Cadence, My Little Pony, alicorn, pink body, yellow and pink mane, heart cutie mark, love ruler",
    "mlp_discord": "Discord, My Little Pony, draconequus, chaotic, unpredictable",
    "mlp_apple_bloom": "Apple Bloom, My Little Pony, small earth pony, orange body, red bow",
    "mlp_scootaloo": "Scootaloo, My Little Pony, small pegasus, orange body, purple mane",
    "mlp_sweetie_belle": "Sweetie Belle, My Little Pony, small unicorn, white body, pink and purple mane",

    "dislyte_li_ling_f": "Li Ling (female), Dislyte, female version of Li Ling, lightning powers, yellow outfit",
    "dislyte_sally": "Sally, Dislyte, healer, elegant white dress, serene",
    "dislyte_clara": "Clara, Dislyte, healer, bunny ears, cute dress",
    "dislyte_gabrielle": "Gabrielle, Dislyte, warrior, dark armor, wings",
    "dislyte_chloe": "Chloe, Dislyte, fighter, purple hair, casual outfit",
    "dislyte_odette": "Odette, Dislyte, elegant, long hair, musical theme",
    "dislyte_meredith": "Meredith, Dislyte, archer, green outfit, nature theme",
    "dislyte_jiang_man": "Jiang Man, Dislyte, ghost, traditional dress, floating",
    "dislyte_eira": "Eira, Dislyte, ice powers, blue and white outfit",
    "dislyte_drew": "Drew, Dislyte, vampire, dark clothing, seductive",
    "dislyte_pritzker_f": "Pritzker (female), Dislyte, female version of Pritzker, military uniform",
    "dislyte_fatima": "Fatima, Dislyte, fire powers, dancer, vibrant outfit",
    "dislyte_brewster_f": "Brewster (female), Dislyte, female version of Brewster, bounty hunter, guns",
    "dislyte_yun_chuan_f": "Yun Chuan (female), Dislyte, female version of Yun Chuan, elegant, traditional clothes",
    "dislyte_hyde_f": "Hyde (female), Dislyte, female version of Hyde, gothic, dark powers",
    "dislyte_leora": "Leora, Dislyte, sun powers, golden outfit, radiant",
    "dislyte_tevor_f": "Tevor (female), Dislyte, female version of Tevor, archer, wild look",
    "dislyte_zora": "Zora, Dislyte, fire dancer, vibrant red outfit",
    "dislyte_embla": "Embla, Dislyte, dark magic, mysterious, long black hair",
    "dislyte_ophilia": "Ophilia, Dislyte, elegant, light powers, white dress",
    "dislyte_ahmed_f": "Ahmed (female), Dislyte, female version of Ahmed, healer, gentle",
    "dislyte_everett_f": "Everett (female), Dislyte, female version of Everett, strong, protector",
    "dislyte_ollie_f": "Ollie (female), Dislyte, female version of Ollie, playful, skater",
    "dislyte_jin_hee": "Jin Hee, Dislyte, martial artist, red and black outfit",
    "dislyte_ifrit_f": "Ifrit (female), Dislyte, female version of Ifrit, fire demon, powerful",
    "dislyte_sienna": "Сиенна",
    "dislyte_valeria": "Валерия",
    "dislyte_ashley": "Эшли",
    "dislyte_triki_f": "Трики (F)",
    "dislyte_narmer_f": "Нармер (F)",
    "dislyte_tye": "Тай",
    "dislyte_biondina": "Биондина",
    "dislyte_dhalia": "Далия",
    "dislyte_elaine": "Элейн",
    "dislyte_cecilia": "Сесилия",
    "dislyte_intisar": "Интисар",
    "dislyte_kaylee": "Кейли",
    "dislyte_layla": "Лейла",
    "dislyte_lynn": "Линн",
    "dislyte_melanie": "Мелани",
    "dislyte_mona": "Мона",
    "dislyte_nicole": "Николь",
    "dislyte_q": "Кью",
    "dislyte_ren_si": "Жэнь Си",
    "dislyte_stewart_f": "Стюарт (F)",
    "dislyte_tang_xuan_f": "Тан Сюань (F)",
    "dislyte_unaky": "Унаки",
    "dislyte_victoria": "Виктория",
    "dislyte_xiao_yin": "Сяо Инь",
    "dislyte_ye_suhua": "Е Сухуа",
    "dislyte_zhong_nan": "Чжун Нань",
    "dislyte_anadora": "Анадора",
    "dislyte_bernice": "Бернис",
    "dislyte_brynn": "Бринн",
    "dislyte_catherine": "Катерина",
    "dislyte_chang_pu": "Чан Пу",
    "dislyte_eugene_f": "Юджин (F)",
    "dislyte_freddy_f": "Фредди (F)",
    "dislyte_hall_f": "Холл (F)",
    "dislyte_helena": "Хелена",
    "dislyte_jacob_f": "Джейкоб (F)",
    "dislyte_jeanne": "Жанна",
    "dislyte_li_ao_f": "Ли Ао (F)",
    "dislyte_lu_yi_f": "Лу И (F)",
    "dislyte_mark_f": "Марк (F)",
    "dislyte_olivia": "Оливия",
    "dislyte_sander_f": "Сандер (F)",
    "dislyte_stella": "Стелла",
    "dislyte_alice": "Алиса",
    "dislyte_arcana": "Аркана",
    "dislyte_aurelius_f": "Аурелиус (F)",
    "dislyte_bette": "Бетте",
    "dislyte_bonnie": "Бонни",
    "dislyte_celine": "Селин",
    "dislyte_corbin_f": "Корбин (F)",
    },
    "head": {
        "ahegao": "Ахегао",
        "pain_face": "Лицо в боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "fetish": {
        "nipple_piercing": "Пирсинг сосков",
        "clitoral_piercing": "Пирсинг клитора",
        "foot_fetish": "Фетиш стоп",
        "footjob": "Футджоб",
        "mouth_nipples": "Рты вместо сосков",
        "nipple_hole": "Отверстие в соске",
        "anus_piercing": "Пирсинг ануса",
        "vagina_piercing": "Пирсинг вагины",
        "gag": "Кляп",
        "blindfold": "Повязка на глаза",
        "horse_sex": "Секс с конем"
    },
    "pokemon": {
        "reshiram": "Реширам",
        "mew": "Мю",
        "mewtwo": "Мюту",
        "gardevoir": "Гардевуар",
        "umbreon": "Эмбреон",
        "lugia": "Лугия",
        "shadow_lugia": "Шадоу Лугия",
        "lopunny": "Лопанни",
        "goodra": "Гудра",
        "pokemon_jessie": "Джесси",
        "pokemon_lusamine": "Лусамине",
    }
}

# --- Промпты для модели ---
TAG_PROMPTS = {
    **CHARACTER_PROMPTS, # Включаем промпты персонажей
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "dilated anus, anus stretched, open anus, internal view of anus, anus gaping",
    "dilated_vagina": "dilated vagina, vagina stretched, open pussy, internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus",
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo, belly bulge, stomach distended",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "long_dildo_path": (
        "dildo inserted into anus, seamless and continuous dildo, dildo visibly exiting from mouth, "
        "realistic rubber texture, abdomen with a raised, snake-like pattern running along the surface, "
        "or a smooth, continuous raised stripe indicating the dildo's path internally, "
        "skin taut over the shape, subtle undulation suggesting the form beneath the skin"
    ),
    "urethral_dildo": "urethral dildo, dildo in urethra, dildo inserted into urethra",
    "two_dildos_anus_vagina": "one dildo inserted into anus, one dildo inserted into vagina",
    "two_dildos_one_hole": "two dildos, one hole, multiple dildos in one orifice, dildos inserted into same hole", # Updated generic prompt for two dildos in one hole
    "horse_sex": "horse sex, mare, horse cock, equine, intercourse with horse",
    "doggy": "doggy style, on all fours, hands on floor",
    "standing": "standing pose",
    "squat": "squatting pose, hands behind head",
    "lying": "lying down, prone",
    "hor_split": "horizontal split, legs spread wide, extreme flexibility",
    "ver_split": "vertical split, one leg raised high, extreme flexibility",
    "on_back_legs_behind_head": "on back, legs behind head, extreme flexibility, arched back",
    "on_side_leg_up": "on side, one leg straight up, leg lifted high",
    "suspended": "suspended, hanging pose, body floating",
    "front_facing": "front facing, facing viewer, full front view",
    "back_facing": "back facing, from behind, full back view, ass shot",
    "top_down_view": "top down view, from above",
    "bottom_up_view": "bottom up view, from below, looking up at crotch",
    "hands_spreading_vagina": "hands spreading vagina, labia spread by hands, fingers stretching pussy",
    "lotus_pose": "lotus pose, legs crossed, sitting position",
    "scissors_pose": "scissors pose, two girls, legs intertwined, scissoring",
    "inverted_extreme_bridge": "extreme acrobatic pose, deep inversion, bridge pose, shoulder stand, hand support, head touching floor, side-turned head, loose hair on floor, shoulders on surface, elbows bent, hands in front of face, palms on floor, stabilizing hands, extremely arched back, deep back bend, emphasized lumbar curve, high elevated buttocks, buttocks near head level, buttocks facing viewer, legs spread wide, acute angle legs, slightly bent knees, feet touching floor, pointed toes, arched body, flexible, acrobatic",
    "leaning_forward_wall": "half-undressed, leaning forward, hands supporting, head slightly tilted, head turned back to viewer, looking over shoulder, hands on wall, hands on vertical surface, raised shoulders, tense trapezius, straight back, back almost parallel to floor, slight back arch, pushed out buttocks, emphasized buttocks, legs shoulder-width apart, thighs tilted forward, bent knees, relaxed stance",
    "standing_vertical_split_supported": "standing, one leg on floor, other leg extended vertically up, leg almost touching head, both hands supporting raised leg, holding ankle, straight back, tense core muscles, open pelvis, maximum stretch, flexible, acrobatic",
    "boat_pose_double_split_up": "boat pose, both legs raised up 90+ degrees, hands holding both feet, torso leaned back, tense back, balancing, stable pose, static, requires strength, flexible",
    "deep_sumo_squat": "deep squat, knees spread wide, heels on floor, pelvis deep down, hands down for balance, hands on floor for balance, straight spine, raised chest",
    "standing_horizontal_split_balanced": "standing, one leg to side horizontally, hands spread for balance, body strictly vertical, open pelvis, strong balance control, flexible, acrobatic",
    "classic_bridge": "bridge pose, support on palms and feet, body arched upwards, full back arch, stomach facing up, head tilted back, stretched neck, fingers and toes pointed forward",
    "sitting_horizontal_split_supported": "sitting, one leg forward, one leg back, horizontal split, hands on floor for support, torso slightly raised, pelvis low to floor, straight back, elongated neck, flexible",
    "stockings_normal_white": "white stockings only",
    "stockings_normal_black": "black stockings only",
    "stockings_normal_red": "red stockings only",
    "stockings_normal_pink": "pink stockings only",
    "stockings_normal_gold": "gold stockings only",
    "stockings_fishnet_white": "white fishnet stockings",
    "stockings_fishnet_black": "black fishnet stockings",
    "stockings_fishnet_red": "red fishnet stockings",
    "stockings_fishnet_pink": "pink fishnet stockings",
    "stockings_fishnet_gold": "gold fishnet stockings",
    "bikini_tan_lines": "bikini tan lines",
    "shibari": "shibari ropes",
    "cow_costume": "cow costume, cow ears, cow horns, cow tail, wearing stockings only",
    "big_breasts": "big breasts",
    "small_breasts": "small breasts",
    "body_fit": "fit body",
    "body_fat": "curvy body",
    "body_muscular": "muscular body",
    "age_loli": "loli",
    "age_milf": "milf",
    "age_21": "21 year old",
    "cum": "cum covered, messy",
    "belly_bloat": "belly bulge, pregnant looking belly",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "futanari",
    "femboy": "male, boy, very feminine body, femboy, androgynous, flat chest, penis, testicles, thin waist, wide hips, boyish hips, no breasts",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "furry cow girl, cow costume",
    "furry_cat": "furry cat girl, cat costume",
    "furry_dog": "furry dog girl, dog costume",
    "furry_dragon": "furry dragon girl, dragon costume",
    "furry_sylveon": "furry sylveon, sylveon costume, pink, ribbons, sexy",
    "furry_fox": "furry fox girl, fox costume",
    "furry_bunny": "furry bunny girl, bunny costume",
    "furry_wolf": "furry wolf girl, wolf costume",
    "furry_bear": "furry bear girl, bear ears, bear tail",
    "furry_bird": "furry bird girl, bird wings, bird feathers",
    "furry_mouse": "furry mouse girl, mouse ears, mouse tail",
    "furry_deer": "furry deer girl, deer antlers, deer ears, deer tail",
    "furry_tiger": "furry tiger girl, tiger stripes, tiger ears, tiger tail",
    "furry_lion": "furry lion girl, lion mane, lion ears, lion tail",
    "furry_snake": "furry snake girl, snake scales, snake tail, snake eyes",
    "furry_lizard": "furry lizard girl, lizard scales, lizard tail",
    "ahegao": "ahegao face",
    "pain_face": "pain face, grimace",
    "ecstasy_face": "ecstasy face, flushed face, half-closed eyes, open mouth",
    "gold_lipstick": "gold lipstick",
    "nipple_piercing": "nipple piercing",
    "clitoral_piercing": "clitoral piercing",
    "foot_fetish": "foot fetish, detailed feet",
    "footjob": "footjob",
    "mouth_nipples": "mouths instead of nipples",
    "nipple_hole": "nipple hole, hole in nipple",
    "anus_piercing": "anus piercing",
    "vagina_piercing": "vagina piercing",
    "gag": "gag, mouth gag",
    "blindfold": "blindfold",
    "dilated_nipples": "dilated nipples, stretched nipple holes, open nipple holes",
    "anus_spreader_ring": "anus spreader ring, ring holding anus open, anal ring, anus gaping ring",
    "vagina_spreader_ring": "vagina spreader ring, ring holding vagina open, vaginal ring, vagina gaping ring",
    "reshiram": "reshiram, pokemon",
    "mew": "mew, pokemon",
    "mewtwo": "mewtwo, pokemon",
    "gardevoir": "gardevoir, pokemon",
    "umbreon": "umbreon, pokemon",
    "lugia": "lugia, pokemon",
    "shadow_lugia": "shadow lugia, pokemon",
    "lopunny": "lopunny, pokemon",
    "goodra": "goodra, pokemon",
    "pokemon_jessie": "jessie, pokemon, team rocket, red hair, long hair, ponytail",
    "pokemon_lusamine": "lusamine, pokemon, aether foundation, blonde hair, long hair, dress",
    # Новые промпты для поз
    "prone_frog_stretch": "prone frog stretch, chest to floor, hips wide open, splayed thighs, exposed genitals, deep groin stretch, extreme flexibility, inviting pose",
    "standing_deep_forward_bend": "standing deep forward bend, legs wide apart, hands on floor, head dropped between legs, exposed crotch, emphasizing butt, flexible pose",
    "forward_bow_forearms_clasped": "standing deep forward bow, feet close, forearms clasped in front of crotch, hips lifted high, arched back, emphasizing buttocks, submissive pose",
    "top_down_voluminous_bow": "top-down view, deep forward bend, arms forming diamond/heart shape below torso, foreshortened perspective, emphasizes round buttocks, exposed back, inviting from above",
    "inverted_leg_over_shoulder": "supine inverted leg fold, hips lifted high, one leg over shoulder, other leg splayed to side, extreme flexibility, twisted body, exposed vulva/anus, acrobatic",
    "casual_seated_open_knees": "casual seated on floor, knees bent and wide open, legs spread, hands resting on inner thighs, exposed crotch, relaxed and inviting, direct gaze",
}


# --- Функции для создания клавиатур ---

def main_menu():
    """Создает главное меню бота."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def tag_selection_keyboard(category, uid):
    """Создает клавиатуру для выбора тегов в категории."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    current_tags = user_settings.get(uid, {}).get("tags", [])
    
    if category not in TAGS:
        print(f"Error: Category '{category}' not found in TAGS.")
        return kb 
        
    sorted_tags = sorted(TAGS[category].items(), key=lambda item: item[1])

    for tag_key, tag_name_ru in sorted_tags:
        if category == "clothes" and tag_key == "stockings":
            # Специальная кнопка для выбора типа чулок
            kb.add(types.InlineKeyboardButton("Чулки", callback_data="stockings_type_select"))
        else:
            selected = tag_key in current_tags
            prefix = "✅ " if selected else ""
            kb.add(types.InlineKeyboardButton(f"{prefix}{tag_name_ru}", callback_data=f"tag|{tag_key}"))

    kb.add(types.InlineKeyboardButton("⬅️ Назад к категориям", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return kb

def category_menu_keyboard():
    """Создает меню выбора категорий тегов."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"category|{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def character_subcategory_menu_keyboard(uid):
    """Создает меню выбора подкатегорий персонажей."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Сортируем подкатегории по русскоязычному названию
    sorted_char_categories = sorted(CHARACTER_CATEGORIES.items(), key=lambda item: item[1])

    # Определяем, какая подкатегория выбрана, чтобы пометить её
    selected_char_sub_prefix = None
    for tag_key in user_settings.get(uid, {}).get("tags", []):
        for char_prefix in CHARACTER_CATEGORIES.keys():
            if tag_key.startswith(char_prefix + "_"):
                selected_char_sub_prefix = char_prefix
                break
        if selected_char_sub_prefix:
            break

    for key, name in sorted_char_categories:
        label = f"✅ {name}" if selected_char_sub_prefix == key else name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"char_sub|{key}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к категориям", callback_data="choose_tags"))
    return kb

def stockings_type_menu_keyboard(uid):
    """Создает меню выбора типа чулок."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    types_map = {"normal": "Обычные", "fishnet": "В сеточку"}
    current_tags = user_settings.get(uid, {}).get("tags", [])

    for type_key, type_name in types_map.items():
        # Check if any stockings of this type are selected
        selected = any(f"stockings_{type_key}_{color}" in current_tags for color in ["white", "black", "red", "pink", "gold"])
        label = f"✅ {type_name}" if selected else type_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"stockings_type|{type_key}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к категории 'Одежда'", callback_data="category|clothes"))
    return kb

def stockings_color_menu_keyboard(stockings_type, uid):
    """Создает меню выбора цвета чулок."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    colors = {"white": "Белые", "black": "Черные", "red": "Красные", "pink": "Розовые", "gold": "Золотые"}
    current_tags = user_settings.get(uid, {}).get("tags", [])

    for color_key, color_name in colors.items():
        tag_key = f"stockings_{stockings_type}_{color_key}"
        label = f"✅ {color_name}" if tag_key in current_tags else color_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag|{tag_key}"))
    
    kb.add(types.InlineKeyboardButton("⬅️ Назад к типам чулок", callback_data="stockings_type_select"))
    return kb

def settings_menu_keyboard(current_num_images):
    """Создает меню настроек."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(f"Количество изображений: {current_num_images}", callback_data="ignore"))
    kb.add(types.InlineKeyboardButton("1", callback_data="set_num_images|1"))
    kb.add(types.InlineKeyboardButton("2", callback_data="set_num_images|2"))
    kb.add(types.InlineKeyboardButton("3", callback_data="set_num_images|3"))
    kb.add(types.InlineKeyboardButton("4", callback_data="set_num_images|4"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
    return kb

# --- Обработчики сообщений и колбэков ---

@bot.message_handler(commands=["start"])
def start_command_handler(msg):
    """Обработчик команды /start."""
    uid = msg.chat.id
    user_settings[uid] = {"tags": [], "current_category": None, "current_char_subcategory": None, "current_stockings_type": None, "num_images": 1}
    bot.send_message(uid, "Привет, Шеф! Я готов к работе. Что будем генерировать?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик всех кнопок колбэка."""
    uid = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    # Инициализация настроек пользователя, если их нет
    user_settings.setdefault(uid, {"tags": [], "current_category": None, "current_char_subcategory": None, "current_stockings_type": None, "num_images": 1})

    if data == "main_menu":
        bot.edit_message_text("Главное меню:", uid, message_id, reply_markup=main_menu())
        user_settings[uid]["current_category"] = None
        user_settings[uid]["current_char_subcategory"] = None
        user_settings[uid]["current_stockings_type"] = None
    elif data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", uid, message_id, reply_markup=category_menu_keyboard())
    elif data.startswith("category|"):
        category = data.split("|")[1]
        user_settings[uid]["current_category"] = category
        user_settings[uid]["current_char_subcategory"] = None # Сбрасываем подкатегорию персонажей
        user_settings[uid]["current_stockings_type"] = None # Сбрасываем тип чулок

        if category == "characters":
            bot.edit_message_text("Выбери подкатегорию персонажей:", uid, message_id, reply_markup=character_subcategory_menu_keyboard(uid))
        elif category == "clothes":
            bot.edit_message_text("Выбери тип чулок:", uid, message_id, reply_markup=stockings_type_menu_keyboard(uid))
        else:
            bot.edit_message_text(f"Категория: {CATEGORY_NAMES.get(category, category)}", uid, message_id, reply_markup=tag_selection_keyboard(category, uid))
    elif data.startswith("char_sub|"):
        char_sub = data.split("|")[1]
        user_settings[uid]["current_char_subcategory"] = char_sub
        
        # Фильтруем теги, чтобы показывать только теги из этой подкатегории
        # и сортируем их по русскоязычному названию
        filtered_tags = {k: v for k, v in TAGS["characters"].items() if k.startswith(char_sub + "_")}
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        current_tags = user_settings.get(uid, {}).get("tags", [])
        
        # Сначала добавляем теги выбранной подкатегории персонажей
        for tag_key, tag_name_ru in sorted(filtered_tags.items(), key=lambda item: item[1]):
            selected = tag_key in current_tags
            prefix = "✅ " if selected else ""
            kb.add(types.InlineKeyboardButton(f"{prefix}{tag_name_ru}", callback_data=f"tag|{tag_key}"))
        
        kb.add(types.InlineKeyboardButton("⬅️ К подкатегориям", callback_data="category|characters"))
        kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        bot.edit_message_text(f"Подкатегория: {CHARACTER_CATEGORIES.get(char_sub, char_sub)}", uid, message_id, reply_markup=kb)
    elif data == "stockings_type_select":
        bot.edit_message_text("Выбери тип чулок:", uid, message_id, reply_markup=stockings_type_menu_keyboard(uid))
    elif data.startswith("stockings_type|"):
        st_type = data.split("|")[1]
        user_settings[uid]["current_stockings_type"] = st_type
        bot.edit_message_text("Выбери цвет чулок:", uid, message_id, reply_markup=stockings_color_menu_keyboard(st_type, uid))
    elif data.startswith("tag|"):
        tag_key = data.split("|")[1]
        current_tags = user_settings[uid]["tags"]

        if tag_key.startswith("stockings_"):
            # Удаляем все _другие_ теги чулок перед добавлением/удалением текущего
            current_tags[:] = [t for t in current_tags if not t.startswith("stockings_") or t == tag_key]
            
            if tag_key in current_tags:
                current_tags.remove(tag_key)
            else:
                current_tags.append(tag_key)
            
            stockings_type = user_settings[uid].get("current_stockings_type")
            if stockings_type:
                bot.edit_message_reply_markup(chat_id=uid, message_id=message_id, reply_markup=stockings_color_menu_keyboard(stockings_type, uid))
            else: # Fallback to stockings type select if type is somehow lost
                bot.edit_message_reply_markup(chat_id=uid, message_id=message_id, reply_markup=stockings_type_menu_keyboard(uid))
        else: # Для обычных тегов
            if tag_key in current_tags:
                current_tags.remove(tag_key)
            else:
                current_tags.append(tag_key)
            
            # Обновляем клавиатуру, показывая выбранные/невыбранные теги
            current_cat = user_settings[uid].get("current_category")
            current_char_sub = user_settings[uid].get("current_char_subcategory")

            if current_cat == "characters" and current_char_sub:
                # Пересоздаем клавиатуру для подкатегории персонажей
                filtered_tags = {k: v for k, v in TAGS["characters"].items() if k.startswith(current_char_sub + "_")}
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tk, tn in sorted(filtered_tags.items(), key=lambda item: item[1]):
                    selected = tk in current_tags
                    prefix = "✅ " if selected else ""
                    kb.add(types.InlineKeyboardButton(f"{prefix}{tn}", callback_data=f"tag|{tk}"))
                kb.add(types.InlineKeyboardButton("⬅️ К подкатегориям", callback_data="category|characters"))
                kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
                bot.edit_message_reply_markup(chat_id=uid, message_id=message_id, reply_markup=kb)
            elif current_cat and current_cat != "characters" and current_cat != "clothes":
                 # Обновляем для обычной категории (кроме персонажей и одежды, т.к. они имеют подменю)
                bot.edit_message_reply_markup(chat_id=uid, message_id=message_id, reply_markup=tag_selection_keyboard(current_cat, uid))
            elif current_cat == "clothes" and not user_settings[uid].get("current_stockings_type"):
                # Если вдруг мы в одежде, но не в чулках, то возвращаемся к меню одежды
                bot.edit_message_reply_markup(chat_id=uid, message_id=message_id, reply_markup=tag_selection_keyboard("clothes", uid))


    elif data == "done_tags":
        selected_tags = user_settings.get(uid, {}).get("tags", [])
        if not selected_tags:
            bot.send_message(uid, "Вы не выбрали ни одного тега.")
            bot.edit_message_text("Главное меню:", uid, message_id, reply_markup=main_menu())
            return
        
        display_tags = []
        for tag_key in selected_tags:
            found = False
            for cat_tags in TAGS.values():
                if tag_key in cat_tags:
                    display_tags.append(cat_tags[tag_key])
                    found = True
                    break
            
            if not found and tag_key.startswith("stockings_"):
                parts = tag_key.split('_')
                if len(parts) == 3: 
                    sock_type_name = "Обычные чулки" if parts[1] == "normal" else "Чулки в сеточку"
                    color_name = {"white": "Белые", "black": "Черные", "red": "Красные", "pink": "Розовые", "gold": "Золотые"}.get(parts[2], parts[2])
                    display_tags.append(f"{sock_type_name} {color_name}")
                else:
                    display_tags.append(tag_key) 
                found = True 
            elif not found:
                display_tags.append(tag_key) 
        
        tag_list = "\n".join(f"• {tag}" for tag in display_tags)
        bot.edit_message_text(f"Вы выбрали:\n\n{tag_list}\n\nТеперь можно сгенерировать изображение.", uid, message_id, reply_markup=types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate")],
            [types.InlineKeyboardButton("⬅️ Изменить теги", callback_data="choose_tags")],
            [types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]))
    elif data == "generate":
        selected_tags = user_settings.get(uid, {}).get("tags", [])
        if not selected_tags:
            bot.send_message(uid, "Сначала выбери теги!")
            return

        user_settings[uid]["last_prompt_tags"] = selected_tags.copy()

        prompt_info = build_prompt(selected_tags)
        positive_prompt = prompt_info["positive_prompt"]
        negative_prompt = prompt_info["negative_prompt"]
        num_images = user_settings[uid].get("num_images", 1)

        bot.edit_message_text("Принято Шеф, приступаю к генерации! Это может занять до минуты...", uid, message_id)

        try:
            generated_urls = replicate_generate(positive_prompt, negative_prompt, num_images)
            if generated_urls:
                media_group = []
                for url in generated_urls:
                    media_group.append(types.InputMediaPhoto(url))
                
                kb = types.InlineKeyboardMarkup()
                kb.add(
                    types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_new_session"),
                    types.InlineKeyboardButton("🎨 Новый запрос", callback_data="choose_tags"),
                    types.InlineKeyboardButton("➡️ Продолжить с этими", callback_data="generate")
                )
                bot.send_media_group(uid, media_group)
                bot.send_message(uid, "✅ Готово!", reply_markup=kb)
            else:
                bot.send_message(uid, "❌ Ошибка генерации. Пожалуйста, попробуйте еще раз.")
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            bot.send_message(uid, f"Произошла ошибка во время генерации. Пожалуйста, попробуйте еще раз. Ошибка: {e}")

    elif data == "settings":
        current_num_images = user_settings[uid].get("num_images", 1)
        bot.edit_message_text(f"Настройки генерации:", uid, message_id, reply_markup=settings_menu_keyboard(current_num_images))
    elif data.startswith("set_num_images|"):
        num = int(data.split("|")[-1])
        user_settings[uid]["num_images"] = num
        current_num_images = user_settings[uid].get("num_images", 1)
        bot.edit_message_text(f"Настройки генерации: количество изображений установлено на {num}.", uid, message_id, reply_markup=settings_menu_keyboard(current_num_images))
    elif data == "start_new_session":
        start_command_handler(call.message)
    elif data == "ignore":
        bot.answer_callback_query(call.id)


# --- Функция для определения категории тега ---
def tag_category(tag):
    """Определяет категорию, к которой относится тег."""
    for cat, items in TAGS.items():
        if tag in items:
            return cat 
    if tag.startswith("stockings_"):
        return "clothes"
    for char_cat_prefix in CHARACTER_CATEGORIES.keys():
        if tag.startswith(char_cat_prefix + "_"):
            return "characters"
    return None


# --- Оптимизированная функция для построения промпта ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов,
    используя оптимальные настройки для достижения максимальной точности.
    """
    base = [
        "masterpiece", "best quality", "ultra detailed", "anime style", "highly detailed",
        "expressive eyes", "perfect lighting", "volumetric lighting", "fully nude", "solo"
    ]

    priority = {
        "characters": [],
        "furry": [],
        "pokemon": [],
        "body": [],
        "poses": [],
        "holes": [],
        "toys": [],
        "clothes": [],
        "fetish": [],
        "head": [],
        "ethnos": []
    }
    
    base_negative = [
        "lowres, bad anatomy, bad hands, bad face, deformed, disfigured, poorly drawn, ",
        "missing limbs, extra limbs, fused fingers, jpeg artifacts, signature, watermark",
        "blurry, cropped, worst quality, low quality, text, error, mutated, censored, ",
        "hands on chest, hands covering breasts, clothing covering genitals, shirt, bra, bikini, ",
        "vagina not visible, anus not visible, penis not visible, bad proportions, ",
        "all clothes, all clothing"
    ]
    negative_prompt_str = "".join(base_negative)


    unique_tags = set(tags) 
    
    if "big_breasts" in unique_tags and "small_breasts" in unique_tags:
        unique_tags.remove("small_breasts") 
    
    if "furry_cow" in unique_tags:
        unique_tags.discard("cow_costume") 

    character_tags_count = 0
    # Проверяем количество выбранных персонажей
    for tag in unique_tags:
        if tag_category(tag) == "characters" and tag in CHARACTER_PROMPTS:
            character_tags_count += 1
    
    if character_tags_count > 1:
        base.insert(0, f"{character_tags_count}girls")
    elif character_tags_count == 1:
        base.insert(0, "1girl")
    # Добавляем "1girl" только если нет персонажей, фури, покемонов и не выбран "femboy"
    elif not any(tag_category(t) in ["characters", "furry", "pokemon"] for t in unique_tags) and "femboy" not in unique_tags:
         base.insert(0, "1girl")


    for tag in unique_tags:
        prompt_value = TAG_PROMPTS.get(tag)
        if prompt_value:
            cat = tag_category(tag)
            if cat in priority:
                priority[cat].append(prompt_value)
            else:
                base.append(prompt_value)
        else:
            found_in_tags_dict = False
            for cat_key, cat_items in TAGS.items():
                if tag in cat_items:
                    cat = tag_category(tag)
                    if cat in priority:
                        priority[cat].append(tag) 
                    else:
                        base.append(tag)
                    found_in_tags_dict = True
                    break
            if not found_in_tags_dict:
                print(f"Warning: Tag '{tag}' found in selected_tags but no prompt defined for it and not found as a direct key in TAGS.")


    # --- Логика для "two_dildos_one_hole" ---
    if "two_dildos_one_hole" in unique_tags:
        # Убедимся, что общий промпт "two dildos, one hole..." добавлен только один раз
        if TAG_PROMPTS["two_dildos_one_hole"] not in priority["toys"]: # Используем прямо TAG_PROMPTS
            priority["toys"].append(TAG_PROMPTS["two_dildos_one_hole"])

        hole_specific_prompts = []
        if "vagina" in unique_tags:
            hole_specific_prompts.append("two dildos in vagina")
            priority["holes"] = [p for p in priority["holes"] if p != TAG_PROMPTS["vagina"]] 
        if "anus" in unique_tags:
            hole_specific_prompts.append("two dildos in anus")
            priority["holes"] = [p for p in priority["holes"] if p != TAG_PROMPTS["anus"]] 
        if "both" in unique_tags:
            hole_specific_prompts.append("two dildos in vagina, two dildos in anus")
            priority["holes"] = [p for p in priority["holes"] if p != TAG_PROMPTS["both"]] 
        if "dilated_vagina" in unique_tags:
            hole_specific_prompts.append("two dildos in dilated vagina")
            priority["holes"] = [p for p in priority["holes"] if p != TAG_PROMPTS["dilated_vagina"]]
        if "dilated_anus" in unique_tags:
            hole_specific_prompts.append("two dildos in dilated anus")
            priority["holes"] = [p for p in priority["holes"] if p != TAG_PROMPTS["dilated_anus"]]
        
        priority["toys"].extend(hole_specific_prompts)


    prompt_parts = base[:]
    for section in ["characters", "furry", "pokemon", "body", "poses", "holes", "toys", "clothes", "fetish", "head", "ethnos"]:
        prompt_parts.extend(priority[section])

    if "bikini_tan_lines" in unique_tags:
        negative_prompt_str = negative_prompt_str.replace("bikini, ", "").replace("bikini", "")

    return {
        "positive_prompt": ", ".join(filter(None, prompt_parts)), 
        "negative_prompt": negative_prompt_str
    } 

# --- Функция для генерации изображения через Replicate ---
class Model: 
    def predict(self, prompt, negative_prompt, num_images):
        return replicate_generate(prompt, negative_prompt, num_images)

model = Model() 

def replicate_generate(positive_prompt, negative_prompt, num_images=1):
    """
    Отправляет запрос на генерацию изображения в Replicate API,
    используя оптимальные настройки для достижения максимальной точности.
    """
    urls = []
    for _ in range(num_images):
        url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        }
        json_data = {
            "version": REPLICATE_MODEL,
            "input": {
                "prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "prepend_preprompt": False,
                "width": 1024,
                "height": 1024,
                "steps": 75,
                "guidance_scale": 18,
                "scheduler": "DPM++ 2M SDE Karras",
                "adetailer_face": True,
                "adetailer_hand": True,
                "seed": -1 
            }
        }

        # Отправка запроса на создание предсказания
        try:
            r = requests.post(url, headers=headers, json=json_data)
            r.raise_for_status() # Вызовет исключение для статусов 4xx/5xx
        except requests.exceptions.RequestException as e:
            print(f"Error sending prediction request: {e}")
            print(f"Request JSON: {json_data}")
            return None

        status_url = r.json()["urls"]["get"]

        for i in range(90):
            time.sleep(2)
            try:
                r = requests.get(status_url, headers=headers)
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error getting prediction status: {e}")
                return None
            
            data = r.json()
            if data["status"] == "succeeded":
                if isinstance(data["output"], list) and data["output"]:
                    urls.append(data["output"][0])
                    break
                else:
                    print("Received empty or invalid 'output' from Replicate.")
                    return None
            elif data["status"] == "failed":
                print(f"Prediction failed: {data.get('error', 'Error message not provided')}")
                print(f"Request JSON: {json_data}")
                return None
        else:
            print("Prediction timed out for one image.")
            return None

    return urls


# --- Настройка Flask webhook ---
@app.route("/", methods=["POST"])
def webhook():
    """Обрабатывает входящие обновления от Telegram."""
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    
    # Инициализируем user_settings для нового пользователя, если он отсутствует
    if update.message and update.message.chat.id not in user_settings:
        user_settings[update.message.chat.id] = {"tags": [], "current_category": None, "current_char_subcategory": None, "current_stockings_type": None, "num_images": 1}

    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    """Простой маршрут для проверки работы приложения."""
    return "бот работает", 200

# --- Запуск бота ---
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)

