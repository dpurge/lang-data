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

#languages = os.listdir(src_dir)

#formats = ('model', 'vocabulary', 'text')

pattern = {
    'anki': {
        'vocabulary': "{phrase}\t{transcription}\t{grammar}\t{translation}\t{image}\t{audio}\t{video}\t{note}\t{tags}\n"
    }
}

Model = collections.namedtuple('Model', [
    'phrase',
    'transcription',
    'translation',
    'audio',
    'video',
    'note'])

Vocabulary = collections.namedtuple('Vocabulary', [
    'phrase',
    'transcription',
    'grammar',
    'translation',
    'audio',
    'video',
    'note'])

Text = collections.namedtuple('Text', [
    'text',
    'transcription',
    'translation',
    'audio',
    'video',
    'note'])

@task
def validate(c):
    schema = {}
    #print('Loading schema files...')
    
    try:
        for filename in glob.glob(
            "{directory}/schema/**/*.json".format(directory=tool_dir),
            recursive=True):
            format = os.path.splitext(os.path.basename(filename))[0]
            with open(filename, encoding='utf-8') as f:
                schema[format] = json.loads(f.read())
    except Exception as e:
        print('Failed to load schema file: {message}'.format(message = str(e)))
        
    for filename in glob.glob(
        "{directory}/**/*.json".format(directory=src_dir),
        recursive=True):
        #print("Validating file: {filename}".format(filename = filename))
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
            print('{filename}: {message}'.format(filename = filename, message = e.message))
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
def build(c):
    #print(
    #    "Executing task: build --language={language} --format={format}".format(
    #        language = language,
    #        format = format))
    
    for dir in tmp_dir, out_dir:
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
            #else:  
            #    print(
            #        "Directory created: {directory}".format(
            #            directory = dir))
            
    for langfile in glob.glob(
        "{directory}/**/language.json".format(directory=src_dir),
        recursive=True):
        with open(langfile, encoding='utf-8') as f:
                langmeta = json.loads(f.read())
        langname = langmeta['data']['name']
        langcode = langmeta['data']['code']
        
        print("Processing language: {langname} ({langcode})".format(
            langname = langname,
            langcode = langcode))
        data = {}
        for datafile in glob.glob(
            "{directory}/**/*.jdp-lang.json".format(
                directory= os.path.dirname(langfile)),
            recursive=True):
            with open(datafile, encoding='utf-8') as f:
                langdata = json.loads(f.read())
            formatname = langdata['meta']['format']
            formatversion = langdata['meta']['version']
            datastatus = langdata['meta']['status']
            tags = langdata['meta']['tags']
            records = langdata['data']
            
            if not formatname in data:
                data[formatname] = {}
            for record in records:
                if not record['phrase'] or not record['translation']:
                    continue
                key = "{phrase}/{grammar}".format(
                    phrase = record['phrase'], grammar = record['grammar'])
                if not key in data[formatname]:
                    data[formatname][key] = {
                        'phrase': record['phrase'],
                        'transcription': record['transcription'],
                        'grammar': record['grammar'],
                        'translation': [],
                        'image': [],
                        'audio': [],
                        'video': [],
                        'note': [],
                        'tags': []
                    }
                for translation in record['translation'].split(';'):
                    translation = translation.strip()
                    if not translation in data[formatname][key]['translation']:
                        data[formatname][key]['translation'].append(translation)
                for note in record['note'].split(';'):
                    note = note.strip()
                    if not note in data[formatname][key]['note']:
                        data[formatname][key]['note'].append(note)
                for tag in tags:
                    if not tag in data[formatname][key]['tags']:
                        data[formatname][key]['tags'].append(tag)
        
        for formatname in data:
            with open(
                '{directory}/{filename}.txt'.format(
                    directory = out_dir,
                    filename = "{}-{}".format(langcode, formatname)),
                'w', encoding='utf-8') as f:
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