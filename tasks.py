import os
import glob
import shutil
import json
import collections

from invoke import task

src_dir = os.path.abspath('./src')
tmp_dir = os.path.abspath('./tmp')
out_dir = os.path.abspath('./out')

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