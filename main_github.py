# Было:
working_proxy = proxy_manager.find_working_proxy(
    max_attempts=50,
    target_url="https://9111.ru"
)

# Должно быть:
working_proxy = proxy_manager.find_working_proxy(
    max_attempts=100,  # Увеличиваем количество попыток
    target_url="https://9111.ru"
)
