import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

# Получение токенов и URL из переменных окружения
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

# ID новой модели Replicate, которую вы используете
REPLICATE_MODEL = "80441e2c32a55f2fcf9b77fa0a74c6c86ad7deac51eed722b9faedb253265cb4"

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей

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
        "two_dildos_one_hole": "Два дилдо в одно отверстие",
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
        "two_dildos_anus_vagina": "Дилдо в анусе и вагине"
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
        "inverted_extreme_bridge": "Экстремальный мост/стойка на плечах с инверсией", # NEW POSE
        "leaning_forward_wall": "Наклон вперёд у стены", # NEW POSE
        "standing_vertical_split_supported": "Вертикальный шпагат стоя с поддержкой", # NEW POSE
        "boat_pose_double_split_up": "Поза лодки / двойной шпагат вверх", # NEW POSE
        "deep_sumo_squat": "Глубокий присед (сумо-поза)", # NEW POSE
        "standing_horizontal_split_balanced": "Горизонтальный шпагат стоя с балансом", # NEW POSE
        "classic_bridge": "Мостик", # NEW POSE
        "sitting_horizontal_split_supported": "Горизонтальный шпагат сидя с опорой" # NEW POSE
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
        "genshin_ar_traveler_f": "Аether (F)", # Female Traveler (Aether)
        "genshin_lumine": "Люмин", # Lumine (Female Traveler)
        "genshin_signora": "Синьора",
        "genshin_arlecchino": "Арлекино",
        "genshin_snezhnaya_fatui_harbinger": "Предвестник Фатуи", # Generic female Fatui Harbinger

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
        "hsr_stelle": "Стелла (F)", # Female Trailblazer
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
        "hsr_hanabi": "Ханами", # Sparkle alternative name
        "hsr_robin": "Робин",
        "hsr_aventurine_f": "Авантюрин (F)", # Female Aventurine

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
        "zzz_lycaon": "Ликаон (F)", # Female Lycaon
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
        "dislyte_li_ling_f": "Ли Лин (F)", # Female Li Ling
        "dislyte_sally": "Салли",
        "dislyte_clara": "Клара",
        "dislyte_gabrielle": "Габриэль",
        "dislyte_chloe": "Хлоя",
        "dislyte_odette": "Одетта",
        "dislyte_meredith": "Мередит",
        "dislyte_jiang_man": "Цзян Мань",
        "dislyte_eira": "Эйра",
        "dislyte_drew": "Дрю",
        "dislyte_pritzker_f": "Притцкер (F)", # Female Pritzker
        "dislyte_fatima": "Фатима",
        "dislyte_brewster_f": "Брюстер (F)", # Female Brewster
        "dislyte_yun_chuan_f": "Юнь Чуань (F)", # Female Yun Chuan
        "dislyte_hyde_f": "Хайд (F)", # Female Hyde
        "dislyte_leora": "Леора",
        "dislyte_tevor_f": "Тевор (F)", # Female Tevor
        "dislyte_zora": "Зора",
        "dislyte_embla": "Эмбла",
        "dislyte_ophilia": "Офелия",
        "dislyte_ahmed_f": "Ахмед (F)", # Female Ahmed
        "dislyte_everett_f": "Эверетт (F)", # Female Everett
        "dislyte_ollie_f": "Олли (F)", # Female Ollie
        "dislyte_jin_hee": "Джин Хи",
        "dislyte_ifrit_f": "Ифрит (F)", # Female Ifrit
        "dislyte_sienna": "Сиенна",
        "dislyte_valeria": "Валерия",
        "dislyte_ashley": "Эшли",
        "dislyte_triki_f": "Трики (F)", # Female Triki
        "dislyte_narmer_f": "Нармер (F)", # Female Narmer
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
        "dislyte_stewart_f": "Стюарт (F)", # Female Stewart
        "dislyte_tang_xuan_f": "Тан Сюань (F)", # Female Tang Xuan
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
    "head": { # Category added earlier, ensuring it's in TAGS
        "ahegao": "Ахегао",
        "pain_face": "Лицо в боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "fetish": { # Category added earlier, ensuring it's in TAGS
        "nipple_piercing": "Пирсинг сосков",
        "clitoral_piercing": "Пирсинг клитора",
        "foot_fetish": "Фетиш стоп",
        "footjob": "Футджоб",
        "mouth_nipples": "Рты вместо сосков",
        "nipple_hole": "Отверстие в соске",
        "anus_piercing": "Пирсинг ануса",
        "vagina_piercing": "Пирсинг вагины",
        "gag": "Кляп",
        "blindfold": "Повязка на глаза"
    },
    "pokemon": { # Перенесено из characters
        "reshiram": "Реширам",
        "mew": "Мю",
        "mewtwo": "Мюту",
        "gardevoir": "Гардевуар",
        "umbreon": "Эмбреон",
        "lugia": "Лугия",
        "shadow_lugia": "Шадоу Лугия",
        "lopunny": "Лопанни",
        "goodra": "Гудра",
        "pokemon_jessie": "Джесси", # Moved from characters
        "pokemon_lusamine": "Лусамине", # Moved from characters
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

# --- Промпты для модели ---
TAG_PROMPTS = {
    **CHARACTER_EXTRA, # Включаем промпты персонажей
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "dilated anus, anus stretched, open anus, internal view of anus, anus gaping",
    "dilated_vagina": "dilated vagina, vagina stretched, open pussy, internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus",
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",
    "two_dildos_one_hole": "two dildos, one hole, multiple dildos in one orifice, dildos inserted into same hole", # Corrected
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo, belly bulge, stomach distended", # Added belly bulge
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "long_dildo_path": (
        "dildo inserted into anus, dildo visibly pushing through intestines, belly bulge, stomach distended, "
        "dildo exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber" # Improved
    ),
    "urethral_dildo": "urethral dildo, dildo in urethra, dildo inserted into urethra",
    "two_dildos_anus_vagina": "one dildo inserted into anus, one dildo inserted into vagina",
    "horse_sex": "horse sex, mare, horse cock, equine, intercourse with horse", # NEW
    "doggy": "doggy style, on all fours, hands on floor",
    "squat": "squatting pose, hands behind head",
    "lying": "lying down",
    "lotus_pose": "lotus pose, legs crossed, sitting position",
    "scissors_pose": "scissors pose, two girls, legs intertwined, scissoring",
    "inverted_extreme_bridge": "extreme acrobatic pose, deep inversion, bridge pose, shoulder stand, hand support, head touching floor, side-turned head, loose hair on floor, shoulders on surface, elbows bent, hands in front of face, palms on floor, stabilizing hands, extremely arched back, deep back bend, emphasized lumbar curve, high elevated buttocks, buttocks near head level, buttocks facing viewer, legs spread wide, acute angle legs, slightly bent knees, feet touching floor, pointed toes, arched body, flexible, acrobatic", # NEW POSE PROMPT
    "leaning_forward_wall": "half-undressed, leaning forward, hands supporting, head slightly tilted, head turned back to viewer, looking over shoulder, hands on wall, hands on vertical surface, raised shoulders, tense trapezius, straight back, back almost parallel to floor, slight back arch, pushed out buttocks, emphasized buttocks, legs shoulder-width apart, thighs tilted forward, bent knees, relaxed stance", # NEW POSE PROMPT
    "standing_vertical_split_supported": "standing, one leg on floor, other leg extended vertically up, leg almost touching head, both hands supporting raised leg, holding ankle, straight back, tense core muscles, open pelvis, maximum stretch, flexible, acrobatic", # NEW POSE PROMPT
    "boat_pose_double_split_up": "sitting pose, both legs raised up 90+ degrees, hands holding both feet, torso leaned back, tense back, balancing, stable pose, static, requires strength, flexible", # NEW POSE PROMPT
    "deep_sumo_squat": "deep squat, knees spread wide, heels on floor, pelvis deep down, hands down for balance, hands on floor for balance, straight spine, raised chest", # NEW POSE PROMPT
    "standing_horizontal_split_balanced": "standing, one leg to side horizontally, hands spread for balance, body strictly vertical, open pelvis, strong balance control, flexible, acrobatic", # NEW POSE PROMPT
    "classic_bridge": "bridge pose, support on palms and feet, body arched upwards, full back arch, stomach facing up, head tilted back, stretched neck, fingers and toes pointed forward", # NEW POSE PROMPT
    "sitting_horizontal_split_supported": "sitting, one leg forward, one leg back, horizontal split, hands on floor for support, torso slightly raised, pelvis low to floor, straight back, elongated neck, flexible", # NEW POSE PROMPT
    "stockings_white": "white stockings only",
    "stockings_black": "black stockings only",
    "stockings_red": "red stockings only",
    "stockings_pink": "pink stockings only",
    "stockings_gold": "gold stockings only",
    "stockings_fishnet_white": "white fishnet stockings", # Modified for subcategory
    "stockings_fishnet_black": "black fishnet stockings", # Modified for subcategory
    "stockings_fishnet_red": "red fishnet stockings", # Modified for subcategory
    "stockings_fishnet_pink": "pink fishnet stockings", # Modified for subcategory
    "stockings_fishnet_gold": "gold fishnet stockings", # Modified for subcategory
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
    "age_21": "21 год",
    "cum": "cum covered",
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
    "pain_face": "face in pain",
    "ecstasy_face": "ecstasy face",
    "gold_lipstick": "gold lipstick",
    "nipple_piercing": "nipple piercing",
    "clitoral_piercing": "clitoral piercing",
    "foot_fetish": "foot fetish",
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
    "pokemon_jessie": "jessie, pokemon, team rocket, red hair, long hair, ponytail", # Moved
    "pokemon_lusamine": "lusamine, pokemon, aether foundation, blonde hair, long hair, dress", # Moved
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

# --- Функции для создания клавиатур ---
def main_menu():
    """Создает главное меню бота."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    """Создает меню выбора категорий тегов."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def character_subcategory_menu(selected_tags):
    """Создает меню выбора подкатегорий персонажей."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CHARACTER_CATEGORIES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"char_sub_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def stockings_type_menu(selected_tags):
    """Создает меню выбора типа чулок."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("Обычные чулки", callback_data="stockings_type_normal"))
    kb.add(types.InlineKeyboardButton("Чулки в сеточку", callback_data="stockings_type_fishnet"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def stockings_color_menu(stockings_type, selected_tags):
    """Создает меню выбора цвета чулок."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    colors = {"white": "Белые", "black": "Черные", "red": "Красные", "pink": "Розовые", "gold": "Золотые"}
    for color_key, color_name in colors.items():
        tag_key = f"stockings_{stockings_type}_{color_key}"
        label = f"✅ {color_name}" if tag_key in selected_tags else color_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_clothes_{tag_key}"))
    
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_stockings_type"))
    return kb

def tag_menu(category, selected_tags, char_subcategory=None):
    """Создает меню выбора тегов внутри определенной категории."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    tags_to_display = {}
    if category == "characters" and char_subcategory:
        # Фильтруем теги персонажей по выбранной подкатегории
        for tag_key, tag_name in TAGS[category].items():
            # Префикс подкатегории должен соответствовать началу ключа тега
            if tag_key.startswith(char_subcategory + "_"):
                tags_to_display[tag_key] = tag_name
    elif category == "clothes" and "stockings" in TAGS[category]: # Handle stockings subcategory
        # If stockings is a subcategory, we don't display it here directly
        for tag_key, tag_name in TAGS[category].items():
            if tag_key != "stockings": # Exclude the stockings subcategory trigger
                tags_to_display[tag_key] = tag_name
        # Add a button for stockings subcategory
        kb.add(types.InlineKeyboardButton("Чулки", callback_data="stockings_type_select"))
    else:
        tags_to_display = TAGS[category]

    for tag_key, tag_name in tags_to_display.items():
        # Skip stockings related tags if we are in the main clothes menu
        if category == "clothes" and (tag_key.startswith("stockings_") and tag_key != "stockings"):
            continue

        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    
    if category == "characters":
        kb.add(types.InlineKeyboardButton("⬅ К подкатегориям", callback_data="back_to_char_sub"))
    else:
        kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def settings_menu(current_num_images):
    """Создает меню настроек."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(f"Количество изображений: {current_num_images}", callback_data="ignore"))
    kb.add(types.InlineKeyboardButton("1", callback_data="set_num_images_1"))
    kb.add(types.InlineKeyboardButton("2", callback_data="set_num_images_2"))
    kb.add(types.InlineKeyboardButton("3", callback_data="set_num_images_3"))
    kb.add(types.InlineKeyboardButton("4", callback_data="set_num_images_4"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main"))
    return kb

# --- Обработчики сообщений и колбэков ---
@bot.message_handler(commands=["start"])
def start(msg):
    """Обработчик команды /start."""
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "stockings_type": None, "num_images": 1} # Добавлено stockings_type
    bot.send_message(cid, "Привет Шеф!", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Общий обработчик для всех кнопок колбэка."""
    cid = call.message.chat.id
    message_id = call.message.message_id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "stockings_type": None, "num_images": 1}

    data = call.data

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, message_id, reply_markup=category_menu())

    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        selected = user_settings[cid]["tags"]
        
        if cat == "characters":
            user_settings[cid]["last_char_sub"] = None 
            bot.edit_message_text("Выбери подкатегорию персонажей:", cid, message_id, reply_markup=character_subcategory_menu(selected))
        elif cat == "clothes":
            bot.edit_message_text("Категория: Одежда", cid, message_id, reply_markup=tag_menu(cat, selected))
        else:
            category_display_name = CATEGORY_NAMES.get(cat, cat)
            bot.edit_message_text(f"Категория: {category_display_name}", cid, message_id, reply_markup=tag_menu(cat, selected))

    elif data == "stockings_type_select":
        bot.edit_message_text("Выбери тип чулок:", cid, message_id, reply_markup=stockings_type_menu(user_settings[cid]["tags"]))

    elif data.startswith("stockings_type_"):
        stockings_type = data[len("stockings_type_"):]
        user_settings[cid]["stockings_type"] = stockings_type
        bot.edit_message_text("Выбери цвет чулок:", cid, message_id, reply_markup=stockings_color_menu(stockings_type, user_settings[cid]["tags"]))

    elif data == "back_to_stockings_type":
        bot.edit_message_text("Выбери тип чулок:", cid, message_id, reply_markup=stockings_type_menu(user_settings[cid]["tags"]))

    elif data.startswith("char_sub_"):
        char_sub = data[9:]
        user_settings[cid]["last_char_sub"] = char_sub
        selected = user_settings[cid]["tags"]
        subcategory_display_name = CHARACTER_CATEGORIES.get(char_sub, char_sub)
        bot.edit_message_text(f"Подкатегория: {subcategory_display_name}", cid, message_id, reply_markup=tag_menu("characters", selected, char_sub))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]

        # Special handling for stockings to remove conflicting tags
        if tag.startswith("stockings_"):
            # Remove any existing stockings tags before adding the new one
            tags_to_remove = [t for t in tags if t.startswith("stockings_")]
            for t_rem in tags_to_remove:
                tags.remove(t_rem)
            
            if tag not in tags: # Add the new stockings tag
                tags.append(tag)
            
            # Update the menu for stockings color selection
            stockings_type = user_settings[cid]["stockings_type"]
            bot.edit_message_reply_markup(cid, message_id, reply_markup=stockings_color_menu(stockings_type, tags))
            return # Exit to prevent re-rendering the main tag menu

        # General tag handling
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        
        current_char_sub = user_settings[cid].get("last_char_sub") if cat == "characters" else None
        bot.edit_message_reply_markup(cid, message_id, reply_markup=tag_menu(cat, tags, current_char_sub))

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, message_id, reply_markup=main_menu())

    elif data == "back_to_cat":
        if user_settings[cid].get("last_cat") == "characters" and user_settings[cid].get("last_char_sub"):
            user_settings[cid]["last_char_sub"] = None
            bot.edit_message_text("Выбери подкатегорию персонажей:", cid, message_id, reply_markup=character_subcategory_menu(user_settings[cid]["tags"]))
        else:
            bot.edit_message_text("Выбери категорию:", cid, message_id, reply_markup=category_menu())
    
    elif data == "back_to_char_sub":
        user_settings[cid]["last_char_sub"] = None
        bot.edit_message_text("Выбери подкатегорию персонажей:", cid, message_id, reply_markup=character_subcategory_menu(user_settings[cid]["tags"]))

    elif data == "settings":
        current_num_images = user_settings[cid].get("num_images", 1)
        bot.edit_message_text(f"Настройки генерации:", cid, message_id, reply_markup=settings_menu(current_num_images))
    
    elif data.startswith("set_num_images_"):
        num = int(data.split("_")[-1])
        user_settings[cid]["num_images"] = num
        current_num_images = user_settings[cid].get("num_images", 1)
        bot.edit_message_text(f"Настройки генерации: количество изображений установлено на {num}.", cid, message_id, reply_markup=settings_menu(current_num_images))

    elif data == "back_to_main":
        bot.edit_message_text("Главное меню:", cid, message_id, reply_markup=main_menu())

    elif data == "generate":
        tags = user_settings[cid]["tags"]
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return

        prompt_info = build_prompt(tags)
        positive_prompt = prompt_info["positive_prompt"]
        negative_prompt = prompt_info["negative_prompt"]
        num_images = user_settings[cid].get("num_images", 1)
        
        user_settings[cid]["last_prompt_tags"] = tags.copy()

        bot.send_message(cid, "Принято Шеф, приступаю!")

        generated_urls = replicate_generate(positive_prompt, negative_prompt, num_images)
        if generated_urls:
            media_group = []
            for url in generated_urls:
                media_group.append(types.InputMediaPhoto(url))
            
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            bot.send_media_group(cid, media_group)
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации. Пожалуйста, попробуйте еще раз.")

    elif data == "edit_tags":
        if "last_prompt_tags" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt_tags"]
            bot.send_message(cid, "Изменяем теги, использованные в предыдущей генерации:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов с предыдущей генерации. Сначала сделай генерацию.")

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "stockings_type": None, "num_images": 1}
        bot.send_message(cid, "Настройки сброшены. Начнем заново!", reply_markup=main_menu())
    
    elif data == "ignore":
        bot.answer_callback_query(call.id)

# --- Функция для определения категории тега ---
def tag_category(tag):
    """Определяет категорию, к которой относится тег."""
    for cat, items in TAGS.items():
        if tag in items:
            if cat in ["body", "ethnos"]:
                return "body"
            if cat == "poses":
                return "pose"
            if cat == "holes":
                return "holes"
            if cat == "toys":
                return "toys"
            if cat == "clothes":
                return "clothes"
            if cat == "fetish":
                return "fetish"
            if cat == "head":
                return "face"
            if cat == "pokemon": # Pokemon category now includes characters
                return "pokemon"
            
            for char_cat_key in CHARACTER_CATEGORIES.keys():
                if tag.startswith(char_cat_key + "_"):
                    return "character"
    return None

# --- Оптимизированная функция для построения промпта ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов,
    используя новую логику группировки и обработки конфликтов.
    """
    base = [
        "masterpiece", "best quality", "ultra detailed", "anime style", "highly detailed",
        "expressive eyes", "perfect lighting", "volumetric lighting", "fully nude", "solo"
    ]

    priority = {
        "character": [],
        "furry": [],
        "body": [],
        "pose": [],
        "holes": [],
        "toys": [],
        "clothes": [],
        "fetish": [],
        "face": [],
        "pokemon": []
    }
    
    base_negative = (
        "lowres, bad anatomy, bad hands, bad face, deformed, disfigured, poorly drawn, "
        "missing limbs, extra limbs, fused fingers, jpeg artifacts, signature, watermark",
        "blurry, cropped, worst quality, low quality, text, error, mutated, censored, "
        "hands on chest, hands covering breasts, clothing covering genitals, shirt, bra, bikini, "
        "vagina not visible, anus not visible, penis not visible, bad proportions, "
        "all clothes, all clothing"
    )
    base_negative = "".join(base_negative)


    # Уникальные теги и спец. обработка конфликтов
    unique = set(tags)
    
    # Приоритет большим грудям
    if "big_breasts" in unique and "small_breasts" in unique:
        unique.remove("small_breasts") 
    
    # Костюм коровы уже включён в furry_cow
    if "furry_cow" in unique:
        unique.discard("cow_costume") 

    # Handle multiple characters
    character_tags_count = 0
    for tag in unique:
        for char_cat_key in CHARACTER_CATEGORIES.keys():
            if tag.startswith(char_cat_key + "_"):
                character_tags_count += 1
                break
    
    if character_tags_count > 1:
        base.insert(0, f"{character_tags_count}girls")
    elif character_tags_count == 1:
        base.insert(0, "1girl")
    elif not any(tag_category(t) in ["furry", "pokemon"] for t in unique): # Add 1girl if no specific character or furry/pokemon
         base.insert(0, "1girl")

    # Группировка по категориям
    for tag in unique:
        if tag in CHARACTER_EXTRA:
            priority["character"].append(TAG_PROMPTS.get(tag, tag))
        elif tag.startswith("furry_"):
            priority["furry"].append(TAG_PROMPTS.get(tag, tag))
        elif tag.startswith("pokemon_") or tag in ["reshiram", "mew", "mewtwo", "gardevoir", "umbreon", "lugia", "shadow_lugia", "lopunny", "goodra"]:
            priority["pokemon"].append(TAG_PROMPTS.get(tag, tag))
        elif tag in TAG_PROMPTS:
            key = tag_category(tag)
            if key:
                priority[key].append(TAG_PROMPTS[tag])

    prompt_parts = base[:]
    # Порядок добавления важен: количество девушек, персонажи, фури, покемоны, тело, позы, отверстия, игрушки, одежда, фетиши, лицо
    for section in ["character", "furry", "pokemon", "body", "pose", "holes", "toys", "clothes", "fetish", "face"]:
        prompt_parts.extend(priority[section])

    # Танлайны убирают купальник из негативного промпта
    if "bikini_tan_lines" in unique:
        base_negative += ", bikini"

    return {
        "positive_prompt": ", ".join(prompt_parts),
        "negative_prompt": base_negative
    } 

# --- Функция для генерации изображения через Replicate ---
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
                "seed": -1 # Генерировать новый сид для каждого изображения
            }
        }

        # Отправка запроса на создание предсказания
        r = requests.post(url, headers=headers, json=json_data)
        if r.status_code != 201:
            print(f"Ошибка при отправке предсказания: {r.status_code} - {r.text}")
            print(f"Request JSON: {json_data}")
            return None

        status_url = r.json()["urls"]["get"]

        # Ожидание завершения генерации (до 3 минут)
        for i in range(90):
            time.sleep(2)
            r = requests.get(status_url, headers=headers)
            if r.status_code != 200:
                print(f"Ошибка при получении статуса предсказания: {r.status_code} - {r.text}")
                return None
            data = r.json()
            if data["status"] == "succeeded":
                if isinstance(data["output"], list) and data["output"]:
                    urls.append(data["output"][0])
                    break
                else:
                    print("Получен пустой или некорректный 'output' от Replicate.")
                    return None
            elif data["status"] == "failed":
                print(f"Предсказание не удалось: {data.get('error', 'Сообщение об ошибке не предоставлено')}")
                print(f"Request JSON: {json_data}")
                return None
        else:
            print("Время ожидания предсказания истекло для одного изображения.")
            return None

    return urls

# --- Настройка вебхука Flask ---
@app.route("/", methods=["POST"])
def webhook():
    """Обрабатывает входящие обновления от Telegram."""
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    
    if update.message and update.message.chat.id not in user_settings:
        bot.send_message(update.message.chat.id, "Привет Шеф!", reply_markup=main_menu())
        user_settings[update.message.chat.id] = {"tags": [], "last_cat": None, "last_char_sub": None, "stockings_type": None, "num_images": 1}

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
