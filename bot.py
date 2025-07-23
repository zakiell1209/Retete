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
        "lotus_pose": "Поза лотоса", # NEW
        "scissors_pose": "Поза ножницы (две девушки)" # NEW
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
        "furry_bear": "Фури медведь", # NEW
        "furry_bird": "Фури птица", # NEW
        "furry_mouse": "Фури мышь", # NEW
        "furry_deer": "Фури олень", # NEW
        "furry_tiger": "Фури тигр", # NEW
        "furry_lion": "Фури лев", # NEW
        "furry_snake": "Фури змея", # NEW
        "furry_lizard": "Фури ящерица" # NEW
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
    "nier_2b": "2b, nier automata, white hair, black dress",

    # Spy x Family
    "spyxfamily_yor_forger": "yor forger, spy x family, black hair, red dress",

    # Akame ga Kill
    "akamegakill_esdeath": "esdeath, akame ga kill, blue hair, military uniform, high heels",

    # Azur Lane
    "azurlane_formidable": "formidable, azur lane, long white hair, dress",

    # Fate Series
    "fate_castoria": "castoria, fate grand order, white hair, dress, long sleeves",
    "fate_saber": "saber, artoria pendragon, fate series, blonde hair, blue dress",
    "fate_astolfo": "astolfo, fate series, pink hair, femboy, androgynous",

    # Resident Evil
    "residentevil_lady_dimitrescu": "lady dimitrescu, resident evil, tall female, white dress, elegant hat, sharp claws, mature female",

    # Street Fighter
    "streetfighter_chun_li": "chun li, street fighter, muscular thighs, qipao, hair buns",
    "streetfighter_cammy": "cammy white, street fighter, blonde hair, green leotard, muscular, braid",
    "streetfighter_balrog_f": "balrog, female, street fighter, boxer, muscular female, braids",
    "streetfighter_juri": "juri han, street fighter, purple hair, taekwondo, spider lily, evil smile",
    "streetfighter_menat": "menat, street fighter, fortune teller, blue hair, sphere, egyptian",
    "streetfighter_laura": "laura matsuda, street fighter, brazilian, green clothes, long hair, electric powers",
    "streetfighter_poison": "poison, street fighter, trans, pink hair, short shorts, crop top",
    "streetfighter_maki": "maki genryusai, street fighter, kunoichi, short hair, ninja outfit",
    "streetfighter_rose": "rose, street fighter, fortune teller, red scarf, mystical powers",
    "streetfighter_r_mika": "rainbow mika, street fighter, wrestler, blue wrestling suit, blonde hair, muscular",
    "streetfighter_ibuki": "ibuki, street fighter, ninja, school uniform, kunai",
    "streetfighter_karin": "karin kanzuki, street fighter, rich girl, blonde hair, school uniform, ojou-sama",
    "streetfighter_ed": "ed, street fighter, female, boxer, psychic powers, blonde hair", # Предполагаем женскую версию
    "streetfighter_fang": "f.a.n.g, female, street fighter, poison, long clothes", # Предполагаем женскую версию
    "streetfighter_e_honda_f": "e. honda, female, street fighter, sumo wrestler, large body", # Предполагаем женскую версию, промпт для соответствия

    # Atomic Heart
    "atomicheart_twins": "robot, twin sisters, black bodysuit, black hair, white hair, atomic heart",

    # Bleach - НОВЫЕ ПЕРСОНАЖИ И ИСПРАВЛЕННЫЙ ПРОМПТ ДЛЯ YORUICHI
    "bleach_renji_f": "renji abarai, female, bleach, red hair, tattoos, shinigami, zanpakuto",
    "bleach_rukia_kuchiki": "rukia kuchiki, bleach, short black hair, shinigami, zanpakuto, noble family",
    "bleach_orihime_inoue": "orihime inoue, bleach, long orange hair, hairpin, school uniform, healer",
    "bleach_yoruichi_shihoin": "yoruichi shihoin, bleach, dark skin, purple short hair, cat form, thunder god, shinigami",
    "bleach_rangiku_matsumoto": "rangiku matsumoto, bleach, blonde wavy hair, large breasts, shinigami, haori, vice-captain",
    "bleach_nemu_kurotsuchi": "nemu kurotsuchi, bleach, short black hair, maid outfit, emotionless, artificial soul, lieutenant",
    "bleach_nelliel_tu_odelschwanck": "nelliel tu odelschwanck, bleach, arrancar, green hair, mask fragment, revealing outfit, childlike form, adult form, espada",
    "bleach_tier_harribel": "tier harribel, bleach, arrancar, shark-like mask, tanned skin, revealing coat, espada",
    "bleach_retsu_unohana": "retsu unohana, bleach, black braided hair, calm expression, shinigami captain, kimono, healing powers, fierce past",
    "bleach_soi_fon": "soi fon, bleach, short black hair, shinigami captain, uniform, assassin, strict, high speed",
    "bleach_hiyori_sarugaki": "hiyori sarugaki, bleach, blonde pigtails, visored, school uniform, aggressive, short temper",
    "bleach_lisa_yadomaru": "lisa yadomaru, bleach, long black hair, glasses, school uniform, shinigami, visored, lewd librarian",
    "bleach_mashiro_kuna": "mashiro kuna, bleach, green hair, energetic, visored, goggles, eccentric",
    "bleach_nanao_ise": "nanao ise, bleach, short black hair, glasses, shinigami vice-captain, serious, intellectual",
    "bleach_isane_kotetsu": "isane kotetsu, bleach, long silver hair, shinigami vice-captain, gentle, healer",
    "bleach_momo_hinamori": "momo hinamori, bleach, brown hair, shinigami, loyal, innocent, prone to distress",
    "bleach_candice_catnipp": "candice catnipp, bleach, quincy, blonde spiky hair, lightning powers, sternritter, aggressive",
    "bleach_bambietta_basterbine": "bambietta basterbine, bleach, quincy, short black hair, explosive powers, sternritter, volatile",
    "bleach_giselle_gewelle": "giselle gewelle, bleach, quincy, blonde hair, zombie powers, sternritter, crossdresser, creepy",
    "bleach_meninas_mcallon": "meninas mcallon, bleach, quincy, pink hair, muscular, sternritter, strong",
    "bleach_liltotto_lamperd": "liltotto lamperd, bleach, quincy, blonde pigtails, childlike, sternritter, cannibalistic",


    # Danmachi
    "danmachi_hestia": "hestia, danmachi, black hair, blue ribbons, white dress",
    "danmachi_freya": "freya, danmachi, long silver hair, purple eyes, elegant dress",

    # Повесть о конце света (Record of Ragnarok)
    "ragnarok_aphrodite": "aphrodite, record of ragnarok, large breasts, blonde hair, revealing outfit",

    # Naruto
    "naruto_hinata": "hinata hyuga, naruto, long dark blue hair, byakugan, shy, large breasts",
    "naruto_tsunade": "tsunade, naruto, blonde hair, large breasts, strong, medical ninja",

    # Overlord
    "overlord_albedo": "albedo, overlord, succubus, black wings, white dress, long black hair",
    "overlord_shalltear": "shalltear bloodfallen, overlord, vampire, short blonde hair, frilly dress, parasol",

    # Безумный азарт (Kakegurui)
    "kakegurui_yumeko": "yumeko jabami, kakegurui, long black hair, red eyes, school uniform, insane smile",
    "kakegurui_kirari": "kirari momobami, kakegurui, white hair, blue lips, school uniform, student council president",
    "kakegurui_mary": "mary saotome, kakegurui, blonde hair, school uniform, twin tails",

    # Магическая битва (Jujutsu Kaisen)
    "jujutsukaisen_mei_mei": "mei mei, jujutsu kaisen, long black hair, axe, confident expression",

    # Герой Щита (The Rising of the Shield Hero)
    "shieldhero_mirelia_melromarc": "mirelia q melromarc, the rising of the shield hero, queen, blonde hair, elegant dress",
    "shieldhero_malty_melromarc": "malty s melromarc, the rising of the shield hero, bitch, cruel smile, red hair, blonde hair, princess, villainess",
    
    # Helltaker
    "helltaker_lucifer": "lucifer, helltaker, long black hair, business suit",

    # Zenless Zone Zero
    "zzz_ellen_joe": "ellen joe, zenless zone zero, long blonde hair, school uniform, glasses, student",
    "zzz_koleda": "koleda, zenless zone zero, bear ears, blonde hair, maid uniform",
    "zzz_lycaon": "lycaon, female, zenless zone zero, wolf girl, black hair, combat outfit",
    "zzz_nicole": "nicole demara, zenless zone zero, short blue hair, business suit, glasses",
    "zzz_anby": "anby demara, zenless zone zero, white hair, casual clothes, electric powers",
    "zzz_nekomiya": "nekomiya mana, zenless zone zero, cat girl, ninja, black hair, agile",
    "zzz_aisha": "aisha, zenless zone zero, bunny girl, white hair, cute dress",
    "zzz_haruka": "haruka, zenless zone zero, pink hair, schoolgirl, cheerful",
    "zzz_corin": "corin, zenless zone zero, detective, blonde hair, trench coat",
    "zzz_grace": "grace, zenless zone zero, elegant dress, mature, long hair",
    "zzz_hoshimi": "hoshimi, zenless zone zero, idol, pink hair, stage outfit",
    "zzz_rory": "rory, zenless zone zero, mechanic, short hair, overalls",
    "zzz_bonnie": "bonnie, zenless zone zero, cowgirl, hat, red hair",
    "zzz_elize": "elize, zenless zone zero, maid, long blonde hair",
    "zzz_fubuki": "fubuki, zenless zone zero, samurai, white hair, kimono",
    "zzz_sana": "sana, zenless zone zero, cyborg, blue hair, futuristic outfit",
    "zzz_yuki": "yuki, zenless zone zero, school uniform, black hair, shy",
        
    # Pokémon (персонажи-люди) - Moved to "pokemon" category
    "pokemon_jessie": "jessie, pokemon, team rocket, red hair, long hair, ponytail",
    "pokemon_lusamine": "lusamine, pokemon, aether foundation, blonde hair, long hair, dress",

    # League of Legends
    "lol_qiyana": "qiyana, league of legends",
    "lol_aurora": "aurora, league of legends",
    "lol_katarina": "katarina, league of legends",
    "lol_akali": "akali, league of legends",
    "lol_irelia": "irelia, league of legends",
    "lol_caitlyn": "caitlyn, league of legends",
    "lol_briar": "briar, league of legends",
    "lol_kaisa": "kaisa, league of legends",
    "lol_evelynn": "evelynn, league of legends",
    "lol_ahri": "ahri, league of legends",
    "lol_belveth": "belveth, league of legends",
    "lol_fiora": "fiora, league of legends",
    "lol_gwen": "gwen, league of legends",
    "lol_zoe": "zoe, league of legends",
    "lol_missfortune": "miss fortune, league of legends",
    "lol_neeko": "neeko, league of legends",
    "lol_samira": "samira, league of legends",
    "lol_sona": "sona, league of legends",
    "lol_elise": "elise, league of legends",

    # My Little Pony
    "mlp_twilight_sparkle": "twilight sparkle, my little pony, alicorn, purple body, dark blue mane, magic aura",
    "mlp_applejack": "applejack, my little pony, earth pony, orange body, blonde mane, cowboy hat",
    "mlp_rainbow_dash": "rainbow dash, my little pony, pegasus, light blue body, rainbow mane, cloud, lightning bolt",
    "mlp_rarity": "rarity, my little pony, unicorn, white body, purple mane, diamonds, fashionista",
    "mlp_fluttershy": "fluttershy, my little pony, pegasus, yellow body, pink mane, butterflies, shy, animal lover",
    "mlp_pinkie_pie": "pinkie pie, my little pony, earth pony, pink body, pink curly mane, balloons, cheerful, party",
    "mlp_spike": "spike, my little pony, dragon, green scales, purple spikes, loyal, baby dragon",
    "mlp_princess_celestia": "princess celestia, my little pony, alicorn, white body, rainbow mane, sun, royalty",
    "mlp_princess_luna": "princess luna, my little pony, alicorn, dark blue body, flowing mane, moon, royalty",
    "mlp_princess_cadence": "princess cadence, my little pony, alicorn, pink body, purple and yellow mane, crystal heart, royalty",
    "mlp_discord": "discord, my little pony, draconequus, chaotic, mischievous, master of chaos",
    "mlp_apple_bloom": "apple bloom, my little pony, earth pony, yellow body, red mane, cutie mark crusader",
    "mlp_scootaloo": "scootaloo, my little pony, pegasus, orange body, purple mane, cutie mark crusader, scooter",
    "mlp_sweetie_belle": "sweetie belle, my little pony, unicorn, white body, pink and purple mane, cutie mark crusader",

    # Dislyte
    "dislyte_li_ling_f": "li ling, female, dislyte, red hair, dragon, elegant outfit",
    "dislyte_sally": "sally, dislyte, siren, blue hair, mermaid tail, elegant dress",
    "dislyte_clara": "clara, dislyte, valkyrie, blonde hair, armor, wings",
    "dislyte_gabrielle": "gabrielle, dislyte, archangel, white wings, blonde hair, elegant dress",
    "dislyte_chloe": "chloe, dislyte, griffin, blonde hair, short hair, casual outfit",
    "dislyte_odette": "odette, dislyte, swan, elegant dress, graceful, long hair",
    "dislyte_meredith": "meredith, dislyte, medusa, snake hair, green skin, revealing outfit",
    "dislyte_jiang_man": "jiang man, dislyte, black hair, traditional chinese dress, elegant",
    "dislyte_eira": "eira, dislyte, ice queen, white hair, blue dress, cold expression",
    "dislyte_drew": "drew, dislyte, dark hair, casual outfit, energetic",
    "dislyte_pritzker_f": "pritzker, female, dislyte, blonde hair, glasses, scientist",
    "dislyte_fatima": "fatima, dislyte, desert warrior, tanned skin, veil, sword",
    "dislyte_brewster_f": "brewster, female, dislyte, red hair, punk outfit, guitar",
    "dislyte_yun_chuan_f": "yun chuan, female, dislyte, traditional chinese outfit, long hair",
    "dislyte_hyde_f": "hyde, female, dislyte, dark hair, gothic outfit, mysterious",
    "dislyte_leora": "leora, dislyte, lioness, blonde hair, armored, fierce",
    "dislyte_tevor_f": "tevor, female, dislyte, blonde hair, casual outfit, energetic",
    "dislyte_zora": "zora, dislyte, desert wanderer, dark skin, tribal outfit",
    "dislyte_embla": "embla, dislyte, raven, black wings, dark outfit, mysterious",
    "dislyte_ophilia": "ophilia, dislyte, fairy, green hair, light dress, nature",
    "dislyte_ahmed_f": "ahmed, female, dislyte, desert prince, traditional outfit, elegant",
    "dislyte_everett_f": "everett, female, dislyte, casual outfit, confident",
    "dislyte_ollie_f": "ollie, female, dislyte, short hair, sporty outfit, cheerful",
    "dislyte_jin_hee": "jin hee, dislyte, korean traditional dress, elegant, long hair",
    "dislyte_ifrit_f": "ifrit, female, dislyte, fiery hair, demonic, powerful",
    "dislyte_sienna": "sienna, dislyte, nature spirit, green hair, leafy outfit",
    "dislyte_valeria": "valeria, dislyte, gladiator, armored, strong, short hair",
    "dislyte_ashley": "ashley, dislyte, pop star, pink hair, stage outfit, microphone",
    "dislyte_triki_f": "triki, female, dislyte, mischievous, clown outfit, colorful hair",
    "dislyte_narmer_f": "narmer, female, dislyte, egyptian pharaoh, golden armor, elegant",
    "dislyte_tye": "tye, dislyte, archer, green hair, forest outfit",
    "dislyte_biondina": "biondina, dislyte, water spirit, blue hair, flowing dress",
    "dislyte_dhalia": "dhalia, dislyte, flower girl, colorful dress, innocent",
    "dislyte_elaine": "elaine, dislyte, knight, armor, sword, determined",
    "dislyte_cecilia": "cecilia, dislyte, nun, white habit, serene expression",
    "dislyte_intisar": "intisar, dislyte, desert dancer, revealing outfit, veil",
    "dislyte_kaylee": "kaylee, dislyte, pop star, colorful hair, stage outfit",
    "dislyte_layla": "layla, dislyte, street fighter, casual outfit, tough",
    "dislyte_lynn": "lynn, dislyte, archer, green outfit, forest",
    "dislyte_melanie": "melanie, dislyte, gothic lolita, dark dress, elegant",
    "dislyte_mona": "mona, dislyte, pop star, pink hair, stage outfit",
    "dislyte_nicole": "nicole, dislyte, spy, black suit, mysterious",
    "dislyte_q": "q, dislyte, hacker, futuristic outfit, short hair",
    "dislyte_ren_si": "ren si, dislyte, traditional chinese outfit, elegant",
    "dislyte_stewart_f": "stewart, female, dislyte, punk, guitar, casual outfit",
    "dislyte_tang_xuan_f": "tang xuan, female, dislyte, monkey king, staff, energetic",
    "dislyte_unaky": "unaky, dislyte, tribal warrior, wild, animalistic",
    "dislyte_victoria": "victoria, dislyte, steampunk, goggles, mechanical parts",
    "dislyte_xiao_yin": "xiao yin, dislyte, traditional chinese dancer, elegant",
    "dislyte_ye_suhua": "ye suhua, dislyte, healer, gentle, flowing dress",
    "dislyte_zhong_nan": "zhong nan, dislyte, traditional chinese warrior, armored",
    "dislyte_anadora": "anadora, dislyte, siren, blue hair, elegant dress",
    "dislyte_bernice": "bernice, dislyte, street dancer, casual outfit, energetic",
    "dislyte_brynn": "brynn, dislyte, archer, forest outfit, focused",
    "dislyte_catherine": "catherine, dislyte, noble, elegant dress, blonde hair",
    "dislyte_chang_pu": "chang pu, dislyte, traditional chinese healer, gentle",
    "dislyte_eugene_f": "eugene, female, dislyte, short hair, sporty outfit",
    "dislyte_freddy_f": "freddy, female, dislyte, punk rock, guitar, wild hair",
    "dislyte_hall_f": "hall, female, dislyte, elegant, long dress, mysterious",
    "dislyte_helena": "helena, dislyte, archer, forest outfit, determined",
    "dislyte_jacob_f": "jacob, female, dislyte, casual outfit, short hair",
    "dislyte_jeanne": "jeanne, dislyte, knight, armor, sword, brave",
    "dislyte_li_ao_f": "li ao, female, dislyte, traditional chinese warrior, armored",
    "dislyte_lu_yi_f": "lu yi, female, dislyte, traditional chinese dancer, elegant",
    "dislyte_mark_f": "mark, female, dislyte, casual outfit, short hair",
    "dislyte_olivia": "olivia, dislyte, elegant, long dress, mysterious",
    "dislyte_sander_f": "sander, female, dislyte, casual outfit, short hair",
    "dislyte_stella": "stella, dislyte, pop star, colorful hair",
    "dislyte_alice": "alice, dislyte, elegant, formal dress",
    "dislyte_arcana": "arcana, dislyte, mystic, flowing robes",
    "dislyte_aurelius_f": "aurelius, female, dislyte, powerful, leader, golden armor",
    "dislyte_bette": "bette, dislyte, spy, sleek outfit, mysterious",
    "dislyte_bonnie": "bonnie, dislyte, cowgirl, western wear, confident",
    "dislyte_celine": "celine, dislyte, singer, stage outfit, microphone",
    "dislyte_corbin_f": "corbin, female, dislyte, mercenary, combat gear, tough",
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
    "lotus_pose": "lotus pose, legs crossed, sitting position", # NEW
    "scissors_pose": "scissors pose, two girls, legs intertwined, scissoring", # NEW
    "hor_split": "horizontal split, legs stretched fully to sides, pelvis on floor, inner thighs visible",
    "ver_split": "vertical split, holding own raised leg",
    "on_back_legs_behind_head": "on back, legs behind head",
    "on_side_leg_up": "on side with leg raised",
    "suspended": "suspended",
    "front_facing": "front to viewer",
    "back_facing": "back to viewer",
    "top_down_view": "shot from above, top-down view",
    "bottom_up_view": "shot from below, bottom-up view",
    "hands_spreading_vagina": "hands spreading vagina",
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
    "furry_bear": "furry bear girl, bear ears, bear tail", # NEW
    "furry_bird": "furry bird girl, bird wings, bird feathers", # NEW
    "furry_mouse": "furry mouse girl, mouse ears, mouse tail", # NEW
    "furry_deer": "furry deer girl, deer antlers, deer ears, deer tail", # NEW
    "furry_tiger": "furry tiger girl, tiger stripes, tiger ears, tiger tail", # NEW
    "furry_lion": "furry lion girl, lion mane, lion ears, lion tail", # NEW
    "furry_snake": "furry snake girl, snake scales, snake tail, snake eyes", # NEW
    "furry_lizard": "furry lizard girl, lizard scales, lizard tail", # NEW
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
