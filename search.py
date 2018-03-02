from __future__ import unicode_literals
from __future__ import print_function
import sys
from subprocess import call, check_output
from glob import glob
import videogrep
import re
import os
from vidpy import Composition, Clip, config
from multiprocessing import Pool

config.MELT_BINARY = 'melt'

def download_subtitles(q, page=1, total_pages=1):
    url = 'https://www.youtube.com/results?search_query={},cc&page={}'.format(q, page)
    call(['youtube-dl', url, '--write-auto-sub', '--skip-download', '-o', '%(id)s'])

    if page < total_pages:
        download_subtitles(q, page+1, total_pages)


def get_timestamps(q):

    comp = {}
    for f in glob('*.vtt'):
        with open(f, 'r') as infile:
            text = infile.read()
            if '::cue' not in text:
                continue
            sentences = videogrep.parse_auto_sub(text)

            for s in sentences:
                for w in s['words']:
                    if re.search(q, w['word']):
                        vid = f.replace('.en.vtt', '')
                        if vid not in comp:
                            comp[vid] = []
                        if w['end'] - w['start'] > 0:
                            comp[vid].append(w)

    return comp


def get_vid_url(vid):
    print(vid)
    try:
        url = check_output(['youtube-dl', '-f', '22', '-g', 'https://www.youtube.com/watch?v={})'.format(vid)])
        url = url.decode('utf-8').strip()
        return (vid, url)
    except:
        return (vid, None)


def download_segment(url, start, end, outname):
    args = ['melt', url, 'in=:{}'.format(start), 'out=:{}'.format(end), '-consumer', 'avformat:{}'.format(outname)]
    call(args)
    return outname


def compose(timestamps):
    p = Pool(processes=5)
    _urls = p.map(get_vid_url, timestamps.keys())
    urls = {}
    for v, u in _urls:
        if u:
            urls[v] = u


    to_download = []
    i = 0
    for vid in timestamps:
        if vid not in urls:
            continue

        words = timestamps[vid]

        for w in words:
            start = w['start']
            end = w['end'] + 0.02
            outname = str(i).zfill(4) + '.mp4'
            to_download.append((urls[vid], start, end, outname))
            i += 1
            # if os.path.exists(outname):
            #     i += 1
            #     continue


    clipnames = p.starmap(download_segment, to_download)

    clips = []
    for f in clipnames:
        clips.append(Clip(f))

    comp = Composition(clips, singletrack=True)
    comp.save('supercut.mp4')


def main():
    download_subtitles(sys.argv[1], page=1, total_pages=5)
    comp = get_timestamps(sys.argv[1])
    compose(comp)


if __name__ == '__main__':
    main()


