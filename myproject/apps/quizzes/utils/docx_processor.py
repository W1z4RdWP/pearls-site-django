"""
Утилита для парсинга DOCX файлов с тестами.

Формат DOCX:
- Курсивный текст = вопрос в формате "Вопрос 1. Текст вопроса"
  (строго: слово "Вопрос" + пробел + номер + точка + пробел + текст вопроса)
- Обычный текст = варианты ответов
- Жирный текст или маркер = правильный ответ
"""
import docx
from typing import Dict, List, Any, Optional
import re


class DocxQuizProcessor:
    """Класс для обработки DOCX файлов с тестами"""
    
    def __init__(self):
        pass
    
    def parse_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Парсит DOCX файл и возвращает структурированные данные теста.
        
        Args:
            file_path: Путь к DOCX файлу
            
        Returns:
            Словарь с ключами:
            - questions: список вопросов
        """
        doc = docx.Document(file_path)
        
        questions = []
        current_question = None
        current_answers = []
        
        for paragraph in doc.paragraphs:
            # Проверяем, является ли параграф курсивным (вопрос)
            is_italic = self._is_italic(paragraph)
            
            # Курсивный текст = номер и текст вопроса в формате "Вопрос 1. Текст вопроса"
            if is_italic:
                # Сохраняем предыдущий вопрос если есть
                if current_question:
                    if current_answers:
                        current_question['answers'] = current_answers
                        questions.append(current_question)
                    current_answers = []
                
                # Парсим номер и текст вопроса (формат: "Вопрос 1. Текст вопроса")
                question_text = paragraph.text.strip()
                question_data = self._parse_question_text(question_text)
                
                # Пропускаем вопросы с некорректным форматом (order = 0)
                if question_data['order'] == 0:
                    continue
                
                current_question = {
                    'order': question_data['order'],
                    'text': question_data['text'],
                    'type': 'single'  # По умолчанию один правильный ответ
                }
            
            # Обычный текст = варианты ответов
            elif paragraph.text.strip() and current_question:
                answer_text = paragraph.text.strip()
                
                # ВАЖНО: Проверяем, не является ли этот текст новым вопросом
                # (на случай, если вопрос не распознан как курсивный)
                if self._looks_like_question_text(answer_text):
                    # Сохраняем предыдущий вопрос если есть
                    if current_question:
                        if current_answers:
                            current_question['answers'] = current_answers
                            questions.append(current_question)
                        current_answers = []
                    
                    # Парсим номер и текст вопроса
                    question_data = self._parse_question_text(answer_text)
                    
                    # Пропускаем вопросы с некорректным форматом (order = 0)
                    if question_data['order'] == 0:
                        continue
                    
                    current_question = {
                        'order': question_data['order'],
                        'text': question_data['text'],
                        'type': 'single'
                    }
                    continue  # Переходим к следующему параграфу
                
                # Если это не вопрос, обрабатываем как вариант ответа
                # Проверяем, является ли ответ правильным
                is_correct = self._is_correct_answer(paragraph)
                
                # Определяем тип вопроса на основе правильных ответов
                if is_correct and current_question['type'] == 'single':
                    # Если уже есть правильный ответ, значит это multiple
                    if any(ans.get('is_correct', False) for ans in current_answers):
                        current_question['type'] = 'multiple'
                
                current_answers.append({
                    'text': answer_text,
                    'is_correct': is_correct
                })
        
        # Сохраняем последний вопрос
        if current_question:
            if current_answers:
                current_question['answers'] = current_answers
                questions.append(current_question)
        
        # Сортируем вопросы по порядку (по номеру из текста)
        questions.sort(key=lambda x: x.get('order', 999))
        
        return {
            'questions': questions
        }
    
    def _is_italic(self, paragraph) -> bool:
        """Проверяет, является ли параграф курсивным (вопрос)"""
        # Проверяем курсивность во всех runs параграфа
        runs = paragraph.runs
        if not runs:
            return False
        
        # Если хотя бы один run имеет курсивное начертание, считаем параграф курсивным
        for run in runs:
            if hasattr(run, 'font') and run.font:
                if run.font.italic:
                    return True
        
        return False
    
    def _parse_question_text(self, text: str) -> Dict[str, Any]:
        """
        Парсит текст вопроса в формате "Вопрос 1. Текст вопроса".
        
        Формат строго: "Вопрос" + пробел + номер + точка + пробел + текст вопроса
        Примеры:
        - "Вопрос 1. Какой вопрос?" -> order: 1, text: "Какой вопрос?"
        - "Вопрос 27. Текст вопроса" -> order: 27, text: "Текст вопроса"
        """
        # Строгий паттерн для формата "Вопрос 1. Текст вопроса"
        pattern = r'^Вопрос\s+(\d+)\.\s+(.+)$'
        
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            order = int(match.group(1))
            question_text = match.group(2).strip()
            return {'order': order, 'text': question_text}
        
        # Если формат не соответствует, возвращаем 0 (вопрос будет пропущен или обработан некорректно)
        return {'order': 0, 'text': text.strip()}
    
    def _looks_like_question_text(self, text: str) -> bool:
        """
        Проверяет, похож ли текст на вопрос в формате "Вопрос X. Текст вопроса".
        Используется для распознавания вопросов, которые не были распознаны как курсивные.
        """
        # Проверяем строгий формат "Вопрос X. Текст"
        pattern = r'^Вопрос\s+\d+\.\s+.+$'
        return bool(re.match(pattern, text, re.IGNORECASE))
    
    def _is_correct_answer(self, paragraph) -> bool:
        """
        Определяет, является ли ответ правильным.
        Проверяет:
        - Жирный текст (bold)
        - Маркеры (bullet points)
        - Специальные символы в начале (✓, +, *, и т.д.)
        """
        # Проверяем жирность текста
        for run in paragraph.runs:
            if hasattr(run, 'font') and run.font:
                if run.font.bold:
                    return True
        
        # Проверяем маркеры
        if paragraph.style and 'List' in paragraph.style.name:
            return True
        
        # Проверяем специальные символы в начале строки
        text = paragraph.text.strip()
        correct_markers = ['✓', '+', '*', '•', '→', '→', '✓', '☑']
        if text and text[0] in correct_markers:
            return True
        
        # Проверяем паттерны типа "(правильный)", "[правильно]" и т.д.
        correct_patterns = [
            r'^\s*\(правил[ьь]н[ыо]\)',
            r'^\s*\[правил[ьь]н[ыо]\]',
            r'^\s*правил[ьь]н[ыо]',
            r'^\s*✓',
            r'^\s*\+',
        ]
        
        for pattern in correct_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False

