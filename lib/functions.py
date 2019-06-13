import os
import collections
import glob
import shutil
import json
import jsonschema
import fnmatch
import hashlib

import jinja2

#from .patterns import *

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


Language = collections.namedtuple('Language',[
    'name',
    'code',
    'directory',
    'files'])
Format = collections.namedtuple('Format', [
    'name',
    'version'])
Category = collections.namedtuple('Category', [
    'lexical',
    'grammatical'])
VocabularyRecord = collections.namedtuple('VocabularyRecord', [
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
WritingRecord = collections.namedtuple('WritingRecord', [
    'phrase',
    'transcription',
    'ipa',
    'image',
    'audio',
    'video',
    'note',
    'format',
    'tags'])
TextRecord = collections.namedtuple('TextRecord', [
    'phrase',
    'transcription',
    'image',
    'audio',
    'video',
    'note',
    'format',
    'tags'])

def get_media_filename(filename):
    media_filename = ''
    
    if filename:
        if os.path.exists(filename):
            media_filename = os.path.abspath(filename)
        else:
            raise Exception(
                'Cannot find file in directory "{current_dir}": {file_name}'.format(
                    current_dir = os.getcwd(),
                    file_name = filename))
    
    return media_filename
    
def get_media_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_language(directory, language):
    
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

def get_record_vocabulary(data, translation, format, tags):
    return VocabularyRecord(
        phrase = data.get('phrase', '').strip(),
        transcription = data.get('transcription', ''),
        category = Category(
            lexical = data.get('category', {}).get('lexical', ''),
            grammatical = None),
        translation = [i.strip() for i in data\
            .get('translation', {})\
            .get(translation, '')\
            .split(';')],
        image = get_media_filename(data.get('image', '')),
        audio = get_media_filename(data.get('audio', '')),
        video = get_media_filename(data.get('video', '')),
        note = [i.strip() for i in data\
            .get('note', {})\
            .get(translation, '')\
            .split(';')],
        format = format,
        tags = tags)
        
    
def get_record_writing(data, translation, format, tags):
                
    return WritingRecord(
        phrase = data.get('phrase', '').strip(),
        transcription = data.get('transcription', ''),
        ipa = data.get('ipa', '').strip(),
        image = get_media_filename(data.get('image', '')),
        audio = get_media_filename(data.get('audio', '')),
        video = get_media_filename(data.get('video', '')),
        note = [i.strip() for i in data\
            .get('note', {})\
            .get(translation, '')\
            .split(';')],
        format = format,
        tags = tags)
        
def get_record_text(data, translation, format, tags):
    
    return TextRecord(
        phrase = data.get('phrase', '').strip(),
        transcription = data.get('transcription', ''),
        image = get_media_filename(data.get('image', '')),
        audio = get_media_filename(data.get('audio', '')),
        video = get_media_filename(data.get('video', '')),
        note = [i.strip() for i in data\
            .get('note', {})\
            .get(translation, '')\
            .split(';')],
        format = format,
        tags = tags)

def get_records(language, format, tag, translation):
    
    current_directory = os.getcwd()
    
    for datafile in language.files:
        with open(datafile, encoding='utf-8') as f:
            langdata = json.loads(f.read())
            
        data_directory = os.path.dirname(datafile)
        os.chdir(data_directory)
        
        status = langdata['meta']['status']
        if not status == 'ready':
            continue
        
        fmt = Format(
            name = langdata['meta']['format'],
            version = langdata['meta']['version'])
        if not fnmatch.fnmatch(fmt.name, format):
            continue
        
        tags = langdata['meta']['tags']
        if not fnmatch.filter(tags, tag):
            continue
        
        for item in langdata['data']:
            if fmt.name == 'vocabulary':
                record = get_record_vocabulary(
                    data = item,
                    translation = translation,
                    format = fmt,
                    tags = tags)
                if not record.phrase: continue
                if not record.translation: continue
            elif fmt.name == 'writing':
                record = get_record_writing(
                    data = item,
                    translation = translation,
                    format = fmt,
                    tags = tags)
                if not record.phrase: continue
            elif fmt.name == 'text':
                record = get_record_text(
                    data = item,
                    translation = translation,
                    format = fmt,
                    tags = tags)
                if not record.phrase: continue
            else:
                raise Exception(
                    'Unsupported format: {name}'.format(
                        name = fmt.name))
            
            yield(record)
        
    os.chdir(current_directory)


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
        if type(record) == VocabularyRecord:
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
            
        elif type(record) == WritingRecord:
            if not record.transcription in data[record.format.name][record.phrase]:
                data[record.format.name][record.phrase][record.transcription] = {
                'ipa': [],
                'image': [],
                'audio': [],
                'video': [],
                'note': [],
                'tags': []}
                
            item = data[record.format.name][record.phrase][record.transcription]
            item['ipa'].append(record.ipa)
            item['image'].append(record.image)
            item['audio'].append(record.audio)
            item['video'].append(record.video)
            
            for I,J in \
                (record.note, item['note']),\
                (record.tags, item['tags']):
                for i in I:
                    if i and not i in J:
                        J.append(i)
        elif type(record) == TextRecord:
            pass
        else:
            raise Exception(
                'Cannot process records of type: {}'.format(
                    type(record).__name__))
    
    return data

def export_media(data, directory):
    image_dir = os.path.join(directory, 'image')
    audio_dir = os.path.join(directory, 'audio')
    video_dir = os.path.join(directory, 'video')
    
    if not os.path.exists(image_dir): os.makedirs(image_dir)
    if not os.path.exists(audio_dir): os.makedirs(audio_dir)
    if not os.path.exists(video_dir): os.makedirs(video_dir)
        
    for phrase in data:
        for transcription in data[phrase]:
            item = data[phrase][transcription]
            
            images = []
            for image in item['image']:
                if image:
                    image_md5 = get_media_md5(image)
                    _, image_extension = os.path.splitext(image)
                    exported_image = os.path.join(
                        image_dir,
                        '{name}{extension}'.format(
                            name = image_md5,
                            extension = image_extension))
                    if not os.path.isfile(exported_image):
                        shutil.copyfile(image, exported_image)
                    images.append(os.path.basename(exported_image))
            item['image'] = images

def export_data(data, language, directory, output):
    templateLoader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), 'template'))
    templateEnv = jinja2.Environment(loader=templateLoader)
    
    for formatname in data:
        media_dir = os.path.join(
            directory, "{}-{}".format(language, formatname))
        export_media(data[formatname], media_dir)
    
        for output_name in 'txt', 'html':
            if not fnmatch.fnmatch(output_name, output):
                continue
            
            template = templateEnv.get_template("{}-{}.{}".format(language, formatname, output_name))
            filename = os.path.join(
                directory, "{}-{}.{}".format(language, formatname, output_name))
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(template.render(data = data[formatname]))
            
            yield filename
