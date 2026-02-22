
import os
import argparse
import glob
import zipfile
import shutil

from extract_lyrics import any_audio_has_lyric, audio_has_lyric, save_lyrics, get_audio_files
from extract_lyrics import AUDIO_EXTS

def get_user_folder():
    return os.environ.get('HOMEPATH') or os.environ.get('USERPROFILE')

def parse_args():
    parser = argparse.ArgumentParser(description='Extract music zip file')
    parser.add_argument('-d', '--dst-dir',
        default=os.path.join(get_user_folder(), 'Music'),
        help='destination to extract')
    parser.add_argument('-s', '--search-dir',
        default='.',
        help='search dir')
    parser.add_argument('--old-dir', 
        default=os.path.join('.', 'old'),
        help='directory to store .zip file extraction was done')
    return parser.parse_args()


def split_artist_and_album(file_path: str):
    """ファイル名からアーティスト名とアルバム名を分離して取得する
    Parameters:
        file_path (str): ファイルのパス
    Returns:
        tuple: (artist_name, album_name)
    """
    file_name = os.path.basename(file_path)
    stem, _ = os.path.splitext(file_name)
    return stem.split(' - ', maxsplit=1)   # don't care " - " in artist name


def prepare_sub_directory(dst_dir: str, subdir_name: str) -> str:
    """指定されたディレクトリ内にサブディレクトリを作成し、そのパスを返す
    Parameters:
        dst_dir (str): 親ディレクトリのパス
        subdir_name (str): 作成するサブディレクトリの名前
    Returns:
        str: 作成されたサブディレクトリのパス
    """
    subdir_path = os.path.join(dst_dir, subdir_name)
    if not os.path.isdir(subdir_path):
        os.mkdir(subdir_path)
    return subdir_path


ARTIST_NAME_REPL_LIST = {
    '𝙎𝙤𝙧𝙚𝙘𝙖𝙪𝙨𝙖𝙦𝙞𝙘𝙝': 'Sorecausaqich'
}

def replace_unwanted_artist_name(artist_name: str):
    s = artist_name
    for k, v in ARTIST_NAME_REPL_LIST.items():
        s = s.replace(k, v)
    return s


if __name__ == "__main__":
    args = parse_args()

    print(f'search dir: {args.search_dir}')
    print(f'dst dir:    {args.dst_dir}')
    print(f'old dir:    {args.old_dir}')
    print('')

    if not os.path.isdir(args.search_dir):
        raise RuntimeError(f'search dir is not found ({args.search_dir})')
    if not os.path.isdir(args.dst_dir):
        raise RuntimeError(f'dst dir is not found ({args.dst_dir})')

    print('searching zip file...')
    zip_files = glob.glob(os.path.join(args.search_dir, '*.zip'))

    if zip_files:
        print(f'{len(zip_files)} zip files was found.')

        for zip_file in zip_files:
            zip_basename = os.path.basename(zip_file)
            album_dirname, _ = os.path.splitext(zip_basename)

            artist_name, album_name = split_artist_and_album(zip_basename)
            
            artist_name = replace_unwanted_artist_name(artist_name)
            
            artist_dir = prepare_sub_directory(args.dst_dir, artist_name)
            album_dir = prepare_sub_directory(artist_dir, album_dirname)

            # check if already audio files are stored in album_dir,
            # in order to avoid duplicating processes.
            already_exist_audios = get_audio_files(album_dir)
            if already_exist_audios:
                exist_audios = [os.path.basename(f) for f in already_exist_audios]
                print(f'[WARN] Before Extracting {zip_basename}:')
                print(f'[WARN]   Some audio files are stored in')
                print(f'[WARN]   destination album dir: {album_dir}')
                print(f'[WARN]   ' + \
                    '\n[WARN]   '.join(exist_audios))
                print('')
                
                def you_want_to_extract_anyway() -> bool:
                    while True:
                        ans = input('Extract anyway ? [yes/NO] >>> ')
                        if ans.lower() in ['', 'n', 'no']:
                            return False
                        elif ans.lower() in ['y', 'yes']:
                            return True
                        else:
                            print('Answer \'yes\' or \'no\'.')
                
                if not you_want_to_extract_anyway():
                    print(f'[INFO] Skipped : {zip_basename}')
                    continue
            
            # extract zip
            print(f'[{zip_basename}]')
            print(f'  Extracting to "{album_dir}" ... ', end='')
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(path=album_dir)
            print('OK')
            
            # move the processed zip file into 'old' directory
            os.makedirs(args.old_dir, exist_ok=True)
            shutil.move(zip_file, args.old_dir)
            
            # extract lyrics and save as text file
            if any_audio_has_lyric(album_dir):
                print(f'  Some lyrics are found.')
                saved_lyric_file = save_lyrics(album_dir)
                print(f'  Extracted lyrics into file:')
                print(f'    {saved_lyric_file}')
    else:
        print('Zip file was not found.')
    
    # process audio files (for single release)
    print('searching audio file...')
    audio_files = get_audio_files(args.search_dir)
    
    if audio_files:
        print(f'{len(audio_files)} audio files was found.')
        for audio_file in audio_files:
            audio_basename = os.path.basename(audio_file)
            artist_name, _ = split_artist_and_album(audio_basename)
            artist_name = replace_unwanted_artist_name(artist_name)
            artist_dir = prepare_sub_directory(args.dst_dir, artist_name)
            print(f'[{audio_basename}]')
            print(f'  Moving to "{artist_dir}" ... ', end='')
            moved_path = shutil.move(audio_file, artist_dir)
            print('OK')

            if audio_has_lyric(moved_path):
                print(f'  Some lyrics are found.')
                saved_lyric_file = save_lyrics(artist_dir)
                print(f'  Extracted lyrics into file:')
                print(f'    {saved_lyric_file}')
    else:
        print('Audio file was not found.')

    print('Done.')
