# vapoursynth-find-matching-frames

## Goal

The goal of this script was to be able to compare easily multiple source without the need to define and search the frames that must be compared.

## Requirements

* [Debian](DEBIAN.md)

* [Windows](WINDOWS.md)

## Use

```
usage: vapoursynth-find-matching-frames.py [-h] -s SOURCES [SOURCES ...]
                                           [-n NUMBER] [-o OUTPUT] [-r RATIO]
                                           [-p] [--noref] [-f FRAMES] [-v]
                                           [--resizer RESIZER] [-g] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCES [SOURCES ...], --sources SOURCES [SOURCES ...]
                        Paths of videos sources
  -n NUMBER, --number NUMBER
                        Number of frames to be taken in each video (default:
                        5)
  -o OUTPUT, --output OUTPUT
                        Define output dimension for comparison by example
                        640x480 (default: it take width and height of the
                        first source)
  -r RATIO, --ratio RATIO
                        Define the ratio that will downsize the videos for
                        speeding up comparison (default: GCD that is a
                        multiple of 2 * 5)
  -p, --precision       If set 3 planes (slower) are used to calculate the
                        difference instead of only 1 (default: disabled)
  --noref               If set the frames of the reference source are not
                        saved (default: disabled)
  -f FRAMES, --frames FRAMES
                        Use the list of frames as reference separate each
                        frames with a comma it (default: disabled)
  -v, --verbose         Enable the frame informations while making the
                        comparison (default: disabled)
  --resizer RESIZER     Name of the resize to be used in Vapoursynth like
                        core.resize.<resizer> (default: Spline36)
  -g, --grouping        Use FRAME-SOURCES-(ORIGINAL_FRAME).png as output
                        format instead of SOURCES-FRAME-(ORIGINAL_FRAME).png
                        (default: disabled)
  -c, --common          Doesn't search for matching frames because the encodes
                        comes from the same source (default: disabled)
```


## Example

```bash
vapoursynth-find-matching-frames.py --sources source1.mkv source2.mkv
```

## Common issues

* Threading is used based on source so it's not really optimized and the process can be a bit slow
* Sometimes deadlock can happen, I guess it's Threading related but `CTRL+C` or relauching the process is enough to continue

## Screencomparison websites

* [Screenshotcomparison](https://screenshotcomparison.com/) but limited to 2 pictures only
* [Slow.pics](https://slow.pics/) better support if you have multiple sources and pictures

## Credits

* Use IMWRI to save pictures (https://gist.github.com/OrangeChannel/c702baf34b4d4e4383c8209b8eadd8fb)
* Use a generic method to save pictures (https://gist.github.com/alemonmk/4182404c083a2a25d33a)

## Similar projects

* [LVSFunc](https://lvsfunc.readthedocs.io/en/latest/#module-lvsfunc.comparison) have the same process to compare frames but his goal is more about finding differences than finding matching frames
