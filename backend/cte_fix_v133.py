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
        task_ct = ContentType.objects.get_for_model(Task)

        # ВАРИАНТ 1: Пробуем обращение через Col
        from django_cte import Col
        
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
                    object_id__in=Col("task_id")  # Попробуем Col вместо cte.col
                ).values(
                    "task_id",
                    parent_task_id=F("object_id"),
                    depth=Value(1, output_field=IntegerField())  # Фиксированная глубина
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


# ВАРИАНТ 2: Используем правильный синтаксис для 1.3.3
class TreeTaskViewSetV2(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        task_ct = ContentType.objects.get_for_model(Task)

        # Попробуем использовать правильный синтаксис для рекурсивной части
        def recursive_cte(cte):
            # Базовая часть
            base = TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values(
                "task_id",
                parent_task_id=Value(None, output_field=IntegerField()),
                depth=Value(0, output_field=IntegerField())
            )

            # Рекурсивная часть - используем EXISTS
            recursive = TaskRelation.objects.filter(
                content_type=task_ct
            ).extra(
                where=["EXISTS (SELECT 1 FROM recursive_tasks WHERE recursive_tasks.task_id = tasks_taskrelation.object_id)"]
            ).values(
                "task_id",
                parent_task_id=F("object_id"),
                depth=Value(1, output_field=IntegerField())
            )

            return base.union(recursive, all=True)

        tasks_cte = With.recursive(recursive_cte, name="recursive_tasks")

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


# ВАРИАНТ 3: Максимально простой для django-cte 1.3.3
class TreeTaskViewSetV3(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        task_ct = ContentType.objects.get_for_model(Task)

        # Самый простой рекурсивный CTE
        tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id").union(
                TaskRelation.objects.filter(
                    content_type=task_ct
                ).extra(
                    where=["object_id = ANY(SELECT task_id FROM recursive_tasks)"]
                ).values("task_id"),
                all=True
            ),
            name="recursive_tasks"
        )

        final_qs = (
            Task.objects
            .with_cte(tasks_cte)
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )

        return final_qs


# ВАРИАНТ 4: Через raw SQL в extra - должно точно работать
class TreeTaskViewSetV4(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        task_ct = ContentType.objects.get_for_model(Task)

        def make_cte(cte):
            base_qs = TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id")

            recursive_qs = TaskRelation.objects.filter(
                content_type=task_ct
            ).extra(
                where=["tasks_taskrelation.object_id IN (SELECT task_id FROM recursive_tasks)"]
            ).values("task_id")

            return base_qs.union(recursive_qs, all=True)

        tasks_cte = With.recursive(make_cte, name="recursive_tasks")

        return (
            Task.objects
            .with_cte(tasks_cte)
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )