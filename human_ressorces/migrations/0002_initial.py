# Generated by Django 5.1.1 on 2024-09-29 16:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('human_ressorces', '0001_initial'),
        ('pages', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='wishlist',
            field=models.ManyToManyField(blank=True, related_name='wishlisted_by', to='pages.painting'),
        ),
        migrations.AddField(
            model_name='absence',
            name='atelier',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='human_ressorces.atelier'),
        ),
        migrations.AddField(
            model_name='profile',
            name='atelier_absent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='absent_profiles', to='human_ressorces.atelier'),
        ),
        migrations.AddField(
            model_name='profile',
            name='ateliers',
            field=models.ManyToManyField(blank=True, to='human_ressorces.atelier'),
        ),
        migrations.AddField(
            model_name='absence',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='human_ressorces.profile'),
        ),
        migrations.AlterUniqueTogether(
            name='absence',
            unique_together={('profile', 'date_from', 'atelier')},
        ),
    ]
