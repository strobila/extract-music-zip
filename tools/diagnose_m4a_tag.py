"""
m4aファイルのタグ編集ができない原因を診断するツール
"""

import argparse
import os
import stat
import struct
import sys


# ---------------------------------------------------------------------------
# 診断結果クラス
# ---------------------------------------------------------------------------

class DiagnosticResult:
    OK = 'OK'
    WARN = 'WARN'
    NG = 'NG'
    INFO = 'INFO'

    def __init__(self, status: str, title: str, detail: str):
        self.status = status
        self.title = title
        self.detail = detail

    def __str__(self):
        color_map = {
            self.OK:   '\033[92m',   # 緑
            self.WARN: '\033[93m',   # 黄
            self.NG:   '\033[91m',   # 赤
            self.INFO: '\033[96m',   # シアン
        }
        reset = '\033[0m'
        c = color_map.get(self.status, '')
        label = f'[{self.status:<4}]'
        return f'{c}{label}{reset} {self.title}: {self.detail}'


# ---------------------------------------------------------------------------
# 診断チェック関数
# ---------------------------------------------------------------------------

def check_file_exists(filepath: str) -> DiagnosticResult:
    """ファイルが存在するか確認"""
    if os.path.isfile(filepath):
        size = os.path.getsize(filepath)
        return DiagnosticResult(DiagnosticResult.OK, 'ファイル存在', f'存在する ({size:,} bytes)')
    return DiagnosticResult(DiagnosticResult.NG, 'ファイル存在', 'ファイルが見つからない')


def check_extension(filepath: str) -> DiagnosticResult:
    """拡張子が .m4a であるか確認"""
    _, ext = os.path.splitext(filepath)
    ext_lower = ext.lower()
    if ext_lower == '.m4a':
        return DiagnosticResult(DiagnosticResult.OK, '拡張子', f'正常 ({ext})')
    return DiagnosticResult(
        DiagnosticResult.WARN, '拡張子',
        f'"{ext}" は .m4a ではない。別フォーマットのファイルをリネームした可能性がある'
    )


def check_read_permission(filepath: str) -> DiagnosticResult:
    """読み取り権限があるか確認"""
    if os.access(filepath, os.R_OK):
        return DiagnosticResult(DiagnosticResult.OK, '読み取り権限', 'あり')
    return DiagnosticResult(DiagnosticResult.NG, '読み取り権限', 'なし — os.chmod() で解除が必要')


def check_write_permission(filepath: str) -> DiagnosticResult:
    """書き込み権限があるか確認"""
    if not os.access(filepath, os.W_OK):
        # 読み取り専用フラグを確認
        file_stat = os.stat(filepath)
        readonly = not bool(file_stat.st_mode & stat.S_IWRITE)
        detail = '読み取り専用フラグが立っている' if readonly else '権限なし'
        return DiagnosticResult(DiagnosticResult.NG, '書き込み権限', f'なし — {detail}')
    return DiagnosticResult(DiagnosticResult.OK, '書き込み権限', 'あり')


def check_file_lock(filepath: str) -> DiagnosticResult:
    """ファイルが他プロセスにロックされていないか確認"""
    try:
        with open(filepath, 'ab'):
            pass
        return DiagnosticResult(DiagnosticResult.OK, 'ファイルロック', 'ロックなし（排他書き込み可能）')
    except PermissionError:
        return DiagnosticResult(
            DiagnosticResult.NG, 'ファイルロック',
            '他のプロセス（音楽プレイヤー等）がファイルをロックしている'
        )
    except Exception as e:
        return DiagnosticResult(DiagnosticResult.WARN, 'ファイルロック', f'確認失敗: {e}')


def _read_mp4_atoms(filepath: str) -> list[tuple[int, str, int]]:
    """
    MP4/M4Aファイルのトップレベルアトムを列挙する
    Returns:
        list of (offset, name, size)
    """
    atoms = []
    with open(filepath, 'rb') as f:
        file_size = os.path.getsize(filepath)
        offset = 0
        while offset < file_size:
            f.seek(offset)
            header = f.read(8)
            if len(header) < 8:
                break
            size = struct.unpack('>I', header[:4])[0]
            name = header[4:8].decode('latin-1', errors='replace')
            if size == 1:
                # 64bit拡張サイズ
                ext = f.read(8)
                if len(ext) < 8:
                    break
                size = struct.unpack('>Q', ext)[0]
            elif size == 0:
                # ファイル末尾まで
                size = file_size - offset
            if size < 8:
                break
            atoms.append((offset, name, size))
            offset += size
    return atoms


def check_mp4_atoms(filepath: str) -> list[DiagnosticResult]:
    """MP4アトム構造を確認"""
    results = []
    try:
        atoms = _read_mp4_atoms(filepath)
        names = [name for _, name, _ in atoms]

        # ftyp チェック
        if 'ftyp' in names:
            results.append(DiagnosticResult(DiagnosticResult.OK, 'MP4 ftyp アトム', '存在する（正常な MP4/M4A ファイル形式）'))
        else:
            results.append(DiagnosticResult(DiagnosticResult.WARN, 'MP4 ftyp アトム', 'なし — MP4/M4Aとして認識できない可能性がある'))

        # moov チェック
        if 'moov' not in names:
            results.append(DiagnosticResult(DiagnosticResult.NG, 'MP4 moov アトム', 'なし — ファイルが破損しているか不完全な可能性がある'))
        else:
            moov_offset = next(off for off, n, _ in atoms if n == 'moov')
            mdat_offsets = [off for off, n, _ in atoms if n == 'mdat']
            if mdat_offsets and moov_offset > mdat_offsets[-1]:
                results.append(DiagnosticResult(
                    DiagnosticResult.WARN, 'MP4 moov アトム位置',
                    'moov がファイル末尾にある — ライブラリによってはタグ書き込みに失敗することがある'
                ))
            else:
                results.append(DiagnosticResult(DiagnosticResult.OK, 'MP4 moov アトム', '先頭付近に存在する'))

        # アトム一覧表示
        atom_summary = ', '.join(names[:10]) + ('...' if len(names) > 10 else '')
        results.append(DiagnosticResult(DiagnosticResult.INFO, 'トップレベルアトム', atom_summary))

    except Exception as e:
        results.append(DiagnosticResult(DiagnosticResult.WARN, 'MP4 アトム解析', f'失敗: {e}'))

    return results


def check_drm(filepath: str) -> DiagnosticResult:
    """DRM 保護がかかっていないか確認（drms / sinf アトムの有無）"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        if b'drms' in content or b'sinf' in content:
            return DiagnosticResult(
                DiagnosticResult.NG, 'DRM',
                'DRM 関連アトム (drms/sinf) を検出 — DRM 保護ファイルはタグ編集不可'
            )
        return DiagnosticResult(DiagnosticResult.OK, 'DRM', 'DRM アトムなし')
    except Exception as e:
        return DiagnosticResult(DiagnosticResult.WARN, 'DRM', f'確認失敗: {e}')


def check_tinytag_read(filepath: str) -> DiagnosticResult:
    """tinytag でタグ読み取りができるか確認"""
    try:
        from tinytag import TinyTag
        tag = TinyTag.get(filepath)
        title = tag.title or '(なし)'
        artist = tag.artist or '(なし)'
        return DiagnosticResult(
            DiagnosticResult.OK, 'tinytag 読み取り',
            f'成功 — title="{title}", artist="{artist}"'
        )
    except ImportError:
        return DiagnosticResult(DiagnosticResult.INFO, 'tinytag 読み取り', 'tinytag 未インストール (pip install tinytag)')
    except Exception as e:
        return DiagnosticResult(DiagnosticResult.NG, 'tinytag 読み取り', f'失敗: {e}')


def check_mutagen_available() -> DiagnosticResult:
    """mutagen がインストールされているか確認"""
    try:
        import mutagen  # noqa: F401
        import mutagen.mp4  # noqa: F401
        return DiagnosticResult(DiagnosticResult.OK, 'mutagen インストール', f'あり (version: {mutagen.version_string})')
    except ImportError:
        return DiagnosticResult(
            DiagnosticResult.WARN, 'mutagen インストール',
            'なし — タグ書き込みには mutagen が必要 (pip install mutagen)'
        )


def check_mutagen_read(filepath: str) -> DiagnosticResult:
    """mutagen でタグ読み取りができるか確認"""
    try:
        import mutagen.mp4
        audio = mutagen.mp4.MP4(filepath)
        tags = audio.tags
        if tags is None:
            return DiagnosticResult(
                DiagnosticResult.WARN, 'mutagen 読み取り',
                'タグが存在しない (audio.tags is None) — 書き込み前に audio.add_tags() が必要'
            )
        tag_keys = list(tags.keys())[:5]
        return DiagnosticResult(DiagnosticResult.OK, 'mutagen 読み取り', f'成功 — タグキー: {tag_keys}')
    except ImportError:
        return DiagnosticResult(DiagnosticResult.INFO, 'mutagen 読み取り', 'mutagen 未インストール — スキップ')
    except mutagen.mp4.MP4StreamInfoError as e:
        return DiagnosticResult(DiagnosticResult.NG, 'mutagen 読み取り', f'MP4 構造エラー: {e}')
    except Exception as e:
        return DiagnosticResult(DiagnosticResult.NG, 'mutagen 読み取り', f'失敗: {e}')


def check_mutagen_write(filepath: str, dry_run: bool = True) -> DiagnosticResult:
    """
    mutagen でタグ書き込みができるか確認
    - dry_run=True  : 実ファイルへの保存はスキップ
    - dry_run=False : 元ファイルのコピーに対して save() を実行
    """
    try:
        import shutil
        import mutagen.mp4
        audio = mutagen.mp4.MP4(filepath)
        if audio.tags is None:
            audio.add_tags()

        # タグオブジェクト操作チェック
        audio.tags['\xa9nam'] = audio.tags.get('\xa9nam', ['']) or ['']

        if dry_run:
            return DiagnosticResult(DiagnosticResult.OK, 'mutagen 書き込み', 'タグオブジェクトの操作は成功（dry_run: 実ファイルへの保存はスキップ）')

        # コピー先パスを生成して保存
        stem, ext = os.path.splitext(filepath)
        copy_path = f'{stem}_writetest{ext}'
        shutil.copy2(filepath, copy_path)
        write_value = '__diagnose_write_test__'
        try:
            copy_audio = mutagen.mp4.MP4(copy_path)
            if copy_audio.tags is None:
                copy_audio.add_tags()
            copy_audio.tags['\xa9nam'] = [write_value]
            copy_audio.save()
        except Exception:
            os.remove(copy_path)
            raise

        # 書き込み後に再読み込みして値を検証
        verify_audio = mutagen.mp4.MP4(copy_path)
        read_back = verify_audio.tags.get('\xa9nam', [None])[0] if verify_audio.tags else None
        if read_back != write_value:
            return DiagnosticResult(
                DiagnosticResult.NG, 'mutagen 書き込み検証',
                f'save() は成功したが読み戻し値が一致しない — 書き込み値: "{write_value}", 読み戻し値: "{read_back}" (コピー先: {copy_path})'
            )
        return DiagnosticResult(
            DiagnosticResult.OK, 'mutagen 書き込み',
            f'save() 成功・読み戻し検証 OK — コピー先: {copy_path}'
        )

    except ImportError:
        return DiagnosticResult(DiagnosticResult.INFO, 'mutagen 書き込み', 'mutagen 未インストール — スキップ')
    except PermissionError as e:
        return DiagnosticResult(DiagnosticResult.NG, 'mutagen 書き込み', f'書き込み権限エラー: {e}')
    except Exception as e:
        return DiagnosticResult(DiagnosticResult.NG, 'mutagen 書き込み', f'失敗: {e}')


# ---------------------------------------------------------------------------
# メイン診断処理
# ---------------------------------------------------------------------------

def diagnose(filepath: str, write_test: bool = False):
    """
    m4aファイルのタグ編集ができない原因を診断する
    Parameters:
        filepath (str): 診断対象のファイルパス
        write_test (bool): True の場合、元ファイルのコピー (<stem>_writetest.m4a) に対して
                           実際に save() を実行して書き込みテストを行う
    """
    print(f'\n診断対象: {filepath}')
    print('=' * 80)

    results: list[DiagnosticResult] = []

    # --- ファイル基本チェック ---
    exists_result = check_file_exists(filepath)
    results.append(exists_result)
    if exists_result.status == DiagnosticResult.NG:
        _print_results(results)
        return

    results.append(check_extension(filepath))
    results.append(check_read_permission(filepath))
    results.append(check_write_permission(filepath))
    results.append(check_file_lock(filepath))

    # --- ファイル構造チェック ---
    print()
    results += check_mp4_atoms(filepath)
    results.append(check_drm(filepath))

    # --- ライブラリチェック ---
    print()
    results.append(check_tinytag_read(filepath))
    results.append(check_mutagen_available())
    results.append(check_mutagen_read(filepath))
    results.append(check_mutagen_write(filepath, dry_run=(not write_test)))

    print()
    _print_results(results)
    _print_summary(results)


def _print_results(results: list[DiagnosticResult]):
    for r in results:
        print(r)


def _print_summary(results: list[DiagnosticResult]):
    print()
    print('=' * 80)
    ng_list = [r for r in results if r.status == DiagnosticResult.NG]
    warn_list = [r for r in results if r.status == DiagnosticResult.WARN]

    if not ng_list and not warn_list:
        print('\033[92m[問題なし] タグ編集を妨げる問題は検出されませんでした。\033[0m')
        return

    if ng_list:
        print('\033[91m[NG 項目] タグ編集ができない原因として以下が考えられます:\033[0m')
        for r in ng_list:
            print(f'  - {r.title}: {r.detail}')

    if warn_list:
        print('\033[93m[警告項目] 以下の点に注意してください:\033[0m')
        for r in warn_list:
            print(f'  - {r.title}: {r.detail}')


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='m4aファイルのタグ編集ができない原因を診断するツール'
    )
    parser.add_argument('filepath', help='診断するm4aファイルのパス')
    parser.add_argument(
        '--write-test',
        action='store_true',
        default=False,
        help='元ファイルのコピー (<stem>_writetest.m4a) に対して実際に書き込みテストを行う（デフォルト: dry-run）'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if not sys.stdout.isatty():
        # リダイレクト時はANSIカラーを無効化
        import re
        original_str = DiagnosticResult.__str__

        def plain_str(self):
            return re.sub(r'\033\[[0-9;]*m', '', original_str(self))

        DiagnosticResult.__str__ = plain_str

    diagnose(args.filepath, write_test=args.write_test)
