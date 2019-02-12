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

languages = os.listdir(src_dir)

formats = ('model', 'vocabulary', 'text')

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
def build(c, language, format):
    print(
        "Executing task: build --language={language} --format={format}".format(
            language = language,
            format = format))
    
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
            
    for filename in glob.glob(
        "{directory}/{language}/**/*.jdp-lang.json".format(
            directory=src_dir, language=language),
        recursive=True):
        print("Processing file: {filename}".format(filename = filename))


@task
def publish(c):
    print("Executing task: publish")
    print(languages)