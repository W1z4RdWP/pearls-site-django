#!/usr/bin/env python
"""
Скрипт для проверки и исправления app_label в моделях Django.
Запускать после создания новых приложений или моделей.
"""

import os
import re
from pathlib import Path

def check_and_fix_app_labels():
    """Проверяет и исправляет app_label в моделях Django"""
    
    # Путь к папке apps
    apps_dir = Path(__file__).parent / 'apps'
    
    if not apps_dir.exists():
        print("Папка apps не найдена")
        return
    
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir() or app_dir.name.startswith('.'):
            continue
            
        app_name = app_dir.name
        models_file = app_dir / 'models.py'
        
        if not models_file.exists():
            continue
            
        print(f"Проверяем приложение: {app_name}")
        
        # Читаем файл models.py
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем все классы моделей
        model_pattern = r'class\s+(\w+)\(models\.Model\):'
        models = re.findall(model_pattern, content)
        
        for model_name in models:
            # Проверяем, есть ли app_label в Meta классе
            meta_pattern = rf'class\s+{model_name}\(models\.Model\):(.*?)class\s+Meta:(.*?)app_label\s*=\s*[\'"]{app_name}[\'"]'
            
            if not re.search(meta_pattern, content, re.DOTALL):
                # Ищем Meta класс без app_label
                meta_without_label_pattern = rf'class\s+{model_name}\(models\.Model\):(.*?)class\s+Meta:(.*?)(?=\n\s*\n|\n\s*class|\Z)'
                match = re.search(meta_without_label_pattern, content, re.DOTALL)
                
                if match:
                    meta_content = match.group(2)
                    # Добавляем app_label в начало Meta класса
                    new_meta_content = f'        app_label = \'{app_name}\'\n{meta_content}'
                    content = content.replace(match.group(2), new_meta_content)
                    print(f"  Добавлен app_label для модели {model_name}")
        
        # Записываем обновленный файл
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("Проверка завершена!")

def check_apps_config():
    """Проверяет и исправляет конфигурацию приложений"""
    
    apps_dir = Path(__file__).parent / 'apps'
    
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir() or app_dir.name.startswith('.'):
            continue
            
        app_name = app_dir.name
        apps_file = app_dir / 'apps.py'
        
        if not apps_file.exists():
            continue
            
        print(f"Проверяем конфигурацию: {app_name}")
        
        with open(apps_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли app_label
        if f'app_label = \'{app_name}\'' not in content:
            # Добавляем app_label после name
            name_pattern = rf'name\s*=\s*[\'"]{app_name}[\'"]'
            if re.search(name_pattern, content):
                content = re.sub(name_pattern, f'name = \'{app_name}\'\n    app_label = \'{app_name}\'', content)
                print(f"  Добавлен app_label в конфигурацию {app_name}")
        
        # Записываем обновленный файл
        with open(apps_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("Проверка конфигураций завершена!")

if __name__ == '__main__':
    print("Проверка app_label в моделях Django...")
    check_and_fix_app_labels()
    print("\nПроверка конфигураций приложений...")
    check_apps_config()
    print("\nВсе проверки завершены!") 