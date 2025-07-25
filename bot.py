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
    "pokemon_chars": "📺 Pokémon (персонажи)",
    "lol": "🎮 League of Legends",
    "mlp": "📺 My Little Pony",
}

# --- Определяем CHARACTER_EXTRA ДО TAG_PROMPTS ---
CHARACTER_EXTRA = {
    "dxd_rias": "rias gremory, red long hair, blue eyes, pale skin, large breasts, highschool dxd",
    "dxd_akeno": "akeno himejima, long black hair, purple eyes, large breasts, highschool dxd",
    "dxd_xenovia_quarta": "xenovia quarta, highschool dxd, blue hair, short hair, sword, holy sword, devil wings, nun uniform",
    "dxd_serafall_leviathan": "serafall leviathan, highschool dxd, magical girl outfit, pink hair, magical wand, devil, large breasts",
    "dxd_asia_argento": "asia argento, highschool dxd, blonde hair, long hair, nun, innocent, healing magic, dragon slayer, devil wings",
    "dxd_koneko_toujou": "koneko toujou, highschool dxd, white hair, cat ears, cat tail, small breasts, stoic expression",
    "dxd_shidou_irina": "shidou irina, highschool dxd, blonde hair, twin tails, energetic, holy sword, angel wings, exorcist",
    "dxd_gasper_vladi": "gasper vladi, highschool duld, male, trap, feminine clothing, long blonde hair, shy, vampire, crossdresser",
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
    "hsr_peia": "peia, honkai star rail, foxian, healer, long hair",
    "hsr_sushang": "sushang, honkai star rail, sword, knight, chicken, red hair",
    "hsr_natasha": "natasha, honkai star rail, doctor, blonde hair, medical coat",
    "hsr_hook": "hook, honkai star rail, child, red hair, big hat, destruction",
    "hsr_pela": "pela, honkai star rail, glasses, detective, blue hair, short hair",
    "hsr_qingque": "qingque, honkai star rail, mahjong, green hair, lazy",
    "hsr_yukong": "yukong, honkai star rail, foxian, pilot, mature, elegant",
    "hsr_guinaifen": "guinaifen, honkai star rail, streamer, fire performer, pink hair",
    "hsr_huohuo": "huohuo, honkai star rail, green hair, fox girl, exorcist, ghost",
    "hsr_xueyi": "xueyi, honkai star rail, puppet, pink hair, executioner, mask",
    "hsr_hanabi": "hanabi, honkai star rail, pink hair, elegant dress, theatrical",
    "hsr_robin": "robin, honkai star rail, idol, blonde hair, singer, elegant dress",
    "hsr_aventurine_f": "aventurine, female, honkai star rail, blonde hair, gambler, suit",

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
    "streetfighter_ed": "ed, street fighter, female, boxer, psychic powers, blonde hair",
    "streetfighter_fang": "f.a.n.g, female, street fighter, poison, long clothes",
    "streetfighter_e_honda_f": "e. honda, female, street fighter, sumo wrestler, large body",

    # Atomic Heart
    "atomicheart_twins": "robot, twin sisters, black bodysuit, black hair, white hair, atomic heart",

    # Bleach
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
        
    # Pokémon (персонажи-люди)
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
        "extreme_acrobatic_inverted_bridge": "Экстремальный мост/стойка на плечах с инверсией",
        "leaning_forward_wall_butt_out": "Наклон вперёд у стены",
        "standing_vertical_split_holding_ankle": "Вертикальный шпагат стоя с поддержкой",
        "seated_double_split_holding_feet": "Поза лодки / двойной шпагат вверх",
        "deep_sumo_squat_knees_apart": "Глубокий присед (сумо-поза)",
        "standing_horizontal_split_arms_out": "Горизонтальный шпагат стоя с балансом",
        "classic_bridge_arching_up": "Мостик",
        "seated_horizontal_split_arms_support": "Горизонтальный шпагат сидя с опорой",
        "prone_frog_stretch_arms_extended": "Пролёт вперёд, плечевой растяг",
        "standing_deep_forward_bend_hands_on_floor": "Стоячий глубокий прогиб с опорой на руки",
        "standing_deep_forward_bow_forearms_clasped": "Наклон со сведёнными предплечьями",
        "top_down_voluminous_bow_arms_rhombus": "Объёмный поклон сверху (вид сверху)",
        "inverted_leg_over_shoulder_supine": "Перевёрнутый сгиб с коленом над плечом",
        "casual_seated_open_knees_feet_on_floor": "Лёгкая поза сидя, колени разведены"
    },
    "clothes": {
        "stockings": "Обычные чулки", # Общий тег для чулок
        "stockings_fishnet": "Чулки сеточкой",
        "stockings_black": "Чулки: Черные",
        "stockings_white": "Чулки: Белые",
        "stockings_pink": "Чулки: Розовые",
        "stockings_red": "Чулки: Красные",
        "stockings_gold": "Чулки: Золотые",
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
        "pokemon_lusamine": "Лусамине"
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

        # Bleach
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
    }
}

# --- Промпты для модели ---
TAG_PROMPTS = {
    # Сначала добавляем промпты из CHARACTER_EXTRA
    **CHARACTER_EXTRA, # Включаем промпты персонажей
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "dilated anus, anus stretched, open anus, internal view of anus, anus gaping",
    "dilated_vagina": "dilated vagina, vagina stretched, open pussy, internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus",
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",
    "two_dildos_one_hole": "two dildos inserted, two dildos into one orifice",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber"
    ),
    "urethral_dildo": "urethral dildo, dildo in urethra, dildo inserted into urethra",
    "two_dildos_anus_vagina": "one dildo inserted into anus, one dildo inserted into vagina",
    "doggy": "doggy style, on all fours, hands on floor",
    "squat": "squatting pose, hands behind head",
    "standing": "standing",
    "lying": "lying down",
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
    "lotus_pose": "lotus pose",
    "scissors_pose": "scissors pose, two girls, legs interlocked",
    # Обновленные промпты для поз
    "extreme_acrobatic_inverted_bridge": "extreme acrobatic, deep inversion, bridge, shoulder stand, hand support, head on floor, hair spread, shoulders on surface, hands bent at elbows in front of face, palms on floor, extremely arched back, raised buttocks, buttocks at head level, facing viewer, legs spread wide, acute angle, knees slightly bent, feet touching floor, toes pointed, center of gravity between shoulders and feet, emphasizes buttocks, back curve, thigh anatomy, acrobatic flexibility",
    "leaning_forward_wall_butt_out": "leaning forward, hands on wall, partially undressed, head tilted, head turned back to viewer, looking over shoulder, raised shoulders, straight back, parallel to floor, slight arch, buttocks pushed back, emphasized by pose, jeans pulled down to knees, legs spread shoulder-width apart, knees half-bent, relaxed, stable",
    "standing_vertical_split_holding_ankle": "standing vertical split, one leg on floor, other leg stretched vertically up, almost touching head, both hands supporting raised leg, ankle grip, straightened back, tensed core muscles, open pelvis, emphasizes extreme stretch",
    "seated_double_split_holding_feet": "seated, both legs raised 90+ degrees up, hands holding both feet, torso tilted back, tensed back, stable, static, requires strength",
    "deep_sumo_squat_knees_apart": "deep sumo squat, squatting, knees spread to sides, heels on floor, pelvis deep, hands down for balance, straight spine, chest raised",
    "standing_horizontal_split_arms_out": "standing horizontal split, one leg on floor, other leg out horizontally, arms spread for balance, body strictly vertical, open pelvis, strong balance control",
    "classic_bridge_arching_up": "classic bridge, supported on palms and feet, body arched upwards, full back arch, stomach facing up, head tilted back, neck stretched, fingers and toes pointed forward",
    "seated_horizontal_split_arms_support": "seated horizontal split, sitting, one leg forward, one leg back, horizontal split, hands on floor for support, torso slightly raised, pelvis as low as possible to floor, straight back, elongated neck",
    "prone_frog_stretch_arms_extended": "prone frog stretch, lying on stomach, arms extended forward, palms on floor, forearms on floor, shoulders pronated, shoulder blades stretched outward, upper back elongated, slight lumbar arch, hips raised, thighs splayed outward, wide frog stretch, knees turned out, shins back, feet relaxed toes back, head tilted forward-down, cheek or chin near floor, emphasizes hip flexibility, adductors, inner thighs, shoulder girdle stretch, 'pulled forward with whole body' dynamic",
    "standing_deep_forward_bend_hands_on_floor": "standing deep forward bend, feet much wider than shoulder-width, knees slightly bent or almost straight, toes slightly outward, hips high, forward bend from hips, long forward bend, lumbar and thoracic spine stretch towards floor, stomach towards thighs, palms on floor, fingers on floor in front of feet or under shoulders, elbows softly bent, head and neck relaxed down, crown or face back through legs, weight distributed between feet and hands, most weight in legs, acrobatic pose, deep wide forward fold",
    "standing_deep_forward_bow_forearms_clasped": "standing deep forward bow, feet together or very close, knees slightly bent, hips strongly pulled back and up, torso tilted forward, buttocks at highest point, long bend, emphasized lumbar arch, forearms clasped in front between thighs, forming 'heart' or 'cup' shape, shoulders inward, elbows bent, head down towards floor or slightly back, dynamic bowing/showing bend, exaggerated style",
    "top_down_voluminous_bow_arms_rhombus": "top-down view, deep bow, arms forming rhombus/heart below torso, foreshortened perspective, shoulders drawn forward, hands joined under body, rounded volume of gluteal-pelvic area, spherical shape, legs together, soft knees",
    "inverted_leg_over_shoulder_supine": "inverted leg over shoulder, lying on back, supine inverted leg fold, hips lifted, legs bent, legs brought back over head, one thigh crosses face line, other abducted to side, twisted inversion, strong lumbar bend, compressed abdomen, one arm embracing thigh/shin from above, other supporting position from side or on floor, head and neck on floor, chin closer to chest, combination of yoga plow, twist, acrobatic contortion",
    "casual_seated_open_knees_feet_on_floor": "casual seated pose, sitting on buttocks, knees bent and spread, feet on floor, heels closer to pelvis or slightly forward, back slightly tilted back or straight, torso slightly forward, hands resting on thighs/knees or holding clothing edges, neutral balance support, head looking forward at viewer",
    "stockings": "stockings", # Общий промпт для чулок
    "stockings_fishnet": "fishnet stockings",
    "stockings_black": "black stockings",
    "stockings_white": "white stockings",
    "stockings_pink": "pink stockings",
    "stockings_red": "red stockings",
    "stockings_gold": "gold stockings",
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
    "furry_bear": "furry bear girl, bear costume",
    "furry_bird": "furry bird girl, bird costume",
    "furry_mouse": "furry mouse girl, mouse costume",
    "furry_deer": "furry deer girl, deer costume",
    "furry_tiger": "furry tiger girl, tiger costume",
    "furry_lion": "furry lion girl, lion costume",
    "furry_snake": "furry snake girl, snake costume",
    "furry_lizard": "furry lizard girl, lizard costume",
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
    "horse_sex": "horse sex, mare sex, horse fucking, human riding horse, horse penis",
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
    "goodra": "goodra, pokemon"
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

def tag_menu(category, selected_tags, char_subcategory=None):
    """Создает меню выбора тегов внутри определенной категории."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    tags_to_display = {}
    if category == "characters" and char_subcategory:
        # Фильтруем теги персонажей по выбранной подкатегории
        for tag_key, tag_name in TAGS[category].items():
            # Префикс подкатегории должен соответствовать началу ключа тега
            # Добавлена проверка на наличие подкатегории в начале ключа
            # и специальная обработка для pokemon_chars
            if char_subcategory == "pokemon_chars" and tag_key.startswith("pokemon_"):
                tags_to_display[tag_key] = tag_name
            elif tag_key.startswith(char_sub + "_"):
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
    user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1}
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
        user_settings[cid] = {"tags": [], "last_cat": None, "last_char_sub": None, "num_images": 1}
        bot.send_message(cid, "Настройки сброшены. Начнем заново!", reply_markup=main_menu())
    
    elif data == "ignore":
        bot.answer_callback_query(call.id)

# --- Функция для определения категории тега ---
def tag_category(tag):
    """Определяет категорию, к которой относится тег."""
    for cat, items in TAGS.items():
        if tag in items:
            # ИСПРАВЛЕНИЕ: Добавляем явную обработку для категории "furry"
            if cat == "furry":
                return "furry"
            # Остальная логика остаётся как была
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
            
            # Для покемонов (существ, не персонажей-людей)
            if cat == "pokemon" and not tag.startswith("pokemon_"):
                return "pokemon"
            
            # Для всех остальных персонажей (включая персонажей покемонов, таких как Джесси)
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
    
    # Приоритет большим грудям, если обе выбраны
    if "big_breasts" in unique and "small_breasts" in unique:
        unique.remove("small_breasts") 
    
    # Костюм коровы уже включён в furry_cow, если выбрана furry_cow
    if "furry_cow" in unique:
        unique.discard("cow_costume") 

    # Обработка тега "stockings" и его цветов
    # Если выбраны конкретные чулки, убираем общий тег "stockings", чтобы избежать дублирования
    specific_stocking_chosen = False
    for stocking_type in ["stockings_fishnet", "stockings_black", "stockings_white", "stockings_pink", "stockings_red", "stockings_gold"]:
        if stocking_type in unique:
            specific_stocking_chosen = True
            break
    
    if specific_stocking_chosen and "stockings" in unique:
        unique.discard("stockings")


    # Обработка тега "femboy"
    if "femboy" in unique:
        unique.discard("big_breasts")
        unique.discard("small_breasts")
        base_negative += ", breasts, female breasts"


    # Группировка по категориям
    for tag in unique:
        key = tag_category(tag)
        if key:
            # Используем TAG_PROMPTS для получения промпта
            prompt_from_map = TAG_PROMPTS.get(tag)
            if prompt_from_map: # Убедимся, что промпт существует
                priority[key].append(prompt_from_map)
            else:
                # Если промпт для тега не найден в TAG_PROMPTS (чего быть не должно после исправления),
                # добавляем сам тег как промпт.
                priority[key].append(tag.replace('_', ' '))


    prompt_parts = base[:]
    # Порядок добавления важен
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
                "seed": -1
            }
        }

        r = requests.post(url, headers=headers, json=json_data)
        if r.status_code != 201:
            print(f"Ошибка при отправке предсказания: {r.status_code} - {r.text}")
            print(f"Request JSON: {json_data}")
            return None

        status_url = r.json()["urls"]["get"]

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
