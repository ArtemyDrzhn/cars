@staticmethod
def get_root_tasks_from_object(content_type, object_id):
    """
    Находит корневые Task'и, поднимаясь вверх по дереву от заданного объекта.
    Возвращает задачи, с которых началась цепочка (у которых нет родителей).
    """
    def make_task_cte(cte):
        # Аннотируем задачи с parent_id (ищем родительскую задачу)
        tasks = Task.objects.annotate(
            parent_id=Subquery(
                TaskRelation.objects.filter(
                    task_id=OuterRef("id"),
                    content_type=ContentType.objects.get_for_model(Task)
                ).values("object_id")[:1]
            )
        )

        # Начальные задачи - те, которые связаны с нашим объектом
        initial_tasks = tasks.filter(
            id__in=TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values_list("task_id", flat=True)
        ).values(
            "id",
            "parent_id",
            depth=Value(0, output_field=IntegerField()),
        )

        # Рекурсивная часть - ищем родительские задачи
        recursive_tasks = cte.join(
            tasks, 
            id=cte.col.parent_id  # Связываем по parent_id из CTE с id задачи
        ).values(
            "id",
            "parent_id", 
            depth=cte.col.depth + Value(1, output_field=IntegerField()),
        )

        return initial_tasks.union(recursive_tasks, all=True)

    cte = With.recursive(make_task_cte)
    content_type_task = ContentType.objects.get_for_model(Task)
    
    # Получаем все задачи из CTE и фильтруем только корневые (без родителей)
    root_tasks = cte.join(
        Task,
        id=cte.col.id,
        _join_type=INNER,
    ).with_cte(cte).annotate(
        parent_id=cte.col.parent_id,
        depth=cte.col.depth,
        content_type=Value(f"{content_type_task.app_label}.{content_type_task.model}")
    ).filter(
        parent_id__isnull=True  # Только корневые задачи (без родителей)
    )
    
    return root_tasks.select_related(
        "filial",
        "filial__region", 
        "type"
    )