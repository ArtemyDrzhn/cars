@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    from django_cte import With
    from django.db.models import F, Value, IntegerField
    from django.contrib.contenttypes.models import ContentType
    
    task_ct = ContentType.objects.get_for_model(Task)

    def make_tasks_cte(cte):
        # Базовый запрос - задачи, связанные напрямую с начальным объектом
        base_query = TaskRelation.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).values(
            task_id=F("task_id"),
            parent_task_id=Value(None, output_field=IntegerField()),
            depth=Value(0, output_field=IntegerField())
        )

        # Рекурсивный запрос - находим задачи, которые связаны с задачами из CTE
        recursive_query = TaskRelation.objects.filter(
            content_type=task_ct,
            object_id__in=cte.col.task_id  # Здесь используем task_id из CTE
        ).values(
            task_id=F("task_id"),
            parent_task_id=F("object_id"),  # object_id здесь - это ID родительской задачи
            depth=cte.col.depth + Value(1, output_field=IntegerField())
        )

        return base_query.union(recursive_query, all=True)

    # Создаем рекурсивный CTE
    tasks_cte = With.recursive(make_tasks_cte)

    # Финальный запрос - получаем полную информацию о задачах
    final_qs = (
        Task.objects
        .with_cte(tasks_cte)
        .annotate(
            depth=tasks_cte.col.depth,
            parent_task_id=tasks_cte.col.parent_task_id
        )
        .filter(id__in=tasks_cte.col.task_id)
        .order_by("depth", "id")
    )

    return final_qs