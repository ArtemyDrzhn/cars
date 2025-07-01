# Исправление ошибки "missing FROM-clause entry for table 'cte'"

## Проблема

Ошибка `django.db.utils.ProgrammingError: missing FROM-clause entry for table "cte"` возникает в рекурсивном CTE (Common Table Expression) в методе `get_related_tasks_from_object`. 

### Основные проблемы в исходном коде:

1. **Неправильная ссылка на CTE**: 
   ```python
   object_id__in=cte.col.task_id  # НЕПРАВИЛЬНО
   ```
   Django ORM не может правильно разрешить эту ссылку на столбец CTE внутри рекурсивной части.

2. **Неправильная ссылка на depth**: 
   ```python
   depth=cte.col.depth + Value(1, output_field=IntegerField())  # НЕПРАВИЛЬНО
   ```

## Решение 1: Исправленный CTE (рекомендуемое)

Замените проблемные строки в методе `make_tasks_cte`:

```python
def make_tasks_cte(cte):
    # Базовый запрос остается без изменений
    base_query = TaskRelation.objects.filter(
        content_type=content_type,
        object_id=object_id
    ).values(
        "task_id",
        parent_task_id=Value(None, output_field=IntegerField()),
        depth=Value(0, output_field=IntegerField())
    )

    # ИСПРАВЛЕНИЕ: используем Subquery
    recursive_query = TaskRelation.objects.filter(
        content_type=task_ct,
        object_id__in=Subquery(cte.queryset().values('task_id'))  # ✅ ПРАВИЛЬНО
    ).values(
        "task_id",
        parent_task_id=F("object_id"),
        depth=F("depth") + Value(1, output_field=IntegerField())  # ✅ ИСПРАВЛЕНО
    )

    return base_query.union(recursive_query, all=True)
```

### Ключевые изменения:
- `cte.col.task_id` → `Subquery(cte.queryset().values('task_id'))`
- `cte.col.depth + Value(1, ...)` → `F("depth") + Value(1, ...)`

## Решение 2: Альтернативный подход без CTE

Если проблемы с CTE продолжаются, используйте рекурсивный Python-подход:

```python
@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    from your_app.models import Task, TaskRelation
    
    task_ct = ContentType.objects.get_for_model(Task)
    all_task_ids = set()
    
    def collect_tasks(ct, obj_id, depth=0, max_depth=10):
        if depth > max_depth:  # Защита от бесконечной рекурсии
            return
            
        task_relations = TaskRelation.objects.filter(
            content_type=ct,
            object_id=obj_id
        ).values_list('task_id', flat=True)
        
        for task_id in task_relations:
            if task_id not in all_task_ids:
                all_task_ids.add(task_id)
                collect_tasks(task_ct, task_id, depth + 1, max_depth)
    
    collect_tasks(content_type, object_id)
    return Task.objects.filter(id__in=all_task_ids).order_by('id')
```

## Сравнение решений

### Решение 1 (исправленный CTE):
- ✅ Выполняется в одном SQL-запросе
- ✅ Лучшая производительность для больших данных
- ✅ Сохраняет информацию о глубине и родительских связях
- ❌ Более сложная отладка

### Решение 2 (Python рекурсия):
- ✅ Простота понимания и отладки
- ✅ Защита от бесконечной рекурсии
- ✅ Более предсказуемое поведение
- ❌ Множественные запросы к БД
- ❌ Может быть медленнее для глубоких иерархий

## Инструкции по применению

1. **Найдите ваш файл с TreeTaskViewSet** (обычно в `apps/tasks/v2/views.py`)

2. **Замените метод `get_related_tasks_from_object`** на исправленную версию из Решения 1

3. **Если продолжают возникать ошибки**, используйте Решение 2

4. **Не забудьте обновить импорты**:
   ```python
   from django.db.models import Value, IntegerField, F, Subquery
   ```

## Дополнительные улучшения

### 1. Добавьте валидацию параметров:
```python
def get_queryset(self):
    content_type_param = self.request.query_params.get("content_type")
    object_id_param = self.request.query_params.get("object_id")
    
    if not content_type_param or not object_id_param:
        from rest_framework.exceptions import ValidationError
        raise ValidationError("content_type and object_id are required")
    
    try:
        app_label, model = content_type_param.split(".")
        object_id = int(object_id_param)
    except (ValueError, AttributeError):
        raise ValidationError("Invalid content_type format or object_id")
    
    content_type = ContentType.objects.get_by_natural_key(
        app_label=app_label, model=model
    )
    return self.get_related_tasks_from_object(content_type, object_id)
```

### 2. Добавьте логирование для отладки:
```python
import logging
logger = logging.getLogger(__name__)

@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    logger.info(f"Getting tasks for {content_type} with id {object_id}")
    # ваш код...
```

### 3. Рассмотрите кэширование:
```python
from django.core.cache import cache

@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    cache_key = f"related_tasks_{content_type.id}_{object_id}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # выполняем запрос...
    result = final_qs
    cache.set(cache_key, result, timeout=300)  # кэш на 5 минут
    return result
```