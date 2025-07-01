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
        # Импорт моделей (замените на правильный путь к вашим моделям)
        from your_app.models import Task, TaskRelation
        
        # РЕШЕНИЕ 1: Полностью через Raw SQL
        raw_sql = """
        WITH RECURSIVE task_tree AS (
            -- Базовый запрос: задачи, связанные напрямую с начальным объектом
            SELECT 
                tr.task_id,
                NULL::integer as parent_task_id,
                0 as depth
            FROM tasks_taskrelation tr
            WHERE tr.content_type_id = %s AND tr.object_id = %s
            
            UNION ALL
            
            -- Рекурсивный запрос: задачи, связанные с задачами из CTE
            SELECT 
                tr.task_id,
                tr.object_id as parent_task_id,
                tt.depth + 1 as depth
            FROM tasks_taskrelation tr
            INNER JOIN task_tree tt ON tr.object_id = tt.task_id
            WHERE tr.content_type_id = %s AND tt.depth < 10  -- Ограничение глубины
        )
        SELECT DISTINCT t.*, tt.depth, tt.parent_task_id
        FROM tasks_task t
        INNER JOIN task_tree tt ON t.id = tt.task_id
        ORDER BY tt.depth, t.id
        """
        
        task_ct = ContentType.objects.get_for_model(Task)
        
        return Task.objects.raw(
            raw_sql, 
            [content_type.id, object_id, task_ct.id]
        )


# РЕШЕНИЕ 2: Гибридный подход - CTE для простых случаев, Python для сложных
class TreeTaskViewSetHybrid(viewsets.GenericViewSet, mixins.ListModelMixin):
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
        from django.db import connection
        
        task_ct = ContentType.objects.get_for_model(Task)
        
        # Используем курсор для выполнения CTE
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE task_tree AS (
                    -- Базовый запрос
                    SELECT 
                        task_id,
                        NULL::integer as parent_task_id,
                        0 as depth
                    FROM tasks_taskrelation 
                    WHERE content_type_id = %s AND object_id = %s
                    
                    UNION ALL
                    
                    -- Рекурсивный запрос
                    SELECT 
                        tr.task_id,
                        tr.object_id as parent_task_id,
                        tt.depth + 1
                    FROM tasks_taskrelation tr
                    INNER JOIN task_tree tt ON tr.object_id = tt.task_id
                    WHERE tr.content_type_id = %s AND tt.depth < 10
                )
                SELECT task_id, parent_task_id, depth FROM task_tree
            """, [content_type.id, object_id, task_ct.id])
            
            task_data = cursor.fetchall()
        
        # Извлекаем ID задач
        task_ids = [row[0] for row in task_data]
        
        if not task_ids:
            return Task.objects.none()
        
        # Создаем словарь для аннотаций
        task_annotations = {
            row[0]: {'parent_task_id': row[1], 'depth': row[2]} 
            for row in task_data
        }
        
        # Получаем задачи и добавляем аннотации
        tasks = Task.objects.filter(id__in=task_ids).order_by('id')
        
        # Добавляем аннотации к каждой задаче
        for task in tasks:
            if task.id in task_annotations:
                task.depth = task_annotations[task.id]['depth']
                task.parent_task_id = task_annotations[task.id]['parent_task_id']
        
        return tasks


# РЕШЕНИЕ 3: Попытка исправить оригинальный CTE
class TreeTaskViewSetFixedCTE(viewsets.GenericViewSet, mixins.ListModelMixin):
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

        # Попробуем другой подход к CTE
        def make_tasks_cte(cte):
            # Создаем базовый QuerySet с явными именами таблиц
            base_qs = TaskRelation.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).values(
                task_id=F("task_id"),
                parent_task_id=Value(None, output_field=IntegerField()),
                depth=Value(0, output_field=IntegerField())
            )

            # Для рекурсивной части используем .extra() с правильной ссылкой на CTE
            recursive_qs = TaskRelation.objects.filter(
                content_type=task_ct
            ).extra(
                tables=['cte'],
                where=['tasks_taskrelation.object_id = cte.task_id']
            ).values(
                task_id=F("task_id"),
                parent_task_id=F("object_id"),
                depth=Value(1, output_field=IntegerField())  # Упрощенная глубина
            )

            return base_qs.union(recursive_qs, all=True)

        tasks_cte = With.recursive(make_tasks_cte, name='cte')

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