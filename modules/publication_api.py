def download_image_from_url(self, image_url: str) -> Optional[str]:
    """
    Скачивает изображение по URL и сохраняет временно.
    
    Args:
        image_url: URL изображения
        
    Returns:
        Путь к скачанному файлу или None
    """
    if not image_url:
        return None
    
    import tempfile
    import requests
    from urllib.parse import urlparse
    
    logger.info(f"📥 Скачивание изображения: {image_url[:50]}...")
    
    try:
        # Создаем временную директорию
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        # Генерируем имя файла
        ext = os.path.splitext(urlparse(image_url).path)[1]
        if not ext:
            ext = '.jpg'
        
        filename = f"image_{int(time.time())}_{random.randint(1000, 9999)}{ext}"
        file_path = temp_dir / filename
        
        # Скачиваем изображение
        response = self.session.get(
            image_url,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Изображение скачано: {file_path}")
            return str(file_path)
        else:
            logger.error(f"❌ Ошибка скачивания: {response.status_code}")
            
    except Exception as e:
        logger.exception(f"❌ Ошибка при скачивании: {e}")
    
    return None
