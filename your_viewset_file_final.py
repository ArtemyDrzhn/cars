@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    from django_cte import With
    from django.db.models import F, Value, IntegerField
    from django.contrib.contenttypes.models import ContentType
    
    task_ct = ContentType.objects.get_for_model(Task)

    def make_tasks_cte(cte):
        # Базовый запрос: находим все задачи, связанные с начальным объектом
        base_query = (
            TaskRelation.objects
            .filter(
                content_type=content_type,
                object_id=object_id
            )
            .annotate(
                task_pk=F('task_id'),
                level=Value(0, output_field=IntegerField()),
                path=F('task_id')  # Путь для отслеживания иерархии
            )
            .values('task_pk', 'level', 'path')
        )

        # Рекурсивная часть: находим задачи, связанные с задачами из предыдущего уровня
        recursive_query = (
            TaskRelation.objects
            .filter(
                content_type=task_ct,
                object_id__in=cte.col.task_pk
            )
            .annotate(
                task_pk=F('task_id'),
                level=cte.col.level + 1,
                path=cte.col.path  # Сохраняем путь от корня
            )
            .values('task_pk', 'level', 'path')
        )

        return base_query.union(recursive_query, all=True)

    # Создаем рекурсивный CTE
    tasks_cte = With.recursive(make_tasks_cte)

    # Получаем итоговый queryset
    return (
        Task.objects
        .with_cte(tasks_cte)
        .annotate(
            depth=tasks_cte.col.level,
            root_path=tasks_cte.col.path
        )
        .filter(id__in=tasks_cte.col.task_pk)
        .distinct()
        .order_by('depth', 'id')
    )