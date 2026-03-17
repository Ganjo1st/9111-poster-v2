def find_working_proxy_aggressive(self, max_attempts: int = 100, target_url: str = "https://9111.ru") -> Optional[str]:
    """
    Агрессивный поиск рабочего прокси с множественными попытками.
    
    Args:
        max_attempts: Максимальное количество попыток
        target_url: Целевой URL для тестирования
        
    Returns:
        Рабочий прокси или None
    """
    logger.info("🔍 АГРЕССИВНЫЙ поиск рабочего российского прокси...")
    
    # Пробуем разные источники
    all_proxies = []
    
    # 1. Сначала наши проверенные
    all_proxies.extend(self.RUSSIAN_PROXIES)
    
    # 2. Пробуем загрузить свежие
    try:
        fresh_proxies = self.fetch_fresh_proxies(max_per_source=100)
        all_proxies.extend(fresh_proxies)
    except:
        pass
    
    # Убираем дубликаты
    all_proxies = list(set(all_proxies))
    random.shuffle(all_proxies)
    
    logger.info(f"📋 Всего прокси для проверки: {len(all_proxies)}")
    
    # Тестируем с разными таймаутами
    for timeout in [5, 10, 15]:
        logger.info(f"⏱️ Тестирование с таймаутом {timeout}с...")
        
        tested = 0
        working = []
        
        for proxy in all_proxies[:max_attempts]:
            tested += 1
            logger.info(f"🔄 Тест {tested}/{min(max_attempts, len(all_proxies))}: {proxy}")
            
            proxies_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            try:
                start = time.time()
                response = requests.get(
                    target_url,
                    proxies=proxies_dict,
                    timeout=timeout,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    allow_redirects=True
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    logger.info(f"  ✅ РАБОТАЕТ! Код: {response.status_code}, время: {elapsed:.2f}с")
                    working.append((proxy, elapsed))
                    
                    # Если нашли быстрый, сразу возвращаем
                    if elapsed < 3.0:
                        self.current_proxy = proxy
                        logger.info(f"🎯 Найден быстрый прокси: {proxy} ({elapsed:.2f}с)")
                        return proxy
                else:
                    logger.info(f"  ❌ Код ответа: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"  ❌ Ошибка: {type(e).__name__}")
        
        if working:
            # Сортируем по скорости
            working.sort(key=lambda x: x[1])
            best_proxy = working[0][0]
            best_speed = working[0][1]
            
            self.current_proxy = best_proxy
            logger.info(f"🎯 Выбран лучший прокси: {best_proxy} ({best_speed:.2f}с)")
            return best_proxy
    
    logger.error("❌ НЕ НАЙДЕНО РАБОЧИХ ПРОКСИ!")
    return None
