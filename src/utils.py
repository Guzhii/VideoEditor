#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 22:04:17 2021

@author: yujiaohao
"""
import os
import subprocess


def downsample_video(video_input_path, video_output_path):
    c = 'ffmpeg -y -i ' + video_input_path + ' -r 30 -c:v libx264 -b:v 3M -strict -2 -movflags faststart ' + video_output_path
    subprocess.call(c, shell=True)


def ffmpeg_extract_subclip(filename, t1, t2, targetname=None):
    """ Makes a new video file playing video file ``filename`` between
        the times ``t1`` and ``t2``. """
    name, ext = os.path.splitext(filename)
    if not targetname:
        T1, T2 = [int(1000 * t) for t in [t1, t2]]
        targetname = "%sSUB%d_%d.%s" % (name, T1, T2, ext)

    cmd = ['ffmpeg', "-y",
           "-ss", "%0.2f" % t1,
           "-i", filename,
           "-t", "%0.2f" % (t2 - t1),
           "-map", "0", "-vcodec", "copy", "-acodec", "copy", targetname]

    subprocess.call(cmd)


def ffmpeg_convert_to_avi(filename, output="tmp.avi"):

    cmd = ['ffmpeg', "-y",
           "-i", filename,
           "-c:v", "libx264",
           "-c:a", "libmp3lame",
           "-b:a", "384K",
           output]

    subprocess.call(cmd)

    return output
