"""19.02.2026
Types communs. 
"""

from typing import Any, IO, TypeVar, Iterator, Callable, Self
from corflow.Transcription import Transcription, Tier, Segment

type Path = str
type IterPath = tuple[str, str, str, Path]
'''filename_no_ext, extension, filename_with_ext, path'''
type IterCorp = tuple[str, str, str, str, Path] # same preceded by 'corpus'
type PathDict = dict[str, Path] # key, path
type GDict = dict[str, str|list|dict]

type PathList = list[Path | list[Path] | tuple[Path]]
type MajData = dict    # json output
type MajGUI = Any      # GUI interface
type MPOutput = list[Any]