import glob
from io import TextIOWrapper
import os
from tinytag import TinyTag


AUDIO_EXTS = ['.mp3', '.flac', '.aac', '.m4a', '.ogg', '.wav', '.aiff']

def get_lyrics(mp3_file: str) -> str:
    """
    オーディオファイルのメタデータから歌詞を取得
    Parameters:
        mp3_file (str): オーディオファイルのパス
    Returns:
        str: 歌詞文字列。歌詞がない場合は None を返す
    """
    lyric_str = None
    tag = TinyTag.get(mp3_file)
    if hasattr(tag, 'extra') and 'lyrics' in tag.extra:
        lyric_str = tag.extra['lyrics']

    return lyric_str


def get_track_title(mp3_file: str) -> str:
    """
    オーディオファイルのメタデータからトラックタイトルを取得
    Parameters:
        mp3_file (str): オーディオファイルのパス
    Returns:
        str: トラックタイトル文字列。タイトルがない場合は None を返す
    """
    title_str = None
    tag = TinyTag.get(mp3_file)
    if hasattr(tag, 'title'):
        title_str = tag.title
    return title_str


def mp3_has_lyric(mp3_file: str) -> bool:
    """
    オーディオファイルのメタデータに歌詞が含まれているかを判定
    Parameters:
        mp3_file (str): オーディオファイルのパス
    Returns:
        bool: 歌詞が含まれている場合は True、そうでない場合は False
    """
    lyric_str = get_lyrics(mp3_file)
    return bool(lyric_str and lyric_str.strip())


def any_mp3_has_lyric(album_dir: str) -> bool:
    """
    アルバムディレクトリ内のいずれかのトラックに歌詞が含まれているかを判定
    Parameters:
        album_dir (str): アルバムディレクトリのパス
    Returns:
        bool: 歌詞が含まれているトラックがある場合は True、そうでない場合は False
    """
    mp3_files = glob.glob(os.path.join(album_dir, '*.mp3'))
    
    for filepath in mp3_files:
        if mp3_has_lyric(filepath):
            return True
    return False


def write_lyric_to_file(mp3_file: str, fout: TextIOWrapper, beginning_lfs: bool = True, ending_lfs: bool = True):
    """
    指定されたオーディオファイルの歌詞をファイルに書き込む
    Parameters:
        mp3_file (str): オーディオファイルのパス
        fout (TextIOWrapper): 書き込み先のファイルオブジェクト
        beginning_lfs (bool): 書き込みの前に改行を挿入するかどうか
        ending_lfs (bool): 書き込みの後に改行を挿入するかどうか
    """
    if beginning_lfs:
        fout.write('\n\n\n')
    fout.write(get_track_title(mp3_file) + '\n')

    lyric_str = get_lyrics(mp3_file)
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
    
    mp3_files = glob.glob(os.path.join(album_dir, '*.mp3'))
    
    if not mp3_files:
        return None
    

    if dst_filename is None:
        dst_filename = os.path.basename(album_dir) + '.lyric'

    dst_filepath = os.path.join(album_dir, dst_filename)

    with open(dst_filepath, 'w', encoding='utf-8', newline='\n') as fout:
        for i, mp3_file in enumerate(mp3_files):
            write_lyric_to_file(mp3_file, fout, beginning_lfs=(i == 0))
    
    return dst_filepath


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('album_dir', help='album dir')
    args = parser.parse_args()
    
    have_lyric = any_mp3_has_lyric(args.album_dir)
    print(f'Any track has lyric: {have_lyric}')

    fpath = save_lyrics(args.album_dir)
    print(f'Saved to: {fpath}')
