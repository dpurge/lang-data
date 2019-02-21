import os
import glob
import shutil
import json
import jsonschema
import collections

from invoke import task

src_dir = os.path.abspath('./src')
tmp_dir = os.path.abspath('./tmp')
out_dir = os.path.abspath('./out')
tool_dir = os.path.abspath('./tool')

pattern = {
    'anki': {
        'vocabulary': "{phrase}\t{transcription}\t{grammar}\t{translation}\t{image}\t{audio}\t{video}\t{note}\t{tags}\n"
    }
}

    
def create_directories(*directories):
    
    for dir in directories:
        if (not os.path.exists(dir)):
            print(
                "Creating directory: {directory}".format(
                    directory = dir))
            try:  
                os.makedirs(dir)
            except OSError:  
                print(
                    "Cannot create directory: {directory}".format(
                        directory = dir))


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


def get_language(directory, language):
    Language = collections.namedtuple('Language', ['name', 'code', 'directory', 'files'])
    for filename in glob.glob(os.path.join(directory, language, 'language.json'), recursive = True):
        with open(filename, encoding='utf-8') as f:
                lang = json.loads(f.read())
        name = lang['data']['name']
        code = lang['data']['code']
        dir  = os.path.dirname(filename)
        files = (datafile for datafile in glob.glob(os.path.join(dir, '**', '*.jdp-lang.json'), recursive=True))
        
        yield Language(
            name = name,
            code = code,
            directory = dir,
            files = files)

def get_data(language, format, tag):
    Format = collections.namedtuple('Format', ['name', 'version'])
    Record = collections.namedtuple('Record', [
        'phrase',
        'transcription',
        'grammar',
        'translation',
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
        
        for record in langdata['data']:
            if not record['phrase'] or not record['translation']:
                continue
            yield Record(
                phrase = record['phrase'],
                transcription = record['transcription'],
                grammar = record['grammar'],
                translation = record['translation'],
                audio = record['audio'],
                video = record['video'],
                note = record['note'],
                format = Format(
                    name = langdata['meta']['format'],
                    version = langdata['meta']['version']),
                tags = langdata['meta']['tags'])


@task
def test(c, language = '*', format = '*', tag = '*'):
    for lang in get_language(directory=src_dir, language = language):
        print("[{lang.code}] {lang.name}: {lang.directory}".format(lang = lang))
        #for filename in lang.files:
        #    print("      - {filename}".format(filename = filename))
        for record in get_data(language = lang, format = format, tag = tag):
            print("      - {rec.phrase} ({tags})".format(rec = record, tags = ', '.join(record.tags)))

@task
def validate(c, language = '*'):
    schema = get_schema(directory = os.path.join(tool_dir, 'schema'))
        
    for filename in glob.glob(os.path.join(src_dir, language, '**', '*.json'), recursive = True):
        try:
            with open(filename, encoding='utf-8') as f:
                jsondata = json.loads(f.read())
            if not 'meta' in jsondata:
                raise Exception("Missing required 'meta' key in: {filename}".format(filename = filename))
            if not 'format' in jsondata['meta']:
                raise Exception("Missing required 'format' key in: {filename}".format(filename = filename))
            if not 'version' in jsondata['meta']:
                raise Exception("Missing required 'version' key in: {filename}".format(filename = filename))
            jsonschema.validate(jsondata, schema['{format}-{version}'.format(format=jsondata['meta']['format'], version=jsondata['meta']['version'])])
        except jsonschema.exceptions.ValidationError as e:
            print('{filename} ({path}): {message}'.format(filename = filename, message = e.message, path = e.path))
        except Exception as e:
            print('{filename}: {message}'.format(filename = filename, message = str(e)))

@task
def clean(c, output = False):
    print("Executing task: clean")
    if (os.path.exists(tmp_dir)):
        print(
            "Deleting temporary directory: {directory}".format(
                directory = tmp_dir))
        shutil.rmtree(tmp_dir)
    if (output and os.path.exists(out_dir)):
        print(
            "Deleting output directory: {directory}".format(
                directory = out_dir))
        shutil.rmtree(out_dir)


@task
def build(c, language = '*', format = '*', tag = '*'):
    
    create_directories(tmp_dir, out_dir)
            
    for lang in get_language(directory=src_dir, language = language):
        print("[{lang.code}] {lang.name}: {lang.directory}".format(lang = lang))
        data = {}
        
        for record in get_data(language = lang, format = format, tag = tag):
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
                    
            for translation in record.translation.split(';'):
                translation = translation.strip()
                if not translation in data[record.format.name][key]['translation']:
                    data[record.format.name][key]['translation'].append(translation)
            for note in record.note.split(';'):
                note = note.strip()
                if not note in data[record.format.name][key]['note']:
                    data[record.format.name][key]['note'].append(note)
            for tagname in record.tags:
                if not tagname in data[record.format.name][key]['tags']:
                    data[record.format.name][key]['tags'].append(tagname)
        
        for formatname in data:
            with open(os.path.join(out_dir, "{}-{}".format(lang.code, formatname)), 'w', encoding='utf-8') as f:
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


@task
def publish(c):
    print("Executing task: publish")
    #print(languages)