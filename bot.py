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
        "nipple_hole": "Отверстие в соске", # Добавлен
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
        "lotus_pose": "Поза лотоса", # Добавлен
        "scissors_pose": "Поза ножницы (две девушки)", # Добавлен
        "inverted_extreme_bridge": "Экстремальный мост/стойка на плечах с инверсией", # Добавлен
        "leaning_forward_wall": "Наклон вперёд у стены", # Добавлен
        "standing_vertical_split_supported": "Вертикальный шпагат стоя с поддержкой", # Добавлен
        "boat_pose_double_split_up": "Поза лодки / двойной шпагат вверх", # Добавлен
        "deep_sumo_squat": "Глубокий присед (сумо-поза)", # Добавлен
        "standing_horizontal_split_balanced": "Горизонтальный шпагат стоя с балансом", # Добавлен
        "classic_bridge": "Мостик", # Добавлен
        "sitting_horizontal_split_supported": "Горизонтальный шпагат сидя с опорой", # Добавлен
        "prone_frog_stretch": "Пролёт вперёд, плечевой растяг", # Добавлен
        "standing_deep_forward_bend": "Стоячий глубокий прогиб с опорой на руки", # Добавлен
        "forward_bow_forearms_clasped": "Наклон со сведёнными предплечьями", # Добавлен
        "top_down_voluminous_bow": "Объёмный поклон сверху (вид сверху)", # Добавлен
        "inverted_leg_over_shoulder": "Перевёрнутый сгиб с коленом над плечом", # Добавлен
        "casual_seated_open_knees": "Лёгкая поза сидя, колени разведены" # Добавлен
    },
    "clothes": {
        "stockings_white": "Белые чулки",
        "stockings_black": "Черные чулки",
        "stockings_red": "Красные чулки",
        "stockings_pink": "Розовые чулки",
        "stockings_gold": "Золотые чулки",
        "stockings_fishnet": "Чулки сеточкой",
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
        "furry_bear": "Фури медведь", # Добавлен
        "furry_bird": "Фури птица", # Добавлен
        "furry_mouse": "Фури мышь", # Добавлен
        "furry_deer": "Фури олень", # Добавлен
        "furry_tiger": "Фури тигр", # Добавлен
        "furry_lion": "Фури лев", # Добавлен
        "furry_snake": "Фури змея", # Добавлен
        "furry_lizard": "Фури ящерица" # Добавлен
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
        "foot_fetish": "Футфетиш",
        "footjob": "Футджоб",
        "mouth_nipples": "Вместо сосков рты",
        "nipple_hole": "Отверстие в сосках",
        "anus_piercing": "Пирсинг ануса",
        "vagina_piercing": "Пирсинг вагины",
        "gag": "Кляп",
        "blindfold": "Повязка на глаза",
        "horse_sex": "Секс с конем", # Добавлен
        "dilated_nipples": "Расширенные соски",
        "anus_spreader_ring": "Расширительное кольцо в анусе",
        "vagina_spreader_ring": "Расширительное кольцо в вагине"
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
        "goodra": "Гудра"
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
        "genshin_xinyan": "Синь Янь
        ",
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
        
        # Pokémon (персонажи-люди)
        "pokemon_jessie": "Джесси",
        "pokemon_lusamine": "Лусамине",

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
    "bleach": "📺 Bleach", # НОВАЯ КАТЕГОРИЯ
    "danmachi": "📺 Danmachi",
    "ragnarok": "📺 Повесть о конце света",
    "naruto": "📺 Naruto",
    "overlord": "📺 Overlord",
    "kakegurui": "📺 Безумный азарт",
    "jujutsukaisen": "📺 Магическая битва",
    "shieldhero": "📺 Герой Щита",
    "helltaker": "🎮 Helltaker",
    "zzz": "🎮 Zenless Zone Zero",
    "pokemon_chars": "📺 Pokémon (персонажи)",
    "lol": "🎮 League of Legends",
    "mlp": "📺 My Little Pony",
    "dislyte": "🎮 Dislyte"
}

# --- Промпты для модели ---
CHARACTER_EXTRA = {
    "dxd_rias": "rias gremory, red long hair, blue eyes, pale skin, large breasts, highschool dxd",
    "dxd_akeno": "akeno himejima, long black hair, purple eyes, large breasts, highschool dxd",
    "dxd_xenovia_quarta": "xenovia quarta, highschool dxd, blue hair, short hair, sword, holy sword, devil wings, nun uniform",
    "dxd_serafall_leviathan": "serafall leviathan, highschool dxd, magical girl outfit, pink hair, magical wand, devil, large breasts",
    "dxd_asia_argento": "asia argento, highschool dxd, blonde hair, long hair, nun, innocent, healing magic, dragon slayer, devil wings",
    "dxd_koneko_toujou": "koneko toujou, highschool dxd, white hair, cat ears, cat tail, small breasts, stoic expression",
    "dxd_shidou_irina": "shidou irina, highschool dxd, blonde hair, twin tails, energetic, holy sword, angel wings, exorcist",
    "dxd_gasper_vladi": "gasper vladi, highschool dxd, male, trap, feminine clothing, long blonde hair, shy, vampire, crossdresser",
    "dxd_rossweisse": "rossweisse, highschool dxd, valkyrie, long silver hair, glasses, mature, large breasts",
    "dxd_yasaka": "yasaka, highschool dxd, kitsune, nine tails, fox ears, kimono, mature woman",
    "dxd_grayfia_lucifuge": "grayfia lucifuge, highschool dxd, maid outfit, long silver hair, red eyes, ice magic, sexy maid",
    
    # Genshin Impact
    "genshin_eula": "eula, light blue hair, fair skin, genshin impact",
    "genshin_mona": "mona, genshin impact, black hair, leotard, golden headdress",
    "genshin_klee": "klee, genshin impact, blonde hair, red dress, explosive",
    "genshin_raiden_shogun": "raiden shogun, genshin impact, purple hair, kimono, electro archon",
    "genshin_paimon": "paimon, genshin impact, floating companion, small body, white hair, crown, emergency food",
    "genshin_amber": "amber, genshin impact, knight of favonius, long brown hair, red bow, goggles",
    "genshin_barbara": "barbara, genshin impact, idol, blue dress, blonde hair, deaconess",
    "genshin_beidou": "beidou, genshin impact, black hair, red outfit, eyepatch, captain",
    "genshin_collei": "collei, genshin impact, green hair, dendro, forest ranger, bandages",
    "genshin_dehya": "dehya, genshin impact, tanned skin, red hair, muscular, mercenary",
    "genshin_diluc_f": "diluc, female, genshin impact, red hair, elegant dress, pyro",
    "genshin_diona": "diona, genshin impact, cat girl, pink hair, bartender, cryo",
    "genshin_fischl": "fischl, genshin impact, prinzessin der verurteilung, gothic dress, blonde hair, oz",
    "genshin_ganyu": "ganyu, genshin impact, qilin, blue hair, horns, long dress, cryo",
    "genshin_hutao": "hutao, genshin impact, funeral parlor director, brown hair, twin tails, ghost, pyro",
    "genshin_jean": "jean gunnhildr, genshin impact, acting grand master, blonde hair, knight uniform",
    "genshin_kazuha_f": "kaedehara kazuha, female, genshin impact, anemo, red leaves, kimono, white hair",
    "genshin_keqing": "keqing, genshin impact, purple hair, cat ears, electro, yuheng",
    "genshin_kuki_shinobu": "kuki shinobu, genshin impact, ninja, green hair, mask, electro",
    "genshin_lisa": "lisa minci, genshin impact, librarian, purple dress, electro, witch",
    "genshin_nahida": "nahida, genshin impact, dendro archon, white hair, green dress, loli",
    "genshin_ningguang": "ningguang, genshin impact, rich, elegant dress, long white hair, geo, jade chamber",
    "genshin_noelle": "noelle, genshin impact, maid, knight, blonde hair, heavy armor",
    "genshin_rosaria": "rosaria, genshin impact, nun, dark outfit, red hair, cryo, cynical",
    "genshin_sara": "kujou sara, genshin impact, tengu, black wings, kimono, electro, general",
    "genshin_sayu": "sayu, genshin impact, ninja, tanuki, anemo, sleepy",
    "genshin_shenhe": "shenhe, genshin impact, white hair, long dress, cryo, exorcist",
    "genshin_sucrose": "sucrose, genshin impact, alchemist, green hair, glasses, anemo",
    "genshin_venti_f": "venti, female, genshin impact, anemo archon, bard, green outfit",
    "genshin_xiangling": "xiangling, genshin impact, chef, brown hair, panda, pyro",
    "genshin_xinyan": "xinyan, genshin impact, rockstar, dark skin, red hair, pyro, lute",
    "genshin_yaemiko": "yae miko, genshin impact, fox ears, pink hair, miko, electro",
    "genshin_yanfei": "yanfei, genshin impact, legal advisor, white hair, deer horns, pyro",
    "genshin_yoimiya": "yoimiya, genshin impact, fireworks, blonde hair, kimono, pyro",
    "genshin_yelan": "yelan, genshin impact, blue hair, black bodysuit, hydro, secret agent",
    "genshin_zhongli_f": "zhongli, female, genshin impact, geo archon, elegant, brown hair, long coat",
    "genshin_furina": "furina, genshin impact, hydro archon, twin tails, white hair, elegant dress, dramatic",
    "genshin_navia": "navia, genshin impact, blonde hair, yellow dress, umbrella, elegant",
    "genshin_chevreuse": "chevreuse, genshin impact, red hair, military uniform, eyepatch, musket",
    "genshin_clorinde": "clorinde, genshin impact, purple hair, fencer, elegant hat, duelist",
    "genshin_ar_traveler_f": "aether, female, genshin impact, blonde hair, traveler outfit, sword",
    "genshin_lumine": "lumine, genshin impact, blonde hair, traveler outfit, sword",
    "genshin_signora": "signora, genshin impact, fatui harbinger, elegant mask, white hair, cryo",
    "genshin_arlecchino": "arlecchino, genshin impact, fatui harbinger, black outfit, twin tails, pyro",
    "genshin_snezhnaya_fatui_harbinger": "snezhnaya fatui harbinger, female, genshin impact, mask, uniform",


    # Honkai Star Rail
    "hsr_kafka": "kafka, purple wavy hair, cold expression, honkai star rail",
    "hsr_fu_xuan": "fu xuan, pink hair, honkai star rail, diviner, short hair, glasses",
    "hsr_sparkle": "sparkle, honkai star rail, pink hair, elegant dress, theatrical",
    "hsr_acheron": "acheron, honkai star rail, purple hair, long coat, samurai",
    "hsr_march_7th": "march 7th, honkai star rail, pink hair, camera, ice powers, archer",
    "hsr_himeko": "himeko, honkai star rail, red hair, red coat, coffee, train conductor",
    "hsr_bronya": "bronya rand, honkai star rail, silver hair, elegant uniform, queen, spear",
    "hsr_seele": "seele, honkai star rail, blue hair, scythe, butterfly, quantum",
    "hsr_jingliu": "jingliu, honkai star rail, white hair, blindfold, sword, ice",
    "hsr_stelle": "stelle, honkai star rail, female trailblazer, brown hair, baseball bat",
    "hsr_herta": "herta, honkai star rail, doll, purple hair, genius, space station",
    "hsr_silver_wolf": "silver wolf, honkai star rail, hacker, blue hair, short hair, cyber punk",
    "hsr_tingyun": "tingyun, honkai star rail, fox ears, kimono, fan, lightning",
    "hsr_asta": "asta, honkai star rail, red hair, space station, rich girl",
    "hsr_clara": "clara, honkai star rail, child, robot, pink hair, shy",
    "hsr_peia": "peia, honkai star rail, foxian, healer, long hair", # Placeholder, adjust if specific design available
    "hsr_sushang": "sushang, honkai star rail, sword, knight, chicken, red hair",
    "hsr_natasha": "natasha, honkai star rail, doctor, blonde hair, medical coat",
    "hsr_hook": "hook, honkai star rail, child, red hair, big hat, destruction",
    "hsr_pela": "pela, honkai star rail, glasses, detective, blue hair, short hair",
    "hsr_qingque": "qingque, honkai star rail, mahjong, green hair, lazy",
    "hsr_yukong": "yukong, honkai star rail, foxian, pilot, mature, elegant",
    "hsr_guinaifen": "guinaifen, honkai star rail, streamer, fire performer, pink hair",
    "hsr_huohuo": "huohuo, honkai star rail, green hair, fox girl, exorcist, ghost",
    "hsr_xueyi": "xueyi, honkai star rail, puppet, pink hair, executioner, mask",
    "hsr_hanabi": "hanabi, honkai star rail, pink hair, elegant dress, theatrical", # Sparkle
    "hsr_robin": "robin, honkai star rail, idol, blonde hair, singer, elegant dress",
    "hsr_aventurine_f": "aventurine, female, honkai star rail, blonde hair, gambler, suit", # Female Aventurine

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
    
    # Pokémon (персонажи-люди)
    "pokemon_jessie": "Джесси",
    "pokemon_lusamine": "Лусамине",

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
    "bleach": "📺 Bleach", # НОВАЯ КАТЕГОРИЯ
    "danmachi": "📺 Danmachi",
    "ragnarok": "📺 Повесть о конце света",
    "naruto": "📺 Naruto",
    "overlord": "📺 Overlord",
    "kakegurui": "📺 Безумный азарт",
    "jujutsukaisen": "📺 Магическая битва",
    "shieldhero": "📺 Герой Щита",
    "helltaker": "🎮 Helltaker",
    "zzz": "🎮 Zenless Zone Zero",
    "pokemon_chars": "📺 Pokémon (персонажи)",
    "lol": "🎮 League of Legends",
    "mlp": "📺 My Little Pony",
    "dislyte": "🎮 Dislyte"
}

# --- Промпты для модели ---
CHARACTER_EXTRA = {
    "dxd_rias": "rias gremory, red long hair, blue eyes, pale skin, large breasts, highschool dxd",
    "dxd_akeno": "akeno himejima, long black hair, purple eyes, large breasts, highschool dxd",
    "dxd_xenovia_quarta": "xenovia quarta, highschool dxd, blue hair, short hair, sword, holy sword, devil wings, nun uniform",
    "dxd_serafall_leviathan": "serafall leviathan, highschool dxd, magical girl outfit, pink hair, magical wand, devil, large breasts",
    "dxd_asia_argento": "asia argento, highschool dxd, blonde hair, long hair, nun, innocent, healing magic, dragon slayer, devil wings",
    "dxd_koneko_toujou": "koneko toujou, highschool dxd, white hair, cat ears, cat tail, small breasts, stoic expression",
    "dxd_shidou_irina": "shidou irina, highschool dxd, blonde hair, twin tails, energetic, holy sword, angel wings, exorcist",
    "dxd_gasper_vladi": "gasper vladi, highschool dxd, male, trap, feminine clothing, long blonde hair, shy, vampire, crossdresser",
    "dxd_rossweisse": "rossweisse, highschool dxd, valkyrie, long silver hair, glasses, mature, large breasts",
    "dxd_yasaka": "yasaka, highschool dxd, kitsune, nine tails, fox ears, kimono, mature woman",
    "dxd_grayfia_lucifuge": "grayfia lucifuge, highschool dxd, maid outfit, long silver hair, red eyes, ice magic, sexy maid",
    
    # Genshin Impact
    "genshin_eula": "eula, light blue hair, fair skin, genshin impact",
    "genshin_mona": "mona, genshin impact, black hair, leotard, golden headdress",
    "genshin_klee": "klee, genshin impact, blonde hair, red dress, explosive",
    "genshin_raiden_shogun": "raiden shogun, genshin impact, purple hair, kimono, electro archon",
    "genshin_paimon": "paimon, genshin impact, floating companion, small body, white hair, crown, emergency food",
    "genshin_amber": "amber, genshin impact, knight of favonius, long brown hair, red bow, goggles",
    "genshin_barbara": "barbara, genshin impact, idol, blue dress, blonde hair, deaconess",
    "genshin_beidou": "beidou, genshin impact, black hair, red outfit, eyepatch, captain",
    "genshin_collei": "collei, genshin impact, green hair, dendro, forest ranger, bandages",
    "genshin_dehya": "dehya, genshin impact, tanned skin, red hair, muscular, mercenary",
    "genshin_diluc_f": "diluc, female, genshin impact, red hair, elegant dress, pyro",
    "genshin_diona": "diona, genshin impact, cat girl, pink hair, bartender, cryo",
    "genshin_fischl": "fischl, genshin impact, prinzessin der verurteilung, gothic dress, blonde hair, oz",
    "genshin_ganyu": "ganyu, genshin impact, qilin, blue hair, horns, long dress, cryo",
    "genshin_hutao": "hutao, genshin impact, funeral parlor director, brown hair, twin tails, ghost, pyro",
    "genshin_jean": "jean gunnhildr, genshin impact, acting grand master, blonde hair, knight uniform",
    "genshin_kazuha_f": "kaedehara kazuha, female, genshin impact, anemo, red leaves, kimono, white hair",
    "genshin_keqing": "keqing, genshin impact, purple hair, cat ears, electro, yuheng",
    "genshin_kuki_shinobu": "kuki shinobu, genshin impact, ninja, green hair, mask, electro",
    "genshin_lisa": "lisa minci, genshin impact, librarian, purple dress, electro, witch",
    "genshin_nahida": "nahida, genshin impact, dendro archon, white hair, green dress, loli",
    "genshin_ningguang": "ningguang, genshin impact, rich, elegant dress, long white hair, geo, jade chamber",
    "genshin_noelle": "noelle, genshin impact, maid, knight, blonde hair, heavy armor",
    "genshin_rosaria": "rosaria, genshin impact, nun, dark outfit, red hair, cryo, cynical",
    "genshin_sara": "kujou sara, genshin impact, tengu, black wings, kimono, electro, general",
    "genshin_sayu": "sayu, genshin impact, ninja, tanuki, anemo, sleepy",
    "genshin_shenhe": "shenhe, genshin impact, white hair, long dress, cryo, exorcist",
    "genshin_sucrose": "sucrose, genshin impact, alchemist, green hair, glasses, anemo",
    "genshin_venti_f": "venti, female, genshin impact, anemo archon, bard, green outfit",
    "genshin_xiangling": "xiangling, genshin impact, chef, brown hair, panda, pyro",
    "genshin_xinyan": "xinyan, genshin impact, rockstar, dark skin, red hair, pyro, lute",
    "genshin_yaemiko": "yae miko, genshin impact, fox ears, pink hair, miko, electro",
    "genshin_yanfei": "yanfei, genshin impact, legal advisor, white hair, deer horns, pyro",
    "genshin_yoimiya": "yoimiya, genshin impact, fireworks, blonde hair, kimono, pyro",
    "genshin_yelan": "yelan, genshin impact, blue hair, black bodysuit, hydro, secret agent",
    "genshin_zhongli_f": "zhongli, female, genshin impact, geo archon, elegant, brown hair, long coat",
    "genshin_furina": "furina, genshin impact, hydro archon, twin tails, white hair, elegant dress, dramatic",
    "genshin_navia": "navia, genshin impact, blonde hair, yellow dress, umbrella, elegant",
    "genshin_chevreuse": "chevreuse, genshin impact, red hair, military uniform, eyepatch, musket",
    "genshin_clorinde": "clorinde, genshin impact, purple hair, fencer, elegant hat, duelist",
    "genshin_ar_traveler_f": "aether, female, genshin impact, blonde hair, traveler outfit, sword",
    "genshin_lumine": "lumine, genshin impact, blonde hair, traveler outfit, sword",
    "genshin_signora": "signora, genshin impact, fatui harbinger, elegant mask, white hair, cryo",
    "genshin_arlecchino": "arlecchino, genshin impact, fatui harbinger, black outfit, twin tails, pyro",
    "genshin_snezhnaya_fatui_harbinger": "snezhnaya fatui harbinger, female, genshin impact, mask, uniform",


    # Honkai Star Rail
    "hsr_kafka": "kafka, purple wavy hair, cold expression, honkai star rail",
    "hsr_fu_xuan": "fu xuan, pink hair, honkai star rail, diviner, short hair, glasses",
    "hsr_sparkle": "sparkle, honkai star rail, pink hair, elegant dress, theatrical",
    "hsr_acheron": "acheron, honkai star rail, purple hair, long coat, samurai",
    "hsr_march_7th": "march 7th, honkai star rail, pink hair, camera, ice powers, archer",
    "hsr_himeko": "himeko, honkai star rail, red hair, red coat, coffee, train conductor",
    "hsr_bronya": "bronya rand, honkai star rail, silver hair, elegant uniform, queen, spear",
    "hsr_seele": "seele, honkai star rail, blue hair, scythe, butterfly, quantum",
    "hsr_jingliu": "jingliu, honkai star rail, white hair, blindfold, sword, ice",
    "hsr_stelle": "stelle, honkai star rail, female trailblazer, brown hair, baseball bat",
    "hsr_herta": "herta, honkai star rail, doll, purple hair, genius, space station",
    "hsr_silver_wolf": "silver wolf, honkai star rail, hacker, blue hair, short hair, cyber punk",
    "hsr_tingyun": "tingyun, honkai star rail, fox ears, kimono, fan, lightning",
    "hsr_asta": "asta, honkai star rail, red hair, space station, rich girl",
    "hsr_clara": "clara, honkai star rail, child, robot, pink hair, shy",
    "hsr_peia": "peia, honkai star rail, foxian, healer, long hair", # Placeholder, adjust if specific design available
    "hsr_sushang": "sushang, honkai star rail, sword, knight, chicken, red hair",
    "hsr_natasha": "natasha, honkai star rail, doctor, blonde hair, medical coat",
    "hsr_hook": "hook, honkai star rail, child, red hair, big hat, destruction",
    "hsr_pela": "pela, honkai star rail, glasses, detective, blue hair, short hair",
    "hsr_qingque": "qingque, honkai star rail, mahjong, green hair, lazy",
    "hsr_yukong": "yukong, honkai star rail, foxian, pilot, mature, elegant",
    "hsr_guinaifen": "guinaifen, honkai star rail, streamer, fire performer, pink hair",
    "hsr_huohuo": "huohuo, honkai star rail, green hair, fox girl, exorcist, ghost",
    "hsr_xueyi": "xueyi, honkai star rail, puppet, pink hair, executioner, mask",
    "hsr_hanabi": "hanabi, honkai star rail, pink hair, elegant dress, theatrical", # Sparkle
    "hsr_robin": "robin, honkai star rail, idol, blonde hair, singer, elegant dress",
    "hsr_aventurine_f": "aventurine, female, honkai star rail, blonde hair, gambler, suit", # Female Aventurine

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
    
    # Pokémon (персонажи-люди)
    "pokemon_jessie": "Джесси",
    "pokemon_lusamine": "Лусамине",

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
}

# --- Функции для создания клавиатур ---
def main_menu():
    """Создает главное меню бота."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")) # Новая кнопка для настроек
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
    else:
        tags_to_display = TAGS[category]

    for tag_key, tag_name in tags_to_display.items():
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
    user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1} # Добавлено num_images
    bot.send_message(cid, "Привет Шеф!", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Общий обработчик для всех кнопок колбэка."""
    cid = call.message.chat.id
    message_id = call.message.message_id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1}

    data = call.data

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, message_id, reply_markup=category_menu())

    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        selected = user_settings[cid]["tags"]
        
        if cat == "characters":
            # Сбрасываем last_char_sub при входе в основную категорию персонажей
            user_settings[cid]["last_char_sub"] = None 
            bot.edit_message_text("Выбери подкатегорию персонажей:", cid, message_id, reply_markup=character_subcategory_menu(selected))
        else:
            category_display_name = CATEGORY_NAMES.get(cat, cat)
            bot.edit_message_text(f"Категория: {category_display_name}", cid, message_id, reply_markup=tag_menu(cat, selected))

    elif data.startswith("char_sub_"):
        char_sub = data[9:]
        user_settings[cid]["last_char_sub"] = char_sub
        selected = user_settings[cid]["tags"]
        subcategory_display_name = CHARACTER_CATEGORIES.get(char_sub, char_sub)
        bot.edit_message_text(f"Подкатегория: {subcategory_display_name}", cid, message_id, reply_markup=tag_menu("characters", selected, char_sub))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        
        current_char_sub = user_settings[cid].get("last_char_sub") if cat == "characters" else None
        bot.edit_message_reply_markup(cid, message_id, reply_markup=tag_menu(cat, tags, current_char_sub))

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, message_id, reply_markup=main_menu())

    elif data == "back_to_cat":
        # Если возвращаемся из подкатегории персонажей, то сначала в меню подкатегорий
        if user_settings[cid].get("last_cat") == "characters" and user_settings[cid].get("last_char_sub"):
            user_settings[cid]["last_char_sub"] = None # Сбрасываем подкатегорию при возврате
            bot.edit_message_text("Выбери подкатегорию персонажей:", cid, message_id, reply_markup=character_subcategory_menu(user_settings[cid]["tags"]))
        else:
            bot.edit_message_text("Выбери категорию:", cid, message_id, reply_markup=category_menu())
    
    elif data == "back_to_char_sub":
        user_settings[cid]["last_char_sub"] = None # Сбрасываем подкатегорию при возврате
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

        bot.send_message(cid, "Принято Шеф, приступаю!") # Сообщение перед генерацией

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
        user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1}
        bot.send_message(cid, "Настройки сброшены. Начнем заново!", reply_markup=main_menu())
    
    elif data == "ignore":
        bot.answer_callback_query(call.id) # Просто игнорируем нажатие на текст-кнопку

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
            if cat == "pokemon":
                return "pokemon"
            
            # Для персонажей определяем категорию "character"
            # Проверяем, начинается ли тег с какого-либо ключа из CHARACTER_CATEGORIES
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
    # Присоединяем части кортежа base_negative в одну строку
    base_negative = "".join(base_negative)


    # Уникальные теги и спец. обработка конфликтов
    unique = set(tags)
    
    # Приоритет большим грудям
    if "big_breasts" in unique and "small_breasts" in unique:
        unique.remove("small_breasts") 
    
    # Костюм коровы уже включён в furry_cow
    if "furry_cow" in unique:
        unique.discard("cow_costume") 

    # Группировка по категориям
    for tag in unique:
        if tag in CHARACTER_EXTRA:
            priority["character"].append(TAG_PROMPTS.get(tag, tag)) # Use TAG_PROMPTS as it contains CHARACTER_EXTRA
        elif tag.startswith("furry_"):
            priority["furry"].append(TAG_PROMPTS.get(tag, tag))
        elif tag in TAG_PROMPTS:
            key = tag_category(tag)
            if key:
                priority[key].append(TAG_PROMPTS[tag])

    prompt_parts = base[:]
    # Порядок добавления важен: персонажи, фури, покемоны, тело, позы, отверстия, игрушки, одежда, фетиши, лицо
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
                    break # Выходим из внутреннего цикла после успешной генерации
                else:
                    print("Получен пустой или некорректный 'output' от Replicate.")
                    return None
            elif data["status"] == "failed":
                print(f"Предсказание не удалось: {data.get('error', 'Сообщение об ошибке не предоставлено')}")
                print(f"Request JSON: {json_data}")
                return None
        else: # Если цикл завершился без break
            print("Время ожидания предсказания истекло для одного изображения.")
            return None # Возвращаем None, если хотя бы одно изображение не сгенерировалось

    return urls # Возвращаем список URL-ов всех сгенерированных изображений

# --- Настройка вебхука Flask ---
@app.route("/", methods=["POST"])
def webhook():
    """Обрабатывает входящие обновления от Telegram."""
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    
    # Автоматическая отправка /start при первом запуске (если это не колбэк)
    # Проверяем, что это новое сообщение и пользователь еще не в user_settings
    if update.message and update.message.chat.id not in user_settings:
        bot.send_message(update.message.chat.id, "Привет Шеф!", reply_markup=main_menu())
        user_settings[update.message.chat.id] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1}

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
