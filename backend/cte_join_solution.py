from rest_framework import viewsets, mixins
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value, IntegerField, F, Subquery, OuterRef
from django_cte import With
from django.db.models.constants import LOUTER
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

        # Создаем CTE с начальными задачами
        initial_tasks_cte = With(
            Task.objects.filter(
                id__in=Subquery(
                    TaskRelation.objects.filter(
                        content_type=content_type,
                        object_id=object_id
                    ).values("task_id")
                )
            ),
            name="initial_tasks"
        )

        # Создаем рекурсивный CTE для получения всех связанных задач
        recursive_tasks_cte = With.recursive(
            lambda cte: TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values("task_id").union(
                TaskRelation.objects.filter(
                    content_type=task_ct
                ).extra(
                    where=["tasks_taskrelation.object_id IN (SELECT task_id FROM recursive_tasks)"]
                ).values("task_id"),
                all=True
            ),
            name="recursive_tasks"
        )

        # Финальный запрос с джойном
        result = (
            Task.objects
            .with_cte(recursive_tasks_cte)
            .filter(id__in=recursive_tasks_cte.col.task_id)
            .annotate(
                parent_id=Subquery(
                    TaskRelation.objects.filter(
                        content_type=task_ct,
                        task_id=OuterRef("id"),
                    ).values("object_id")[:1]
                )
            )
            .order_by("id")
        )

        return result


# ВАРИАНТ 2: Более простой без рекурсивного CTE
class TreeTaskViewSetSimple(viewsets.GenericViewSet, mixins.ListModelMixin):
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

        # Создаем CTE с начальными задачами
        cte = With(
            Task.objects.filter(
                id__in=Subquery(
                    TaskRelation.objects.filter(
                        content_type=content_type,
                        object_id=object_id
                    ).values("task_id")
                )
            ),
            name="base_tasks"
        )

        # Получаем задачи второго уровня
        child_tasks = TaskRelation.objects.filter(
            content_type=task_ct,
            object_id__in=Subquery(cte.queryset().values("id"))
        ).values_list("task_id", flat=True)

        # Объединяем все ID задач
        all_task_ids = list(cte.queryset().values_list("id", flat=True)) + list(child_tasks)
        unique_task_ids = list(set(all_task_ids))

        # Возвращаем задачи с аннотированным parent_id
        result = Task.objects.filter(
            id__in=unique_task_ids
        ).annotate(
            parent_id=Subquery(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    task_id=OuterRef("id"),
                ).values("object_id")[:1]
            )
        ).order_by("id")

        return result


# ВАРИАНТ 3: Ваш исходный код с исправлениями
class TreeTaskViewSetFixed(viewsets.GenericViewSet, mixins.ListModelMixin):
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

        # Ваш код с небольшими исправлениями
        cte = With(
            Task.objects.filter(
                id__in=Subquery(
                    TaskRelation.objects.filter(
                        content_type=content_type,
                        object_id=object_id
                    ).values("task_id")
                )
            ),
            name="base_tasks"
        )

        # Получаем связанные задачи и джойним с CTE
        related_tasks = Task.objects.filter(
            id__in=Subquery(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    object_id__in=Subquery(cte.queryset().values("id"))
                ).values("task_id")
            )
        )

        # Объединяем базовые и связанные задачи
        all_tasks = cte.queryset().union(related_tasks)

        # Аннотируем parent_id
        result = all_tasks.annotate(
            parent_id=Subquery(
                TaskRelation.objects.filter(
                    content_type=task_ct,
                    task_id=OuterRef("id"),
                ).values("object_id")[:1]
            )
        ).order_by("id")

        return result