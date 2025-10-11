import glob
import os
from tinytag import TinyTag


def get_lyrics(mp3_file: str) -> str:
    lyric_str = None
    tag = TinyTag.get(mp3_file)
    if hasattr(tag, 'extra') and 'lyrics' in tag.extra:
        lyric_str = tag.extra['lyrics']

    return lyric_str


def get_track_title(mp3_file: str) -> str:
    title_str = None
    tag = TinyTag.get(mp3_file)
    if hasattr(tag, 'title'):
        title_str = tag.title
    return title_str


def mp3_has_lyric(mp3_file: str) -> bool:
    lyric_str = get_lyrics(mp3_file)
    return bool(lyric_str and lyric_str.strip())


# Check if any track in 'album_dir' have lyrics
def any_mp3_has_lyric(album_dir: str) -> bool:
    mp3_files = glob.glob(os.path.join(album_dir, '*.mp3'))
    
    for filepath in mp3_files:
        if mp3_has_lyric(filepath):
            return True
    return False


def save_lyrics(album_dir: str, dst_filename_: str = None) -> str:
    mp3_files = glob.glob(os.path.join(album_dir, '*.mp3'))
    
    if not mp3_files:
        return None
    
    dst_filename = dst_filename_
    if dst_filename_ is None:
        dst_filename = os.path.basename(album_dir) + '.lyric'

    dst_filepath = os.path.join(album_dir, dst_filename)

    with open(dst_filepath, 'w', encoding='utf-8', newline='\n') as fout:
        fout.write('\n\n\n')
        for filepath in mp3_files:
            fout.write(get_track_title(filepath) + '\n')
            
            lyric_str = get_lyrics(filepath)
            if lyric_str:
                fout.write('\n\n' + lyric_str + '\n')
            fout.write('\n\n\n')
    
    return dst_filepath


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('album_dir', help='album dir')
    args = parser.parse_args()
    
    fpath = dump_lyrics(args.album_dir)
    print(f'Saved to: {fpath}')
