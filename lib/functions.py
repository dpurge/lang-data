import os
import collections
import glob
import shutil
import json
import jsonschema
import fnmatch

import jinja2

from .patterns import *

def create_directories(*directories):
    
    for directory in directories:
        if (not os.path.exists(directory)):
            print(
                "Creating directory: {directory}".format(
                    directory = directory))
            try:  
                os.makedirs(directory)
            except OSError:  
                print(
                    "Cannot create directory: {directory}".format(
                        directory = directory))

def delete_directories(*directories):
        
    for directory in directories:
        if (os.path.exists(directory)):
            print(
                "Deleting directory: {directory}".format(
                    directory = directory))
            shutil.rmtree(directory)


def get_schema(directory):
    schema = {}
    
    try:
        for filename in glob.glob(os.path.join(directory, '**', '*.json'), recursive = True):
            format = os.path.splitext(os.path.basename(filename))[0]
            with open(filename, encoding='utf-8') as f:
                schema[format] = json.loads(f.read())
    except Exception as e:
        print('Failed to load schema file: {message}'.format(message = str(e)))
        
    return schema


def validate_schema(schema_dir, data_dir):
        
    schema = get_schema(directory = schema_dir)
        
    for filename in glob.glob(
        os.path.join(data_dir, '**', '*.json'), recursive = True):
        try:
            with open(filename, encoding='utf-8') as f:
                jsondata = json.loads(f.read())
            if not 'meta' in jsondata:
                raise Exception("Missing required 'meta' key in: {filename}".format(filename = filename))
            if not 'status' in jsondata['meta']:
                raise Exception("Missing required 'status' key in: {filename}".format(filename = filename))
            #if not jsondata['meta']['status'] == 'ready':
            #    continue
            if not 'format' in jsondata['meta']:
                raise Exception("Missing required 'format' key in: {filename}".format(filename = filename))
            if not 'version' in jsondata['meta']:
                raise Exception("Missing required 'version' key in: {filename}".format(filename = filename))
            jsonschema.validate(jsondata, schema['{format}-{version}'.format(format=jsondata['meta']['format'], version=jsondata['meta']['version'])])
        except jsonschema.exceptions.ValidationError as e:
            print('{filename} ({path}): {message}'.format(filename = filename, message = e.message, path = e.path))
        except Exception as e:
            print('{filename}: {message}'.format(filename = filename, message = str(e)))


def get_language(directory, language):

    Language = collections.namedtuple('Language',
        ['name', 'code', 'directory', 'files'])
        
    for filename in glob.glob(
        os.path.join(directory, language, 'language.json'), recursive = True):
        
        with open(filename, encoding='utf-8') as f:
                lang = json.loads(f.read())
        if lang['meta']['status'] != 'ready':
            continue
        
        name = lang['data']['name']
        code = lang['data']['code']
        dir  = os.path.dirname(filename)
        files = (datafile for datafile in glob.glob(
            os.path.join(dir, '**', '*.jdp-lang.json'), recursive=True))
        
        yield Language(
            name = name,
            code = code,
            directory = dir,
            files = files)

def get_records(language, format, tag, translation):
    Format = collections.namedtuple('Format', ['name', 'version'])
    Category = collections.namedtuple('Category', ['lexical', 'grammatical'])
    Record = collections.namedtuple('Record', [
        'phrase',
        'transcription',
        'category',
        'translation',
        'image',
        'audio',
        'video',
        'note',
        'format',
        'tags'])
    
    for datafile in language.files:
        with open(datafile, encoding='utf-8') as f:
            langdata = json.loads(f.read())
            
        if not langdata['meta']['status'] == 'ready':
            continue
        if not fnmatch.fnmatch(langdata['meta']['format'], format):
            continue
        if not fnmatch.filter(langdata['meta']['tags'], tag):
            continue
        
        for record in langdata['data']:
        
            phrase = record.get('phrase', '').strip()
            if not phrase: continue
            
            translations = [i.strip() for i in record\
                .get('translation', {})\
                .get(translation, '')\
                .split(';')]
            if not translations: continue
            
            notes = [i.strip() for i in record\
                .get('note', {})\
                .get(translation, '')\
                .split(';')]
            
            category = Category(
                lexical = record.get('category', {}).get('lexical', ''),
                grammatical = None)
                
            yield Record(
                phrase = phrase,
                transcription = record.get('transcription', ''),
                category = category,
                translation = translations,
                image = record.get('image', ''),
                audio = record.get('audio', ''),
                video = record.get('video', ''),
                note = notes,
                format = Format(
                    name = langdata['meta']['format'],
                    version = langdata['meta']['version']),
                tags = langdata['meta']['tags'])


def get_data(language, format, tag, translation):
    data = {}
    
    for record in get_records(
        language = language,
        format = format,
        tag = tag,
        translation = translation):
        
        if not record.format.name in data:
            data[record.format.name] = {}
        if not record.phrase in data[record.format.name]:
            data[record.format.name][record.phrase] = {}
        if not record.category.lexical in data[record.format.name][record.phrase]:
            data[record.format.name][record.phrase][record.category.lexical] = {
                'transcription': record.transcription,
                'translation': [],
                'image': [],
                'audio': [],
                'video': [],
                'note': [],
                'tags': []}
            
        item = data[record.format.name][record.phrase][record.category.lexical]
                
        for I,J in \
            (record.translation, item['translation']),\
            (record.note, item['note']),\
            (record.tags, item['tags']):
            for i in I:
                if i and not i in J:
                    J.append(i)
    
    return data

def flatten_data(data):
    for phrase in data:
        lexcat = []
        transcription = []
        translation = []
        image = []
        audio = []
        video = []
        note = []
        tags = []
        
        for pos in data[phrase]:
            if pos: lexcat.append(pos)
            item = data[phrase][pos]
            if not item['transcription'] in transcription: transcription.append(item['transcription'])
            for i in item['translation']:
                if not i in translation: translation.append(i)
            for i in item['image']:
                if not i in image: image.append(i)
            for i in item['audio']:
                if not i in audio: audio.append(i)
            for i in item['video']:
                if not i in video: video.append(i)
            for i in item['note']:
                if not i in note: note.append(i)
            for i in item['tags']:
                if not i in tags: tags.append(i)
            
        yield {
            'phrase': phrase,
            'lexcat': ', '.join(lexcat),
            'transcription': '; '.join(transcription),
            'translation': '; '.join(translation),
            'image': '; '.join(image),
            'audio': '; '.join(audio),
            'video': '; '.join(video),
            'note': '; '.join(note),
            'tags': ' '.join(tags)
        }

def export_data(data, language, directory, output):
    templateLoader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), 'template'))
    templateEnv = jinja2.Environment(loader=templateLoader)
    
    for formatname in data:
        for output_name in 'txt', 'html':
            if not fnmatch.fnmatch(output_name, output):
                continue
            
            template = templateEnv.get_template("{}-{}.{}".format(language, formatname, output_name))
            filename = os.path.join(
                directory, "{}-{}.{}".format(language, formatname, output_name))
            
            with open(filename, 'w', encoding='utf-8') as f:
                if output_name == 'txt':
                    f.write(template.render(data = flatten_data(data[formatname])))
                else:
                    f.write(template.render(data = data[formatname]))
            
            yield filename