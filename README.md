# lang-data

The goal of this project is to be a source of 
machine-readable data useful for people learning
foreign languages.

Example of such data are: vocabulary lists, model
sentences, conjugation and declination tables,
samples of handwriting, pronunciation recordings etc.

The data files are not in the format of any specific
application -- to use it in an application like Anki
you have to import it first.


## Language code lookup

Languages are identified by their three-letter code,
which you can look up here:

https://iso639-3.sil.org/code_tables/639/data


## Preferred file formats

To make the processing of the data easy,
this projects defines preferred file formats:

- JSON for the structured data; YAML is the second choice
- Plain text for unformatted, unstructured text data
- Markdown for formatted text; HTML is the second choice
- SVG for images; PNG is the second choice; A7 size for image is preferred

