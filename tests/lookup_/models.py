from django.db import models


class Number(models.Model):
    num = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ("num",)

    def __str__(self):
        return str(self.num)
