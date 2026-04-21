# -*- coding: utf-8 -*-
"""
WeChat directory finder - auto-detect latest order files
Inspired by Claude Code architecture - focused module
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from src.utils.helpers import get_path_mtime, get_path_key


def get_month_folder_names(target_date: Optional[datetime] = None) -> List[str]:
    target = target_date or datetime.now()
    return [
        f"{target.year}年{target.month}月",
        f"{target.year}-{target.month:02d}",
        f"{target.year}-{target.month}",
    ]


def find_wechat_search_dirs(wechat_root: str) -> List[Path]:
    search_root = Path(wechat_root).expanduser()
    if not search_root.is_dir():
        return []

    month_names = set(get_month_folder_names())
    candidates: Dict[str, Path] = {}

    def add_candidate(path: Path) -> None:
        if not path.is_dir():
            return
        candidates[get_path_key(path)] = path

    if search_root.name in month_names:
        add_candidate(search_root)

    try:
        if any(search_root.glob("*.xlsx")):
            add_candidate(search_root)
    except OSError:
        return sorted(candidates.values(), key=get_path_mtime, reverse=True)

    for name in month_names:
        add_candidate(search_root / name)
        add_candidate(search_root / "msg" / "file" / name)

    try:
        for child in search_root.iterdir():
            if not child.is_dir():
                continue
            for name in month_names:
                add_candidate(child / name)
                add_candidate(child / "msg" / "file" / name)
    except OSError:
        pass

    return sorted(candidates.values(), key=get_path_mtime, reverse=True)


def resolve_wechat_search_dir(wechat_root: str) -> Optional[Path]:
    candidates = find_wechat_search_dirs(wechat_root)
    return candidates[0] if candidates else None


def auto_detect_wechat_dirs() -> List[Path]:
    from src.utils.helpers import get_path_key
    common_roots: List[Path] = []
    env_root = Path.home() / "Documents" / "WeChat Files"
    env_root2 = Path.home() / "WeChat Files"

    for root in [
        Path("D:/xwechat_files"),
        Path("E:/xwechat_files"),
        Path("C:/xwechat_files"),
        env_root,
        env_root2,
    ]:
        common_roots.append(root)

    candidates: Dict[str, Path] = {}
    checked: set[str] = set()
    for root in common_roots:
        normalized_root = get_path_key(root.expanduser())
        if normalized_root in checked:
            continue
        checked.add(normalized_root)
        if not root.is_dir():
            continue
        for detected in find_wechat_search_dirs(str(root)):
            candidates[get_path_key(detected)] = detected

    return sorted(candidates.values(), key=get_path_mtime, reverse=True)
