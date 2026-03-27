"""19.02.2026
Types communs. 
"""

from typing import Any, IO, TypeVar, Iterator, Callable, Self
from collections.abc import Sequence, MutableSequence
from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from corflow.Transcription import Transcription, Tier, Segment

type Path = str
type IterPath = tuple[str, str, str, Path]
'''filename_no_ext, extension, filename_with_ext, path'''
type IterCorp = tuple[str, str, str, str, Path] # same preceded by 'corpus'
type PathDict = dict[str, Path] # key, path
type GDict = dict[str, str|list|dict]

type Row = Sequence[Cell]

type PathList = list[Path | list[Path] | tuple[Path]]
type MajData = dict    # json output
type MajGUI = Any      # GUI interface
type MPOutput = list[Any]
type MPList = MutableSequence