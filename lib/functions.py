import os
import collections
import glob
import shutil
import json
import jsonschema
import fnmatch

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
    Record = collections.namedtuple('Record', [
        'phrase',
        'transcription',
        'grammar',
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
            
            grammar = record.get('category', {}).get('lexical', '')
                
            yield Record(
                phrase = phrase,
                transcription = record.get('transcription', ''),
                grammar = grammar,
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
            
        key = "{record.phrase}/{record.grammar}".format(record = record)
        
        if not key in data[record.format.name]:
            data[record.format.name][key] = {
                'phrase': record.phrase,
                'transcription': record.transcription,
                'grammar': record.grammar,
                'translation': [],
                'image': [],
                'audio': [],
                'video': [],
                'note': [],
                'tags': []}
                
        for I,J in \
            (record.translation, data[record.format.name][key]['translation']),\
            (record.note, data[record.format.name][key]['note']),\
            (record.tags, data[record.format.name][key]['tags']):
            for i in I:
                if i and not i in J:
                    J.append(i)
    
    return data


def export_data(data, language, directory, output):
    for formatname in data:
        filename = os.path.join(
            directory, "{}-{}.txt".format(language, formatname))
        with open(filename, 'w', encoding='utf-8') as f:
            for key in data[formatname]:
                f.write(pattern['anki']['vocabulary'].format(
                    phrase =
                        data[formatname][key]['phrase'],
                    transcription =
                        data[formatname][key]['transcription'],
                    grammar =
                        data[formatname][key]['grammar'],
                    translation =
                        '; '.join(data[formatname][key]['translation']),
                    image =
                        '; '.join(data[formatname][key]['image']),
                    audio =
                        '; '.join(data[formatname][key]['audio']),
                    video =
                        '; '.join(data[formatname][key]['video']),
                    note =
                        '; '.join(data[formatname][key]['note']),
                    tags =
                        ' '.join(data[formatname][key]['tags'])
                    ))
        yield filename