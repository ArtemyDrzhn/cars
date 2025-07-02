from django.db.models import (
    Value, IntegerField, BooleanField, Subquery, OuterRef, Case, When
)
from django.contrib.contenttypes.models import ContentType
from django_cte import With
from django.db.models.constants import INNER

# Предполагаемые импорты моделей (нужно адаптировать под ваш проект)
from .models import Task, TaskRelation

class TaskUtils:
    @staticmethod
    def get_root_tasks_from_object(content_type, object_id):
        """
        Находит корневую Task, поднимаясь вверх по дереву от заданного объекта.
        Возвращает одну задачу, с которой началась цепочка (у которой нет родителя).
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
        ).first()  # Возвращаем только первую корневую задачу

    @staticmethod
    def get_tree_path_to_object(content_type, object_id):
        """
        Находит полный путь в дереве задач от корня до заданного объекта.
        1. Находит корневую Task от объекта (используя функцию get_root_tasks_from_object)
        2. От корня идет вниз и строит путь до исходного объекта (включительно)
        3. Не идет дальше исходного объекта вниз по дереву
        """
        # Сначала получаем корневую задачу
        root_task = TaskUtils.get_root_tasks_from_object(content_type, object_id)
        if not root_task:
            # Если корневая задача не найдена, возвращаем пустой QuerySet
            return Task.objects.none()
        
        root_task_ids = [root_task.id]
        
        # ID задач, связанных с нашим объектом (конечная точка)
        target_task_ids = list(TaskRelation.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).values_list("task_id", flat=True))

        def make_path_cte(cte):
            tasks = Task.objects.annotate(
                parent_id=Subquery(
                    TaskRelation.objects.filter(
                        task_id=OuterRef("id"),
                        content_type=ContentType.objects.get_for_model(Task)
                    ).values("object_id")[:1]
                )
            )

            # Начальные задачи - корневые задачи
            initial_tasks = tasks.filter(
                id__in=root_task_ids
            ).values(
                "id",
                "parent_id",
                depth=Value(0, output_field=IntegerField()),
                is_target=Case(
                    When(id__in=target_task_ids, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )

            # Рекурсивная часть - идем вниз от корней
            recursive_tasks = cte.join(
                tasks,
                parent_id=cte.col.id  # Как в исходной функции - идем вниз
            ).filter(
                # Не идем дальше target задач
                cte.col.is_target=False
            ).values(
                "id",
                "parent_id",
                depth=cte.col.depth + Value(1, output_field=IntegerField()),
                is_target=Case(
                    When(id__in=target_task_ids, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )

            return initial_tasks.union(recursive_tasks, all=True)

        cte = With.recursive(make_path_cte)
        content_type_task = ContentType.objects.get_for_model(Task)
        
        # Получаем все задачи пути
        path_tasks = cte.join(
            Task,
            id=cte.col.id,
            _join_type=INNER,
        ).with_cte(cte).annotate(
            parent_id=cte.col.parent_id,
            depth=cte.col.depth,
            is_target=cte.col.is_target,
            content_type=Value(f"{content_type_task.app_label}.{content_type_task.model}")
        )
        
        return path_tasks.select_related(
            "filial",
            "filial__region",
            "type"
        ).order_by("depth", "id")