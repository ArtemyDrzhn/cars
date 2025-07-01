@staticmethod
def get_related_tasks_from_object(content_type, object_id):
    from django_cte import With
    from django.db.models import F, Value, IntegerField, OuterRef, Subquery
    from django.contrib.contenttypes.models import ContentType
    
    task_ct = ContentType.objects.get_for_model(Task)

    # Подзапрос для получения ID задач по TaskRelation
    def get_task_ids_subquery(ct, obj_id):
        return TaskRelation.objects.filter(
            content_type=ct,
            object_id=obj_id
        ).values_list('task_id', flat=True)

    def make_tasks_cte(cte):
        # Базовый запрос - задачи первого уровня
        base_tasks = Task.objects.filter(
            id__in=get_task_ids_subquery(content_type, object_id)
        ).annotate(
            level=Value(0, output_field=IntegerField()),
            parent_id=Value(None, output_field=IntegerField())
        ).values('id', 'level', 'parent_id')

        # Рекурсивный запрос - дочерние задачи
        child_task_ids = get_task_ids_subquery(task_ct, OuterRef('id'))
        
        recursive_tasks = Task.objects.filter(
            id__in=Subquery(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=cte.col.id
                ).values_list('task_id', flat=True)
            )
        ).annotate(
            level=cte.col.level + Value(1, output_field=IntegerField()),
            parent_id=F('task_relations__object_id')
        ).values('id', 'level', 'parent_id')

        return base_tasks.union(recursive_tasks, all=True)

    # Создаем CTE
    tasks_cte = With.recursive(make_tasks_cte)

    # Получаем финальный queryset с полной информацией о задачах
    return (
        Task.objects
        .with_cte(tasks_cte)
        .annotate(
            tree_level=tasks_cte.col.level,
            tree_parent_id=tasks_cte.col.parent_id
        )
        .filter(id__in=tasks_cte.col.id)
        .order_by('tree_level', 'id')
    )