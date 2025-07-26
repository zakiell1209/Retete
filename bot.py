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
    "zzz_haruka": "haruka, zenless zone zero, schoolgirl, pink hair, cheerful",
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
    },
    "toys": {
        "dildo": "Дилдо",
        "huge_dildo": "Большое дилдо",
        "horse_dildo": "Конский дилдо",
        "anal_beads": "Анальные шарики",
        "anal_plug": "Анальная пробка",
    },
    "poses": {
        "doggy": "На четвереньках",
        "standing": "Стоя",
        "squat": "Приседание",
        "lying": "Лежа",
        "hor_split": "Шпагат: нога вверх",
        "ver_split": "На четвереньках: нога вверх",
        "on_back_legs_behind_head": "На спине ноги за головой",
        "on_side_leg_up": "На боку нога вверх",
        "suspended": "Подвешена",
        "front_facing": "Вид спереди",
        "back_facing": "Вид сзади",
        "top_down_view": "Вид сверху",
        "bottom_up_view": "Вид снизу",
        "extreme_acrobatic_inverted_bridge": "Экстремальный мост/стойка на плечах с инверсией",
        "leaning_forward_wall_butt_out": "Наклон у стены",
        "classic_bridge_arching_up": "Мостик",
        "prone_frog_stretch_arms_extended": "На полу: грудь и задница вверх",
        "top_down_voluminous_bow_arms_rhombus": "На полу: задница вверх, ноги согнуты",
    },
    "clothes": {
        "stockings": "Обычные чулки",
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
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "dilated anus, anus stretched, open anus, internal view of anus, anus gaping",
    "dilated_vagina": "dilated vagina, vagina stretched, open pussy, internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "doggy": "doggy style, on all fours, hands on floor",
    "squat": "squatting pose, hands behind head",
    "standing": "standing",
    "lying": "lying down",
    "hor_split": "seated horizontal split, arms support", # Промпт возвращен к старому
    "ver_split": "standing vertical split, one leg on floor, other leg stretched vertically up, almost touching head, both hands supporting raised leg, ankle grip, straightened back, tensed core muscles, open pelvis, emphasizes extreme stretch", # Промпт возвращен к старому
    "on_back_legs_behind_head": "on back, legs behind head",
    "on_side_leg_up": "on side with leg raised",
    "suspended": "suspended",
    "front_facing": "front to viewer",
    "back_facing": "back to viewer",
    "top_down_view": "shot from above, top-down view",
    "bottom_up_view": "shot from below, bottom-up view",
    "extreme_acrobatic_inverted_bridge": "extreme acrobatic, deep inversion, bridge, shoulder stand, hand support, head on floor, hair spread, shoulders on surface, hands bent at elbows in front of face, palms on floor, extremely arched back, raised buttocks, buttocks at head level, facing viewer, legs spread wide, acute angle, knees slightly bent, feet touching floor, toes pointed, center of gravity between shoulders and feet, emphasizes buttocks, back curve, thigh anatomy, acrobatic flexibility",
    "leaning_forward_wall_butt_out": "leaning forward, hands on wall, partially undressed, head tilted, head turned back to viewer, looking over shoulder, raised shoulders, straight back, parallel to floor, slight arch, buttocks pushed back, emphasized by pose, jeans pulled down to knees, legs spread shoulder-width apart, knees half-bent, relaxed, stable", # Промпт возвращен к старому
    "classic_bridge_arching_up": "classic bridge, supported on palms and feet, body arched upwards, full back arch, stomach facing up, head tilted back, neck stretched, fingers and toes pointed forward",
    "prone_frog_stretch_arms_extended": "prone frog stretch, arms extended, chest on floor, buttocks up", # Промпт возвращен к старому
    "top_down_voluminous_bow_arms_rhombus": "top-down view, voluminous bow, arms rhombus, chest on floor, buttocks up, knees bent, feet on floor", # Промпт возвращен к старому
    "stockings": "stockings",
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
    "body_fat": "chubby, plump, slightly overweight, soft body, curvy, fleshy", # Промпт обновлен для "небольшого избыточного веса"
    "age_loli": "klee (genshin impact), very young girl, child-like features, playful, energetic, cute, short dress", # Промпт обновлен для "Кли из геншин импакт"
    "age_milf": "milf",
    "age_21": "21 year old",
    "cum": "cum covered",
    "belly_bloat": "belly bulge, pregnant looking belly",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "futanari",
    "femboy": "male, boy, very feminine body, femboy, androgynous, flat chest, penis, testicles, thin waist, wide hips, boyish hips, no breasts",
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
    "pain_face": "pain expression, grimace, suffering face", # Промпт обновлен
    "ecstasy_face": "ecstasy expression, orgasmic face, flushed cheeks", # Промпт обновлен
    "gold_lipstick": "gold lipstick",
    "nipple_piercing": "nipple piercing",
    "clitoral_piercing": "clitoral piercing",
    "foot_fetish": "foot fetish",
    "footjob": "footjob",
    "anus_piercing": "anus piercing",
    "vagina_piercing": "vagina piercing",
    "gag": "gag, mouth gag",
    "blindfold": "blindfold",
    "horse_sex": "horse sex, mare sex, horse fucking, human riding horse, horse penis",
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

# --- Начало старого кода (до изменений) ---

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать генерацию", callback_data='start_generation'))
    bot.send_message(chat_id, "Привет! Я бот для генерации изображений. Нажмите кнопку, чтобы начать.", reply_markup=markup)

# Обработка callback_query
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if call.data == 'start_generation':
        user_settings[chat_id] = {'prompt': '', 'negative_prompt': '', 'current_category': None, 'selected_tags': []}
        send_main_menu(chat_id)
    elif call.data.startswith('category_'):
        category_key = call.data.replace('category_', '')
        user_settings[chat_id]['current_category'] = category_key
        send_tag_menu(chat_id, category_key)
    elif call.data.startswith('tag_'):
        tag_key = call.data.replace('tag_', '')
        toggle_tag(chat_id, tag_key)
        send_tag_menu(chat_id, user_settings[chat_id]['current_category'])
    elif call.data == 'back_to_main_menu':
        user_settings[chat_id]['current_category'] = None
        send_main_menu(chat_id)
    elif call.data == 'generate_image':
        generate_image(chat_id)
    elif call.data == 'reset_settings':
        user_settings[chat_id] = {'prompt': '', 'negative_prompt': '', 'current_category': None, 'selected_tags': []}
        bot.send_message(chat_id, "Настройки сброшены. Теперь вы можете начать с чистого листа.")
        send_main_menu(chat_id)
    elif call.data.startswith('char_category_'):
        char_category_key = call.data.replace('char_category_', '')
        send_character_subcategory(chat_id, char_category_key)
    elif call.data.startswith('char_tag_'):
        char_tag_key = call.data.replace('char_tag_', '')
        toggle_tag(chat_id, char_tag_key)
        # Если нужно вернуться в подкатегорию персонажей после выбора тега
        current_char_category = next((c_key for c_key, c_tags in TAGS['characters'].items() if char_tag_key in c_tags), None)
        if current_char_category: # Это не сработает, нужно найти категорию по char_tag_key
            found_char_category = None
            for cat_id, cat_name in CHARACTER_CATEGORIES.items():
                if char_tag_key.startswith(cat_id):
                    found_char_category = cat_id
                    break
            if found_char_category:
                send_character_subcategory(chat_id, found_char_category)
            else:
                send_tag_menu(chat_id, 'characters') # Fallback
        else:
            send_tag_menu(chat_id, 'characters') # Fallback

    elif call.data == 'back_to_character_categories':
        send_tag_menu(chat_id, 'characters')


def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f'category_{key}'))
    
    current_prompt = user_settings[chat_id].get('prompt', '')
    selected_tags_display = ", ".join([TAGS[cat][tag] for cat in TAGS for tag in user_settings[chat_id].get('selected_tags', []) if tag in TAGS[cat]])
    
    status_text = f"Текущий промпт: {current_prompt}\nВыбранные теги: {selected_tags_display if selected_tags_display else 'Нет'}"
    
    markup.add(types.InlineKeyboardButton("Сгенерировать изображение", callback_data='generate_image'))
    markup.add(types.InlineKeyboardButton("Сбросить настройки", callback_data='reset_settings'))
    
    bot.send_message(chat_id, status_text + "\n\nВыберите категорию тегов:", reply_markup=markup)

def send_tag_menu(chat_id, category_key):
    markup = types.InlineKeyboardMarkup(row_width=2)
    selected_tags = user_settings[chat_id].get('selected_tags', [])

    if category_key == 'characters':
        for char_cat_key, char_cat_name in CHARACTER_CATEGORIES.items():
            markup.add(types.InlineKeyboardButton(char_cat_name, callback_data=f'char_category_{char_cat_key}'))
    else:
        tags_in_category = TAGS.get(category_key, {})
        for tag_key, tag_name in tags_in_category.items():
            emoji = "✅ " if tag_key in selected_tags else ""
            markup.add(types.InlineKeyboardButton(f"{emoji}{tag_name}", callback_data=f'tag_{tag_key}'))

    markup.add(types.InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu'))
    markup.add(types.InlineKeyboardButton("Сгенерировать изображение", callback_data='generate_image'))
    
    current_prompt = user_settings[chat_id].get('prompt', '')
    selected_tags_display = ", ".join([TAGS[cat][tag] for cat in TAGS for tag in selected_tags if tag in TAGS[cat]])
    
    status_text = f"Текущий промпт: {current_prompt}\nВыбранные теги: {selected_tags_display if selected_tags_display else 'Нет'}"
    
    bot.send_message(chat_id, status_text + "\n\nВыберите теги:", reply_markup=markup)

def send_character_subcategory(chat_id, char_category_key):
    markup = types.InlineKeyboardMarkup(row_width=2)
    selected_tags = user_settings[chat_id].get('selected_tags', [])

    # Filter TAGS['characters'] to only show tags belonging to this subcategory
    # This assumes character tags are prefixed with their category key, e.g., 'dxd_rias'
    
    # We need to iterate through CHARACTER_EXTRA keys that belong to this subcategory
    filtered_char_tags = {k: v for k, v in TAGS['characters'].items() if k.startswith(char_category_key + '_')}

    for char_tag_key, char_tag_name in filtered_char_tags.items():
        emoji = "✅ " if char_tag_key in selected_tags else ""
        markup.add(types.InlineKeyboardButton(f"{emoji}{char_tag_name}", callback_data=f'char_tag_{char_tag_key}'))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад к категориям персонажей", callback_data='back_to_character_categories'))
    markup.add(types.InlineKeyboardButton("Сгенерировать изображение", callback_data='generate_image'))

    current_prompt = user_settings[chat_id].get('prompt', '')
    selected_tags_display = ", ".join([TAGS[cat][tag] for cat in TAGS for tag in selected_tags if tag in TAGS[cat]])
    
    status_text = f"Текущий промпт: {current_prompt}\nВыбранные теги: {selected_tags_display if selected_tags_display else 'Нет'}"

    bot.send_message(chat_id, status_text + f"\n\nВыберите персонажей для категории: {CHARACTER_CATEGORIES[char_category_key]}", reply_markup=markup)


def toggle_tag(chat_id, tag_key):
    if tag_key in user_settings[chat_id]['selected_tags']:
        user_settings[chat_id]['selected_tags'].remove(tag_key)
        bot.send_message(chat_id, f"Тег '{get_tag_display_name(tag_key)}' удален.")
    else:
        user_settings[chat_id]['selected_tags'].append(tag_key)
        bot.send_message(chat_id, f"Тег '{get_tag_display_name(tag_key)}' добавлен.")

def get_tag_display_name(tag_key):
    # Ищем тег во всех категориях
    for category_tags in TAGS.values():
        if tag_key in category_tags:
            return category_tags[tag_key]
    return tag_key # Если не найдено, вернуть сам ключ

def get_replicate_prompt(selected_tags):
    positive_parts = []
    negative_parts = []

    for tag_key in selected_tags:
        if tag_key in TAG_PROMPTS:
            positive_parts.append(TAG_PROMPTS[tag_key])
        else:
            # Fallback for tags not in TAG_PROMPTS (shouldn't happen if TAG_PROMPTS is comprehensive)
            positive_parts.append(tag_key.replace('_', ' ')) 
    
    # Добавьте ваш базовый положительный промпт здесь
    base_positive_prompt = "best quality, masterpiece, highres, original, extremely detailed, perfect lighting, photorealistic, intricate detail"
    
    # Добавьте ваш базовый негативный промпт здесь
    base_negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name"

    return f"{base_positive_prompt}, {', '.join(positive_parts)}", base_negative_prompt

def generate_image(chat_id):
    prompt_text, negative_prompt_text = get_replicate_prompt(user_settings[chat_id].get('selected_tags', []))
    
    bot.send_message(chat_id, "Генерирую изображение... это может занять до минуты.")
    bot.send_chat_action(chat_id, 'upload_photo')

    # Construct the payload for Replicate API
    payload = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt_text,
            "negative_prompt": negative_prompt_text,
            "width": 768,
            "height": 768,
            "num_outputs": 1,
            "num_inference_steps": 50,
            "guidance_scale": 7.5
        }
    }

    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Step 1: Create a prediction
        response = requests.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        prediction_data = response.json()
        
        prediction_id = prediction_data.get("id")
        if not prediction_id:
            bot.send_message(chat_id, "Ошибка: не удалось получить ID предсказания от Replicate.")
            print(f"Prediction creation failed: {prediction_data}")
            return

        # Step 2: Poll for the result
        image_url = None
        for _ in range(60): # Poll for up to 60 seconds (adjust as needed)
            time.sleep(1)
            poll_response = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
            poll_response.raise_for_status()
            poll_data = poll_response.json()
            
            status = poll_data.get("status")
            if status == "succeeded":
                output = poll_data.get("output")
                if output and isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                    break
            elif status == "failed":
                bot.send_message(chat_id, f"Генерация изображения не удалась. Replicate вернул ошибку: {poll_data.get('error', 'Неизвестная ошибка')}")
                print(f"Prediction failed: {poll_data}")
                return
            elif status in ["starting", "processing"]:
                # Still waiting
                continue
            else:
                bot.send_message(chat_id, f"Неизвестный статус генерации: {status}")
                print(f"Unknown prediction status: {status}, data: {poll_data}")
                return

        if image_url:
            bot.send_photo(chat_id, image_url)
        else:
            bot.send_message(chat_id, "Не удалось получить изображение. Пожалуйста, попробуйте еще раз.")

    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"Ошибка при обращении к API Replicate: {e}")
        print(f"Requests error: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"Произошла непредвиденная ошибка: {e}")
        print(f"Unexpected error: {e}")


# Настройка вебхука для Render
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200

# Запуск Flask приложения
if __name__ == '__main__':
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL + API_TOKEN)
        print(f"Webhook set to: {WEBHOOK_URL + API_TOKEN}")
        app.run(host='0.0.0.0', port=PORT)
    else:
        print("WEBHOOK_URL not set, falling back to polling.")
        bot.polling(none_stop=True)

