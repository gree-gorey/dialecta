#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os, sndhdr
from info.models import *
from django.utils import timezone


class OverwriteStorage(FileSystemStorage):

    '''
    Overwrite media files when an old one with the same name exists
    '''
    
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name

class Language(models.Model):
  
  name = models.CharField(max_length=50)
  abbreviation = models.CharField(max_length=5)

  def __str__(self):
    return self.abbreviation

class Dialect(models.Model):
  
  name = models.CharField(max_length=50)
  abbreviation = models.CharField(max_length=5)
  to_language = models.ForeignKey('Language')
  description = models.TextField(blank=True)

  def __str__(self):
    return self.abbreviation

class Lemma(models.Model):

  value = models.CharField(max_length=30)
  POS = models.CharField(max_length=10)
  to_language = models.ForeignKey('Language')
  
  class Meta:
    verbose_name_plural = 'Lemmata'

  def __str__(self):
    return self.value

class Form(models.Model):

  value = models.CharField(max_length=30)
  to_lemma = models.ForeignKey(Lemma, verbose_name='to lemma(ta)')
  annotation = models.CharField(max_length=30)
  
  def __str__(self):
    return self.value

class TokenToForm(models.Model):

  order_id = models.IntegerField()
  to_form = models.ForeignKey('Form')
  to_token = models.ForeignKey('Token')

class Token(models.Model):

  transcription = models.CharField(max_length=50)
  to_forms = models.ManyToManyField('Form', through='TokenToForm')

class Recording(models.Model):
  
  #for import from google docs: filename WITHOUT mp3 or wav
  string_id = models.CharField(max_length=30,verbose_name='Unique ID',unique=True) #C
  recording_date = models.DateField(default=timezone.now) #COMPUTED FROM FILENAME
  recording_time = models.TimeField(blank=True, null=True)
  recording_place = models.ForeignKey(Location, blank=True, null=True)

  #should be changed to "transcription"
  data = models.FileField(storage=OverwriteStorage(),blank=True,null=True, verbose_name='Transciption') #look into directory!
  audio = models.FileField(storage=OverwriteStorage(), blank=True, null=True) #look into directory!

  #ONLY for import from google docs: metacomment1, metacomment2, metacomment3 from the Google docs columns A, B and D
  metacomment1 = models.CharField(max_length=100,blank=True,verbose_name='MetaComment1') #A
  metacomment2 = models.CharField(max_length=100,blank=True,verbose_name='MetaComment2') #B
  metacomment3 = models.CharField(max_length=100,blank=True,verbose_name='MetaComment3') #D

  title = models.CharField(blank=True,max_length=100) #G
  topics = models.TextField(blank=True)  #H
  comments = models.TextField(blank=True) #I
  
  #ONLY for import from google docs: "participants", "informant"
  participants_field = models.TextField(verbose_name='OF: participants',blank=True) #I
  informant = models.TextField(verbose_name='OF: informant',blank=True) #T

  location = models.TextField(verbose_name='Location') #U


  recording_device = models.CharField(max_length=60, blank=True) #V
  to_dialect = models.ForeignKey('Dialect', blank=True, null=True,
                                      verbose_name='Dialect')
  to_speakers = models.ManyToManyField(Speaker, blank=True,
                                      verbose_name='Speakers') #THESE TO BE CONSTRUCTED FROM INF1..INF4
  to_interviewers = models.ManyToManyField(Interviewer, blank=True,
                                      verbose_name='Interviewers') #not used right now
  
##  def clean(self):
##    # Don't allow draft entries to have a pub_date.
##    date_and_letter = '_'.join(self.string_id.split('_')[:2])
##
##    if list(similar_id_queryset)!=[]:
##      raise ValidationError({'string_id': _('Recording with this ID already exists.')})

  def __str__(self):
    return self.string_id

  def participants(self):
    from corpora.elan_tools import ElanObject
    if self.data.path:
      try:
        elan_obj = ElanObject(self.data.path)
        return ', '.join(elan_obj.participants_lst)
      except FileNotFoundError:
        pass
    return ''

  def rename_data_file(self, new_name):

    path, old_name = os.path.split(self.data.path)
    new_name = os.path.join(path, '%s.%s' %(new_name, old_name.split('.')[1]))
    os.rename(self.data.path, new_name)
    self.data.name = new_name
    self.save()

  def rename_audio_file(self, new_name):

    path, old_name = os.path.split(self.audio.path)
    new_name = os.path.join(path, '%s.%s' %(new_name, old_name.split('.')[1]))
    os.rename(self.audio.path, new_name)
    self.audio.name = new_name
    self.save()

  def audio_data(self):
    
    if self.audio.path:
      try:
        data = sndhdr.what(self.audio.path)
        data_str = 'filetype: %s, framerate: %s, nchannels: %s, nframes: %s, sampwidth: %s'%(
          data[0], data[1], data[2], data[3], data[4]
          )
        return data_str
      except:
        pass
    return 'None'

  def file_check(self):
        pass

  class Meta:
    verbose_name = 'Recording'
    verbose_name_plural = 'Recordings'

##def recording_unique_queryset(date_and_letter, ):
##    similar_id_queryset = Recording.objects.filter(string_id__contains=date_and_letter)
##    if self.pk:
##        similar_id_queryset = similar_id_queryset.exclude(pk=self.pk)
##    return similar_id_queryset

class Corpus(models.Model):
  
  to_files = models.ManyToManyField(Recording, verbose_name='Elan data')

  class Meta:
    verbose_name_plural = 'Corpora'

class NormalizationModel(models.Model):

  to_dialect = models.ForeignKey('Dialect')
  to_additional_language = models.ForeignKey('Language', blank=True, null=True)
  examples = models.TextField(blank=True)
  exceptions = models.TextField(blank=True)
  
