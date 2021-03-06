# Generated by Django 2.2.9 on 2020-01-22 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifpy', '0002_twitchgame'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('youtube', models.TextField(default='{}')),
                ('twitch', models.TextField(default='{}')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('youtube', models.TextField(default='{}')),
                ('twitch', models.TextField(default='{}')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
