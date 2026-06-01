# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Authors(models.Model):
    id_wikipedia = models.CharField(db_column='id_Wikipedia', unique=True, max_length=20)  # Field name made lowercase.
    id_openlibrary = models.CharField(db_column='id_OpenLibrary', unique=True, max_length=20)  # Field name made lowercase.
    name = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.CharField(max_length=510, blank=True, null=True)
    wikipedia_url = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    img_author = models.CharField(max_length=510, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Authors'


class Books(models.Model):
    id_author = models.ForeignKey(Authors, models.DO_NOTHING, db_column='id_Author')  # Field name made lowercase.
    title = models.CharField(max_length=100, blank=True, null=True)
    id_openlibrary = models.CharField(db_column='id_OpenLibrary', max_length=20, blank=True, null=True)  # Field name made lowercase.
    first_publish_year = models.IntegerField(blank=True, null=True)
    edition_count = models.IntegerField(blank=True, null=True)
    cover_id = models.CharField(max_length=20, blank=True, null=True)
    cover_url = models.CharField(max_length=50, blank=True, null=True)
    ratings_average = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    ratings_count = models.IntegerField(blank=True, null=True)
    want_to_read_count = models.IntegerField(blank=True, null=True)
    first_sentence = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    subjects = models.TextField(blank=True, null=True)
    links = models.TextField(blank=True, null=True)
    quote_1 = models.CharField(max_length=510, blank=True, null=True)
    quote_2 = models.CharField(max_length=510, blank=True, null=True)
    quote_3 = models.CharField(max_length=510, blank=True, null=True)
    quote_4 = models.CharField(max_length=510, blank=True, null=True)
    quote_5 = models.CharField(max_length=510, blank=True, null=True)
    available = models.IntegerField(blank=True, null=True)
    img_book = models.CharField(max_length=510, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Books'


class Variables(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    value = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Variables'
