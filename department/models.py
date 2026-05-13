from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                name='uniq_department_parent_name',
            ),
        ]

    def __str__(self) -> str:
        return self.name
