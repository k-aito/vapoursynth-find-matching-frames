#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  vapoursynth-find-matching-frames.py
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

"""
vapoursynth-find-matching-frames.py can be used to make reference frames that can be compared on multiple sources
- Define an amount of frames automatically
- Search them in other sources
- Save them on format {source}-{frame reference}-({frame video}) or {frame reference}-{source}-({frame video}) 
"""

################
# PARSING ARGS #
################

import argparse
parser = argparse.ArgumentParser()

# MANDATORY: -s / --sources v1.mkv v2.mkv v3.mkv... (minimum 1)
parser.add_argument("-s", "--sources",
                    required=True,
                    help="Paths of videos sources",
                    nargs='+')
# OPTIONAL: -n / --number 5
parser.add_argument("-n", "--number",
                    required=False,
                    help="Number of frames to be taken in each video (default: 5)",
                    default=5,
                    type=int)
# OPTIONAL: -o / --output
parser.add_argument("-o", "--output",
                    required=False,
                    help="Define output dimension for comparison by example 640x480 (default: it take width and height of the first source)")
# OPTIONAL: -r / --ratio
"""
It doesn't look useful to use a small ratio (1) or the biggest one to make the comparison on a small picture
Sometimes increasing it can help finding the right frame
"""
parser.add_argument("-r", "--ratio",
                    required=False,
                    help="Define the ratio that will downsize the videos for speeding up comparison (default: GCD that is a multiple of 2 * 5)",
                    default=5,
                    type=int)
# OPTIONAL: -p / --precision
"""
It doesn't look really useful to use the 3 planes it got me the same result as only 1
"""
parser.add_argument("-p", "--precision",
                    required=False,
                    help="If set 3 planes (slower) are used to calculate the difference instead of only 1 (default: disabled)",
                    action='store_true')
# OPTIONAL: --noref
parser.add_argument("--noref",
                    required=False,
                    help="If set the frames of the reference source are not saved (default: disabled)",
                    action='store_true')
# OPTIONAL: -f / --frames
parser.add_argument("-f", "--frames",
                    required=False,
                    help="Use the list of frames as reference separate each frames with a comma it (default: disabled)")
# OPTIONAL: -v / --verbose
parser.add_argument("-v", "--verbose",
                    required=False,
                    help="Enable the frame informations while making the comparison (default: disabled)",
                    action='store_true')
# OPTIONAL: --resizer
parser.add_argument("--resizer",
                    required=False,
                    help="Name of the resize to be used in Vapoursynth like core.resize.<resizer> (default: Spline36)",
                    default="Spline36")
# OPTIONAL: -g / --grouping
parser.add_argument("-g", "--grouping",
                    required=False,
                    help="Use FRAME-SOURCES-(ORIGINAL_FRAME).png as output format instead of SOURCES-FRAME-(ORIGINAL_FRAME).png (default: disabled)",
                    action='store_true')

args = parser.parse_args()

###############
# VAPOURSYNTH #
###############

import vapoursynth as vs
import sys
import os
import threading
import pprint
if sys.platform == 'linux':
  import mvsfunc as mvs

core = vs.get_core()

# Define all video sources
s = []
print("INFO: Load sources")
for path in args.sources:
  print("- Load {} with ffms2".format(path))
  s.append(core.ffms2.Source(source=path))
print("")

# Find the max ratio to dowscale the first but that give et multiple of 2
"""
We use the GCD to find the smaller possible value it's the reason we check if the answer is a multiple of 2
If not we just devise the GCD by 2
If args.ratio is set we will define the dimensions by s[0].width / GCD * args.ratio and s[0].height / GCD * args.ratio
"""
import math
gcd = math.gcd(s[0].width, s[0].height)
if (s[0].width / gcd) % 2 != 0 or (s[0].height / gcd) % 2 != 0:
  gcd = gcd / 2

print("INFO: Dimensions of reference source are {}x{}, GCD is {} and ratio is {}".format(s[0].width, s[0].height, gcd, args.ratio))

# For speeding up the process resize s[0] by 4 and adapt the other sources to s_downscale[0]
sd = []
print("INFO: Resize the sources to speedup comparison")
for i, source in enumerate(s):
  if i == 0:
    print("- Resize {} to {}x{}".format(
                                        os.path.basename(args.sources[i]),
                                        (source.width * args.ratio)/gcd,
                                        (source.height * args.ratio)/gcd))
    sd.append(eval("core.resize.{}".format(args.resizer))(
                                  source,
                                  (source.width * args.ratio)/gcd,
                                  (source.height * args.ratio)/gcd,
                                  source.format))
  else:
    print("- Adapt {} to {}".format(os.path.basename(args.sources[i]), os.path.basename(args.sources[0])))
    sd.append(eval("core.resize.{}".format(args.resizer))(source, sd[0].width, sd[0].height, sd[0].format))
print("")

# Just use asked frames if arg.frames is set
print("INFO: Define the frames numbers")
if args.frames != None:
  frames = []
  frames.append([{ "frame": i, "videoframe": sd[0][int(i)] } for i in args.frames.split(',')])
  # If we use defined frames then args.number is equal to the number of frames hat are defined
  args.number = len(frames[0])
else:
  # Define the frame numbers
  """
  TOTAL_FRAMES / COMPARE_FRAMES + 1 give the frame numbers interval
  It let us avoid begin and end frames that are always less usefull
   
  Example:
  We have a total of 100 frames and we want 5 comparison frame
  We do 100 / 5 + 1 = 16 (we need the smallest number self if float so we stay on int)
  The comparison frames will be the next one
  1: 1 * interval = 16
  2: 2 * interval = 32
  3: 3 * interval = 48
  4: 4 * interval = 64
  5: 5 * interval = 80
  """
  # Define interval
  print("- Define the frames interval ({}/{})".format(s[0].num_frames, args.number + 1))
  interval = int(s[0].num_frames / (args.number + 1))

  # Define the frames numbers
  """
  The format of the frames list is a double array [sources][frames numbers]

  Example:
  0: [16, 32, 48, 64, 80] -> # reference frames sd[0]
  1: -> # frames that match for sd[2]
  2: -> # frames that match for sd[...]
  """
  print("- Define the frames for {} with {} as interval".format(os.path.basename(args.sources[0]), interval))
  frames = []
  frames.append([{ "frame": i * interval, "videoframe": sd[0][i * interval] } for i in range(1, args.number + 1)])
  print("")

# Search the same frame in the other sources
"""
Check all the frames of each source and retain the best match for each of them
To speed up the process we check all the frames together because at end each of them will just keep the best match
For speeding up the search process each sources (without the reference) will be scanned separately
"""
print("INFO: Search the same frames in the other sources")
threads = []

for i, source in enumerate(sd):
  # We skip sd[0] because it's the reference
  if i != 0:
    print("- Search for the compared frames in {}".format(os.path.basename(args.sources[i])))
    if args.precision:
      print("- Precision is enabled")
    else:
      print("- Precision is disabled")

    # Workaround we need to precreate the position for list
    frames.append([])
    for _ in range(0, args.number):
      frames[i].append({ "frame": -1, "PlaneStatsDiff": -1 })

    # Compare each frame of the source
    def bestMatch(source, i):
      for numberSourceFrame in range(0, source.num_frames):
        for k, ref in enumerate(frames[0]):
          # Actual frame result
          try:
            # Check difference for all the planes and add them together lowest they are best it match
            if args.precision:
              plane0 = core.std.PlaneStats(ref['videoframe'], source[numberSourceFrame], plane=0).get_frame(0).props['PlaneStatsDiff']
              plane1 = core.std.PlaneStats(ref['videoframe'], source[numberSourceFrame], plane=1).get_frame(0).props['PlaneStatsDiff']
              plane2 = core.std.PlaneStats(ref['videoframe'], source[numberSourceFrame], plane=2).get_frame(0).props['PlaneStatsDiff']
              compare = { "frame": numberSourceFrame, "PlaneStatsDiff": plane0 + plane1 + plane2 }
            else:
              plane0 = core.std.PlaneStats(ref['videoframe'], source[numberSourceFrame], plane=0).get_frame(0).props['PlaneStatsDiff']
              compare = { "frame": numberSourceFrame, "PlaneStatsDiff": plane0 }
          except:
            print("ERROR: {}".format(sys.exc_info()[1]))
            os._exit(1)
          # Take the actual frame if the match is better
          if (frames[i][k]['frame'] == -1) or (frames[i][k]['PlaneStatsDiff'] > compare['PlaneStatsDiff']):
            frames[i][k] = compare
        # Have output each 1000 frames
        if numberSourceFrame % 1000 == 0:
          print("PROGRESS: Source {} after {} frames".format(os.path.basename(args.sources[i]), numberSourceFrame))
          if args.verbose:
            pprint.pprint(frames[i], width=1)

    # Launch a thread for the sd sources without sd[0]
    threads.append(threading.Thread(target=bestMatch, args=(source, i)))

# Start each thread and wait for them to finish before continue
print("- Launch each thread")
print("")
for i in threads:
  i.start()
for i in threads:
  i.join()
print("")

# For using imwri it's based on https://gist.github.com/OrangeChannel/c702baf34b4d4e4383c8209b8eadd8fb
# Imwri is not included by default (for linux) better to take a generic method based on https://gist.github.com/alemonmk/4182404c083a2a25d33a
if sys.platform == "win32" or sys.platform == "win64":
  # Method for saving picture
  method = "imwri plugin"
  def save_picture(clip, filename):
    print("- Save {}".format(filename))
    # It use Point as resize method in th gist but maybe it would be adapter from args.resizer too?
    clip = core.resize.Point(clip,
                              width=clip.width,
                              height=clip.height,
                              format=vs.RGB24,
                              matrix_in_s='709')
    # Use overwrite so that we not need a number in the filename
    out = core.imwri.Write(clip, 'PNG', filename=filename, overwrite=True)
    out.get_frame(0)
else:
  # Method for saving picture
  method = "opencv-python generic method"
  import numpy as np
  import cv2 as cv
  def save_picture(clip, filename):
    print("- Save {}".format(filename))
    # In the gist it use Spline64 but maybe it would be better to use Spline36 like the rest?
    rgbcl = mvs.ToRGB(input=clip, depth=16, kernel='spline64')
    planes_count = rgbcl.format.num_planes
    v = cv.merge([np.array(rgbcl.get_frame(0).get_read_array(i), copy=False) for i in reversed(range(planes_count))])
    cv.imwrite(filename, v)

  # Resize the videos
  print("INFO: Resize the videos")
  for i, source in enumerate(s):
    if args.output is None:
      if i != 0:
        print("- Resize {} to {}x{}".format(os.path.basename(args.sources[i]), s[0].width, s[0].height))
        s[i] = eval("core.resize.{}".format(args.resizer))(source, s[0].width, s[0].height, s[0].format)
    else:
      print("- Resize {} to {}x{}".format(args.sources[i], args.output.split('x')[0], args.output.split('x')[1]))
      s[i] = eval("core.resize.{}".format(args.resizer))(source, args.output.split('x')[0], args.output.split('x')[1], s[0].format)

# Save all the pictures
print("INFO: Save the pictures ({})".format(method))
for i, source in enumerate(frames):
  # Frame of each source
  for j, frame in enumerate(source):
    frameNumber = int(frame['frame'])
    # Use grouping name format if the flag is set
    if args.grouping:
      filename = "{}-{}-({}).png".format(frames[0][j]['frame'], os.path.basename(args.sources[i]), frameNumber)
    else:
      filename = "{}-{}-({}).png".format(os.path.basename(args.sources[i]), frames[0][j]['frame'], frameNumber)
    # Not save s[0] if args.noref == True and display print message only for i == 0
    if args.noref == True and i == 0:
        print("INFO: Reference frames will not be saved")
    elif args.noref == True and i != 0:
        save_picture(s[i][frameNumber], filename)
    else:
      save_picture(s[i][frameNumber], filename)
