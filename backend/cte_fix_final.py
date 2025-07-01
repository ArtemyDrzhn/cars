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

        def make_tasks_cte(cte):
            # Базовый запрос
            base_query = TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id")

            # Рекурсивный запрос с использованием extra()
            recursive_query = TaskRelation.objects.filter(
                content_type=task_ct
            ).extra(
                where=['"tasks_taskrelation"."object_id" IN (SELECT "task_id" FROM "recursive_tasks")']
            ).values("task_id")

            return base_query.union(recursive_query, all=True)

        # Создаем CTE
        tasks_cte = With.recursive(make_tasks_cte, name="recursive_tasks")

        # Финальный запрос
        final_qs = (
            Task.objects
            .with_cte(tasks_cte)
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )

        return final_qs


# АЛЬТЕРНАТИВНАЯ ВЕРСИЯ - если проблема с именами таблиц
class TreeTaskViewSetAlt(viewsets.GenericViewSet, mixins.ListModelMixin):
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

        def make_tasks_cte(cte):
            # Базовый запрос
            base_query = TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id")

            # Рекурсивный запрос - пробуем разные варианты ссылки на CTE
            recursive_query = TaskRelation.objects.filter(
                content_type=task_ct
            ).extra(
                where=['object_id IN (SELECT task_id FROM recursive_tasks)']
            ).values("task_id")

            return base_query.union(recursive_query, all=True)

        # Создаем CTE
        tasks_cte = With.recursive(make_tasks_cte, name="recursive_tasks")

        # Финальный запрос
        final_qs = (
            Task.objects
            .with_cte(tasks_cte)
            .filter(id__in=tasks_cte.col.task_id)
            .order_by("id")
        )

        return final_qs


# САМАЯ ПРОСТАЯ ВЕРСИЯ - попробуем совсем без lambda
class TreeTaskViewSetSimplest(viewsets.GenericViewSet, mixins.ListModelMixin):
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

        # Попробуем создать CTE без lambda
        base_qs = TaskRelation.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).values("task_id")

        tasks_cte = With(base_qs, name="base_tasks")

        # Получаем связанные задачи в несколько шагов
        related_tasks = TaskRelation.objects.filter(
            content_type=task_ct
        ).with_cte(tasks_cte).filter(
            object_id__in=tasks_cte.col.task_id
        ).values_list("task_id", flat=True)

        # Объединяем результаты
        all_task_ids = list(base_qs.values_list("task_id", flat=True)) + list(related_tasks)
        
        # Убираем дубликаты
        unique_task_ids = list(set(all_task_ids))

        return Task.objects.filter(id__in=unique_task_ids).order_by("id")