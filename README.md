# Manga Splitter

Splits manga pages into 3 overlapping portions, making them easier to read in landscape mode in 6 inch
devices (Kindle Paperwhite 4 and Kobo Clara Colour).

* Also trims whitespace margins.

## Usage

Basic usage:
```
main.py -i manga.cbz
```

Will produce a file called `manga_processed.cbz` as a result.

## Options

```
-i: input file
--device-width: target device width, defaults to 1072.
--device-height: target device height, defaults to 1648.
-w: amount of workers for parallel processing of pages.
-q: jpeg quality, defaults to 50.
```

## Notes

This is made to fit my specific use case so not many options are available at this time.
