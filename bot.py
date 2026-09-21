import re
import sys
from pathlib import Path

# Гарантируем корректный ввод/вывод UTF-8 в консоли Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

FAQ_FILE = Path(__file__).parent / "faq.txt"

# Корни ключевых слов по 5 ключевым темам репетиции
TOPIC_KEYWORDS = {
    0: {"врем", "расписан", "длит", "когд", "старт", "начал", "законч", "тайминг", "график", "часов"},
    1: {"команд", "состав", "участник", "человек", "рол", "размер", "капитан", "людей"},
    2: {"трек", "тем", "направлен", "задач", "кейс", "разработ", "разрабат", "прототип", "бот"},
    3: {"сдач", "сдат", "дедлайн", "ссылк", "гит", "репо", "репозитор", "формат", "куда", "отправ"},
    4: {"приз", "наград", "победител", "мерч", "подар", "выигрыш", "бонус", "сертификат", "диплом"},
}

STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все",
    "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по",
    "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "о", "об", "про",
    "какой", "какая", "какое", "какие", "ли", "или", "мы", "будет"
}


def stem_word(word: str) -> str:
    """Упрощённый стемминг для русского языка: усечение стандартных окончаний."""
    word = word.lower().strip()
    endings = (
        "ями", "ами", "ого", "его", "ому", "ему", "ыми", "ей", "ой", "ий", "ый",
        "ам", "ям", "ах", "ях", "ов", "ев", "ом", "ем", "ие", "ые", "ое", "ее",
        "ать", "еть", "ить", "ся", "сь",
        "а", "е", "и", "й", "о", "у", "ы", "ь", "я"
    )
    for ending in endings:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[:-len(ending)]
    return word


def tokenize(text: str) -> list[str]:
    """Разбивка текста на слова с фильтрацией стоп-слов."""
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def load_faq(filepath: Path) -> list[dict]:
    """Загрузка пар вопрос-ответ из faq.txt."""
    if not filepath.exists():
        raise FileNotFoundError(f"Файл {filepath} не найден!")

    items = []
    current_q = None
    current_a = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Q:") or line.startswith("В:"):
                if current_q and current_a:
                    items.append({"question": current_q, "answer": current_a})
                current_q = line.split(":", 1)[1].strip()
                current_a = None
            elif line.startswith("A:") or line.startswith("О:"):
                current_a = line.split(":", 1)[1].strip()
            elif current_a is not None:
                current_a += " " + line

    if current_q and current_a:
        items.append({"question": current_q, "answer": current_a})

    return items


def calculate_match_score(user_query: str, faq_idx: int, faq_item: dict) -> float:
    """Вычисление релевантности вопроса пользователя записи из FAQ."""
    user_tokens = tokenize(user_query)
    if not user_tokens:
        return 0.0

    user_stems = {stem_word(w) for w in user_tokens}
    q_tokens = tokenize(faq_item["question"])
    q_stems = {stem_word(w) for w in q_tokens}

    score = 0.0

    # 1. Прямое совпадение по корням слов с текстом вопроса в FAQ
    stem_overlap = user_stems & q_stems
    score += len(stem_overlap) * 2.0

    # 2. Совпадение с тематическими ключевыми словами для данного вопроса
    keywords = TOPIC_KEYWORDS.get(faq_idx, set())
    for kw in keywords:
        for u_stem in user_stems:
            if u_stem == kw:
                score += 3.0
            elif len(kw) >= 4 and len(u_stem) >= 4:
                if u_stem.startswith(kw) or kw.startswith(u_stem):
                    score += 3.0

    return score


def find_answer(query: str, faq_items: list[dict], threshold: float = 2.0) -> str:
    """Поиск ответа по заданному запросу. Если совпадений нет — возвращает 'не знаю'."""
    if not query.strip():
        return "Пожалуйста, введите вопрос."

    best_score = 0.0
    best_item = None

    for idx, item in enumerate(faq_items):
        score = calculate_match_score(query, idx, item)
        if score > best_score:
            best_score = score
            best_item = item

    if best_score >= threshold and best_item is not None:
        return best_item["answer"]

    return "К сожалению, я не знаю ответа на этот вопрос. Попробуйте спросить о времени, команде, треке, сдаче или призах."


def main():
    try:
        faq_items = load_faq(FAQ_FILE)
    except Exception as e:
        print(f"Ошибка при загрузке FAQ: {e}", file=sys.stderr)
        sys.exit(1)

    # Режим одиночного вопроса через аргументы командной строки
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Вопрос: {query}")
        print(f"Ответ: {find_answer(query, faq_items)}")
        return

    # Интерактивный диалог в терминале
    print("=" * 60)
    print("🤖 Привет! Я FAQ-бот репетиции хакатона.")
    print("Я могу ответить на вопросы по 5 темам:")
    print("  1. Время и расписание")
    print("  2. Состав команды")
    print("  3. Трек и направление")
    print("  4. Сдача проекта")
    print("  5. Призы и награды")
    print("Для завершения напишите 'выход' или 'exit'.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nВы: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "выход", "q"}:
                print("Бот: До встречи и удачи на репетиции! 👋")
                break

            answer = find_answer(user_input, faq_items)
            print(f"Бот: {answer}")
        except (KeyboardInterrupt, EOFError):
            print("\nБот: До встречи! 👋")
            break


if __name__ == "__main__":
    main()
