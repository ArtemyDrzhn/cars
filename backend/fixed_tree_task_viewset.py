from rest_framework import viewsets, mixins
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value, IntegerField, F, Subquery, OuterRef
from django_cte import With
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class TreeTaskViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    def get_queryset(self):
        app_label, model = (
            self.request.query_params.get("content_type")
        ).split(".")
        object_id = int(self.request.query_params.get("object_id"))
        content_type = ContentType.objects.get_by_natural_key(app_label=app_label, model=model)
        return self.get_related_tasks_from_object(content_type, object_id)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "object_id",
                openapi.IN_QUERY,
                description="ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "content_type",
                openapi.IN_QUERY,
                description="Тип контента",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @staticmethod
    def get_related_tasks_from_object(content_type, object_id):
        # Импорт моделей (замените на правильный путь к вашим моделям)
        from your_app.models import Task, TaskRelation
        
        task_ct = ContentType.objects.get_for_model(Task)

        # Создаем CTE, используя правильный подход для django-cte
        tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values(
                task_id=F("task_id"),
                parent_task_id=Value(None, output_field=IntegerField()),
                depth=Value(0, output_field=IntegerField())
            ).union(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=cte.col.task_id  # Это должно работать в новых версиях django-cte
                ).values(
                    task_id=F("task_id"),
                    parent_task_id=F("object_id"),
                    depth=cte.col.depth + 1
                ),
                all=True
            ),
            name="recursive_tasks"
        )

        # Финальный запрос
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


# АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ без рекурсивных CTE (более простое и надежное)
class TreeTaskViewSetAlternative(viewsets.GenericViewSet, mixins.ListModelMixin):
    def get_queryset(self):
        app_label, model = (
            self.request.query_params.get("content_type")
        ).split(".")
        object_id = int(self.request.query_params.get("object_id"))
        content_type = ContentType.objects.get_by_natural_key(app_label=app_label, model=model)
        return self.get_related_tasks_from_object(content_type, object_id)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "object_id",
                openapi.IN_QUERY,
                description="ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "content_type",
                openapi.IN_QUERY,
                description="Тип контента",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @staticmethod
    def get_related_tasks_from_object(content_type, object_id):
        from your_app.models import Task, TaskRelation
        
        task_ct = ContentType.objects.get_for_model(Task)
        
        # Собираем все связанные задачи рекурсивно
        all_task_ids = set()
        
        def collect_tasks(ct, obj_id, depth=0, max_depth=10):
            if depth > max_depth:  # Защита от бесконечной рекурсии
                return
                
            # Находим задачи, связанные с текущим объектом
            task_relations = TaskRelation.objects.filter(
                content_type=ct,
                object_id=obj_id
            ).values_list('task_id', flat=True)
            
            for task_id in task_relations:
                if task_id not in all_task_ids:
                    all_task_ids.add(task_id)
                    # Рекурсивно ищем задачи, связанные с найденной задачей
                    collect_tasks(task_ct, task_id, depth + 1, max_depth)
        
        # Начинаем сбор с исходного объекта
        collect_tasks(content_type, object_id)
        
        # Возвращаем QuerySet с найденными задачами
        return Task.objects.filter(id__in=all_task_ids).order_by('id')