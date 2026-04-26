from services.booking_service import current_lunches, today_statistics


def format_current_lunches() -> str:
    lunches = current_lunches()
    if not lunches:
        return 'Зараз на обіді нікого немає.'
    lines = ['Зараз на обіді:']
    for item in lunches:
        lines.append(f'• {item.get("full_name", "Без імені")} — до {item.get("end_time")}')
    return '\n'.join(lines)


def format_today_stats() -> str:
    stats = today_statistics()
    return f'Статистика за сьогодні:\nУсього обідів: {stats["total"]}\nЗараз на обіді: {stats["current"]}'
