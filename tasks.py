import os

from invoke import task
from lib import *

src_dir = os.path.abspath('./src')
tmp_dir = os.path.abspath('./tmp')
out_dir = os.path.abspath('./out')
tool_dir = os.path.abspath('./tool')


@task
def test(c, language = '*', format = '*', tag = '*'):
    for lang in get_language(directory=src_dir, language = language):
        print("[{lang.code}] {lang.name}: {lang.directory}".format(lang = lang))
        for filename in lang.files:
            print("      - {filename}".format(filename = filename))
        #for record in get_data(language = lang, format = format, tag = tag):
        #    print("      - {rec.phrase} ({tags})".format(rec = record, tags = ', '.join(record.tags)))

@task
def validate(c, language = '*'):
    validate_schema(
        schema_dir = os.path.join(tool_dir, 'schema'),
        data_dir = os.path.join(src_dir, language))

@task
def clean(c, output = False):
    directories = [tmp_dir]
    if output:
        directories.append(out_dir)
    delete_directories(*directories)


@task
def build(c, language = '*', format = '*', tag = '*'):
    #create_directories(tmp_dir, out_dir)
    create_directories(out_dir)
    
    for lang in get_language(directory=src_dir, language = language):
        print("[{lang.code}] {lang.name}: {lang.directory}".format(lang = lang))
        data = get_data(language = lang, format = format, tag = tag)
        for filename in export_data(
            data = data, language = lang.code, directory = out_dir):
            print("      - {filename}".format(filename = filename))


#@task
#def publish(c):
#    print("Executing task: publish")