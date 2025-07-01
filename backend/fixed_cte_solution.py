from rest_framework import viewsets, mixins
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value, IntegerField, F
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
        from apps.tasks.models import Task, TaskRelation  # Замените на правильный путь
        
        task_ct = ContentType.objects.get_for_model(Task)

        # ИСПРАВЛЕННАЯ ВЕРСИЯ: Убираем проблематичную ссылку на cte.col.depth
        tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values(
                "task_id",
                parent_task_id=Value(None, output_field=IntegerField()),
                depth=Value(0, output_field=IntegerField())
            ).union(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=cte.col.task_id
                ).extra(
                    select={
                        'depth': '(SELECT MIN(depth) FROM recursive_tasks WHERE task_id = tasks_taskrelation.object_id) + 1'
                    }
                ).values(
                    "task_id",
                    parent_task_id=F("object_id"),
                    depth=F("depth")  # Будет взята из extra select
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


# АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: Упрощенная версия без отслеживания глубины в CTE
class TreeTaskViewSetSimplified(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        from apps.tasks.models import Task, TaskRelation  # Замените на правильный путь
        
        task_ct = ContentType.objects.get_for_model(Task)

        # УПРОЩЕННАЯ ВЕРСИЯ: без depth в рекурсивной части
        tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values(
                "task_id",
                parent_task_id=Value(None, output_field=IntegerField())
            ).union(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=cte.col.task_id
                ).values(
                    "task_id",
                    parent_task_id=F("object_id")
                ),
                all=True
            ),
            name="recursive_tasks"
        )

        # Финальный запрос - глубину вычисляем отдельно, если нужно
        final_qs = (
            Task.objects
            .with_cte(tasks_cte)
            .annotate(
                parent_task_id=tasks_cte.col.parent_task_id
            )
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )

        return final_qs


# САМОЕ ПРОСТОЕ РЕШЕНИЕ: Минимальный CTE
class TreeTaskViewSetMinimal(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        from apps.tasks.models import Task, TaskRelation  # Замените на правильный путь
        
        task_ct = ContentType.objects.get_for_model(Task)

        # МИНИМАЛЬНАЯ ВЕРСИЯ: только task_id
        tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id").union(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=cte.col.task_id
                ).values("task_id"),
                all=True
            ),
            name="recursive_tasks"
        )

        # Финальный запрос
        final_qs = (
            Task.objects
            .with_cte(tasks_cte)
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )

        return final_qs