import glob
from io import TextIOWrapper
import os
from tinytag import TinyTag


AUDIO_EXTS = ['.mp3', '.flac', '.aac', '.m4a', '.ogg', '.wav', '.aiff']


def get_audio_files(album_dir: str) -> list[str]:
    """
    指定されたディレクトリ内のすべての対応オーディオファイルを取得
    Parameters:
        album_dir (str): アルバムディレクトリのパス
    Returns:
        list[str]: オーディオファイルのパスのリスト
    """
    audio_files = []
    for ext in AUDIO_EXTS:
        audio_files.extend(glob.glob(os.path.join(album_dir, f'*{ext}')))
    return audio_files


def get_lyrics(audio_file: str) -> str:
    """
    オーディオファイルのメタデータから歌詞を取得
    Parameters:
        audio_file (str): オーディオファイルのパス
    Returns:
        str: 歌詞文字列。歌詞がない場合は None を返す
    """
    lyric_str = None
    tag = TinyTag.get(audio_file)
    if hasattr(tag, 'other'):
        if 'lyrics' in tag.other:
            lyric_str = tag.other['lyrics']
        elif 'unsyncedlyrics' in tag.other:
            lyric_str = tag.other['unsyncedlyrics']
        
        if isinstance(lyric_str, list):
            lyric_str = lyric_str[0]

    return lyric_str


def get_track_title(audio_file: str) -> str:
    """
    オーディオファイルのメタデータからトラックタイトルを取得
    Parameters:
        audio_file (str): オーディオファイルのパス
    Returns:
        str: トラックタイトル文字列。タイトルがない場合は None を返す
    """
    title_str = None
    tag = TinyTag.get(audio_file)
    if hasattr(tag, 'title'):
        title_str = tag.title
    return title_str


def audio_has_lyric(audio_file: str) -> bool:
    """
    オーディオファイルのメタデータに歌詞が含まれているかを判定
    Parameters:
        audio_file (str): オーディオファイルのパス
    Returns:
        bool: 歌詞が含まれている場合は True、そうでない場合は False
    """
    lyric_str = get_lyrics(audio_file)
    return bool(lyric_str and lyric_str.strip())


def any_audio_has_lyric(album_dir: str) -> bool:
    """
    アルバムディレクトリ内のいずれかのトラックに歌詞が含まれているかを判定
    Parameters:
        album_dir (str): アルバムディレクトリのパス
    Returns:
        bool: 歌詞が含まれているトラックがある場合は True、そうでない場合は False
    """
    audio_files = get_audio_files(album_dir)
    
    for filepath in audio_files:
        if audio_has_lyric(filepath):
            return True
    return False


def write_lyric_to_file(audio_file: str, fout: TextIOWrapper, beginning_lfs: bool = True, ending_lfs: bool = True):
    """
    指定されたオーディオファイルの歌詞をファイルに書き込む
    Parameters:
        audio_file (str): オーディオファイルのパス
        fout (TextIOWrapper): 書き込み先のファイルオブジェクト
        beginning_lfs (bool): 書き込みの前に改行を挿入するかどうか
        ending_lfs (bool): 書き込みの後に改行を挿入するかどうか
    """
    if beginning_lfs:
        fout.write('\n\n\n')
    fout.write(get_track_title(audio_file) + '\n')

    lyric_str = get_lyrics(audio_file)
    if lyric_str:
        fout.write('\n\n' + lyric_str + '\n')
    if ending_lfs:
        fout.write('\n\n\n')


def is_audio_file(filepath: str) -> bool:
    """
    指定されたファイルが対応するオーディオファイルかどうかを判定
    Parameters:
        filepath (str): ファイルのパス
    Returns:
        bool: 対応するオーディオファイルであれば True、そうでなければ False
    """
    ext = os.path.splitext(filepath)[1].lower()
    return ext in AUDIO_EXTS



def save_lyrics(album_dir: str, dst_filename: str = None) -> str:
    """アルバムディレクトリ内のすべてのオーディオファイルから歌詞を抽出し、テキストファイルに保存する
    Parameters:
        album_dir (str): アルバムディレクトリのパス
        dst_filename (str): 保存する歌詞ファイルの名前。None の場合はアルバムディレクトリ名を使用
    Returns:
        str: 保存された歌詞ファイルのパス
    """
    if os.path.isfile(album_dir) and is_audio_file(album_dir):
        audio_filepath = album_dir
        album_dir = os.path.dirname(album_dir)
        audio_filename = os.path.basename(audio_filepath)
        lyric_filename = os.path.splitext(audio_filename)[0] + '.lyric'
        dst_filepath = os.path.join(album_dir, lyric_filename)
        with open(dst_filepath, 'w', encoding='utf-8', newline='\n') as fout:
            write_lyric_to_file(audio_filepath, fout)
        return dst_filepath
    
    audio_files = get_audio_files(album_dir)
    
    if not audio_files:
        return None
    

    if dst_filename is None:
        dst_filename = os.path.basename(album_dir) + '.lyric'

    dst_filepath = os.path.join(album_dir, dst_filename)

    with open(dst_filepath, 'w', encoding='utf-8', newline='\n') as fout:
        for i, audio_file in enumerate(audio_files):
            write_lyric_to_file(audio_file, fout, beginning_lfs=(i == 0))
    
    return dst_filepath


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('artist_dir', help='artist directory path')
    args = parser.parse_args()
    
    artist_dir = args.artist_dir
    
    if not os.path.isdir(artist_dir):
        print(f'Error: {artist_dir} is not a directory')
        exit(1)
    
    # アーティストディレクトリ直下のアルバムディレクトリを列挙
    album_dirs = [
        os.path.join(artist_dir, item)
        for item in os.listdir(artist_dir)
        if os.path.isdir(os.path.join(artist_dir, item))
    ]
    
    if not album_dirs:
        print(f'No album directories found in {artist_dir}')
        exit(0)
    
    print(f'Found {len(album_dirs)} album directory(ies)')
    
    for album_dir in album_dirs:
        album_name = os.path.basename(album_dir)
        
        # *.lyricファイルの存在チェック
        lyric_files = glob.glob(os.path.join(album_dir, '*.lyric'))
        
        if lyric_files:
            print(f'[{album_name}] Lyric file already exists, skipping')
            continue
        
        # 歌詞を含むオーディオファイルの存在チェック
        if any_audio_has_lyric(album_dir):
            print(f'[{album_name}] Extracting lyrics...')
            fpath = save_lyrics(album_dir)
            if fpath:
                print(f'[{album_name}] Saved to: {os.path.basename(fpath)}')
            else:
                print(f'[{album_name}] Failed to save lyrics')
        else:
            print(f'[{album_name}] No lyrics found')
    
    print('Done.')
