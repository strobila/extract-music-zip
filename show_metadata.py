import argparse
import os
from tinytag import TinyTag


def show_metadata(audio_file: str):
    """
    オーディオファイルのメタデータを表示
    Parameters:
        audio_file (str): オーディオファイルのパス
    """
    if not os.path.isfile(audio_file):
        print(f'Error: {audio_file} is not a file')
        return
    
    try:
        tag = TinyTag.get(audio_file)
        
        print(f'File: {audio_file}')
        print('=' * 80)
        
        # 基本情報
        print(f'Title:        {tag.title}')
        print(f'Artist:       {tag.artist}')
        print(f'Album:        {tag.album}')
        print(f'Album Artist: {tag.albumartist}')
        print(f'Track:        {tag.track}')
        print(f'Disc:         {tag.disc}')
        print(f'Year:         {tag.year}')
        print(f'Genre:        {tag.genre}')
        print(f'Comment:      {tag.comment}')
        print(f'Composer:     {tag.composer}')
        
        # ファイル情報
        print()
        print(f'Duration:     {tag.duration} seconds')
        print(f'Bitrate:      {tag.bitrate} kBit/s')
        print(f'Sample Rate:  {tag.samplerate} Hz')
        print(f'Channels:     {tag.channels}')
        print(f'File Size:    {tag.filesize} bytes')
        
        # 拡張情報（other）
        if hasattr(tag, 'other') and tag.other:
            print()
            print('Other metadata:')
            for key, value in tag.other.items():
                # 歌詞は長いので別扱い
                if key == 'lyrics':
                    lyrics_preview = value[:100] + '...' if len(value) > 100 else value
                    print(f'  {key}: {lyrics_preview}')
                    print(f'         (Total length: {len(value)} characters)')
                else:
                    print(f'  {key}: {value}')
        
        print('=' * 80)
        
    except Exception as e:
        print(f'Error reading metadata: {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display audio file metadata using TinyTag')
    parser.add_argument('audio_file', help='path to audio file')
    args = parser.parse_args()
    
    show_metadata(args.audio_file)
