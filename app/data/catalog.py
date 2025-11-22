from __future__ import annotations

from app.schemas.course import Author, Course, Review

COURSES: list[Course] = [
    Course(
        slug="ai-for-beginners",
        title="AI для повседневной работы",
        tagline="ChatGPT, Claude и нейросети для ваших задач",
        description=(
            "Научитесь использовать ChatGPT, Claude и другие AI-инструменты для решения рабочих задач. "
            "Освоите промт-инжиниринг, автоматизацию рутины и создание контента с помощью нейросетей."
        ),
        price=24000,
        duration_weeks=4,
        level="beginner",
        format="live",
        technologies=["ChatGPT", "Claude", "Gemini", "Notion AI"],
        badges=["Новичкам", "Практика"],
        cover="/static/images_magic/ai_forwork.jfif",
        highlight="Начните использовать AI уже на первой неделе обучения, без технического бэкграунда.",
        author=Author(
            name="Анна Светова",
            title="AI-тренер для новичков",
            avatar="https://images.unsplash.com/photo-1494790108377-be9c29b29330",
        ),
    ),
    Course(
        slug="vibe-coding",
        title="Вайбкодинг: создай свой проект",
        tagline="Разработка без программирования с AI",
        description=(
            "Создайте свой сайт, приложение или сервис без знания кода! Используйте V0, Bolt.new, "
            "Cursor AI и другие инструменты для превращения идеи в готовый продукт за неделю."
        ),
        price=32000,
        duration_weeks=5,
        level="beginner",
        format="hybrid",
        technologies=["V0", "Bolt.new", "Cursor AI", "Replit", "Lovable"],
        badges=["No-Code", "Тренд"],
        cover="/static/images_magic/vibe_coding.jfif",
        highlight="От идеи до MVP за 5 недель. Реальный проект в портфолио без знания программирования.",
        author=Author(
            name="Максим Вайбер",
            title="Vibe Coding Expert",
            avatar="https://images.unsplash.com/photo-1500648767791-00dcc994a43e",
        ),
    ),
    Course(
        slug="ai-visual-generation",
        title="Генерация визуала без дизайнера",
        tagline="Midjourney, DALL-E и Stable Diffusion",
        description=(
            "Научитесь создавать профессиональные изображения, логотипы, иллюстрации и дизайн с помощью "
            "AI. От простых промтов до сложных композиций и коммерческого использования."
        ),
        price=28000,
        duration_weeks=5,
        level="beginner",
        format="live",
        technologies=["Midjourney", "DALL-E", "Stable Diffusion", "Leonardo AI"],
        badges=["Дизайн", "Креатив"],
        cover="/static/images_magic/Generate_visual.jfif",
        highlight="Создавайте визуал для соцсетей, презентаций и бизнеса без дизайнера.",
        author=Author(
            name="Дарья Артова",
            title="AI Art Director",
            avatar="https://images.unsplash.com/photo-1438761681033-6461ffad8d80",
        ),
    ),
    Course(
        slug="ai-copywriting",
        title="AI-копирайтинг и контент",
        tagline="Тексты для бизнеса с нейросетями",
        description=(
            "Освойте создание продающих текстов, контент-планов, постов для соцсетей и SEO-статей с "
            "помощью AI. Научитесь работать с ChatGPT, Jasper, Copy.ai для маркетинга."
        ),
        price=26000,
        duration_weeks=4,
        level="beginner",
        format="hybrid",
        technologies=["ChatGPT", "Jasper", "Copy.ai", "Writesonic"],
        badges=["Контент", "Маркетинг"],
        cover="/static/images_magic/ai_copyright.jfif",
        highlight="Генерируйте качественный контент в 10 раз быстрее с помощью AI-инструментов.",
        author=Author(
            name="Елена Словова",
            title="Content Strategist",
            avatar="https://images.unsplash.com/photo-1487412720507-e7ab37603c6f",
        ),
    ),
    Course(
        slug="comfyui-lab",
        title="ComfyUI и визуальный продакшн",
        tagline="Пайплайны для креатива и motion-дизайна",
        description=(
            "Собираем графы в ComfyUI, работаем с ControlNet, правим свет и текстуры, собираем "
            "пак графики для рекламных кампаний."
        ),
        price=65000,
        duration_weeks=8,
        level="junior",
        format="live",
        technologies=["ComfyUI", "Stable Diffusion", "After Effects"],
        badges=["Design", "Visual"],
        cover="/static/images_magic/comfyui.jfif",
        highlight="Получите уверенный стек для создания визуала под бренд без подрядчиков.",
        author=Author(
            name="Савва Лис",
            title="Creative Director",
            avatar="https://images.unsplash.com/photo-1500648767791-00dcc994a43e",
        ),
    ),
    Course(
        slug="ai-automation",
        title="AI-автоматизация процессов",
        tagline="Make, n8n и кастомные агенты для рутины",
        description=(
            "Учимся описывать процессы, собирать сценарии в Make и n8n, подключать GPT и проверять "
            "результаты. От маркетинга до бэк-офиса."
        ),
        price=72000,
        duration_weeks=9,
        level="middle",
        format="hybrid",
        technologies=["Make", "n8n", "Zapier", "OpenAI API"],
        badges=["Automation", "Ops"],
        cover="/static/images_magic/ai_automatisation.jfif",
        highlight="Запустите автоматизированные пайплайны и освободите часы команды.",
        author=Author(
            name="Маргарита Шторм",
            title="Head of Automation",
            avatar="https://images.unsplash.com/photo-1527980965255-d3b416303d12",
        ),
    ),
    Course(
        slug="voice-agents",
        title="Голосовые ассистенты и поддержка",
        tagline="SpeechKit, ElevenLabs и сценарии общения",
        description=(
            "Проектируем персонажей, пишем сценарии, подключаем CRM и телефонию, тестируем речь и "
            "тональность на реальных клиентах."
        ),
        price=56000,
        duration_weeks=6,
        level="junior",
        format="live",
        technologies=["SpeechKit", "ElevenLabs", "LangChain"],
        badges=["Voice", "CX"],
        cover="/static/images_magic/voice_assist.jfif",
        highlight="Соберёте голосового помощника, который закрывает задачи поддержки и продаж.",
        author=Author(
            name="Остап Янтарь",
            title="Voice AI Lead",
            avatar="https://images.unsplash.com/photo-1527980965255-d3b416303d12",
        ),
    ),
    Course(
        slug="rag-systems",
        title="RAG-системы и корпоративные знания",
        tagline="Как собрать поиск и память для компании",
        description=(
            "Строим витрину знаний на pgvector и Neo4j, организуем ingestion, пишем сервис доступа и "
            "метрики качества ответов."
        ),
        price=92000,
        duration_weeks=12,
        level="middle",
        format="hybrid",
        technologies=["pgvector", "Neo4j", "LangSmith", "FastAPI"],
        badges=["RAG", "Data"],
        cover="/static/images_magic/rag_system.jfif",
        highlight="Настроите поиск по документам и чат с памятью для вашей команды.",
        author=Author(
            name="Ева Кобальт",
            title="Lead ML Engineer",
            avatar="https://images.unsplash.com/photo-1544723795-3fb6469f5b39",
        ),
    ),
    Course(
        slug="ai-strategy",
        title="AI-стратегия для бизнеса",
        tagline="Как выбрать направления и считать отдачу",
        description=(
            "Разбираем экономику проектов, compliance, запуск пилотов и масштабирование. Готовим "
            "дорожную карту внедрения ИИ для компании."
        ),
        price=81000,
        duration_weeks=7,
        level="senior",
        format="recorded",
        technologies=["OpenAI API", "YandexGPT", "Vertex AI"],
        badges=["Leadership", "Strategy"],
        cover="/static/images_magic/ai_for_business.jfif",
        highlight="Сформируете понятный план по развитию нейросетей в бизнесе.",
        author=Author(
            name="Инга Вуаль",
            title="AI Strategy Lead",
            avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
        ),
    ),
]

REVIEWS: list[Review] = [
    Review(
        author="Лев Васильев",
        role="CMO, Macan Digital",
        quote="За первую неделю внедрили промт-воркфлоу из курса и удвоили выработку контента.",
        avatar="https://images.unsplash.com/photo-1521572267360-ee0c2909d518",
    ),
    Review(
        author="Алина Рудая",
        role="Product Owner, EdTech Lab",
        quote="Истории из практики помогли убедить команду в ценности ИИ, теперь строим RAG.",
        avatar="https://images.unsplash.com/photo-1544005313-94ddf0286df2",
    ),
    Review(
        author="Илья Озёрный",
        role="CEO, WowStudio",
        quote="Нейромагический UI влюбляет клиентов. Команда даёт поддержку и честную экспертизу.",
        avatar="https://images.unsplash.com/photo-1544723795-3fb6469f5b39",
    ),
    Review(
        author="Марина Светлова",
        role="Начинающий маркетолог",
        quote="Никогда не думала, что смогу создавать дизайн сама. После курса по Midjourney делаю картинки для соцсетей за 5 минут!",
        avatar="https://images.unsplash.com/photo-1438761681033-6461ffad8d80",
    ),
    Review(
        author="Дмитрий Новиков",
        role="Студент, без опыта в IT",
        quote="Пришёл полным новичком, боялся что не разберусь. Преподаватели объясняют так просто, что через месяц уже помогаю друзьям с ChatGPT!",
        avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
    ),
]

