import argparse
import logging
import struct
import zlib

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from PRP import PRPReader, PRPInstruction, PRPOpCode
from GMS import GeomBase, GeomStat, GeomStats, GeomHeader, GeomTable, GameScene, SceneCompiler


class ToolMode(Enum):
    Compile = 'compile'
    Decompile = 'decompile'

    def __str__(self):
        return self.value


def cli_decompile(gms_path: str, buf_path: str, prp_path: str, tdb_path: str, scene_file: str):
    scene: GameScene = GameScene(gms_path, buf_path, prp_path, tdb_path)
    if not scene.prepare():
        raise RuntimeError(f"Failed to decompile G1 scene {gms_path}")

    scene.dump(scene_file)


def cli_compile(json_scene_path: str, out_prp_file_path: str, tdb_file: str):
    import json

    with open(json_scene_path, "r") as scene_file:
        scene_tree = json.load(scene_file)
        scene_compiler: SceneCompiler = SceneCompiler(scene_tree, tdb_file)
        if scene_compiler.compile(out_prp_file_path):
            print(f"Compile finished. PRP file: {out_prp_file_path}")
        else:
            print(f"Failed to compile scene {json_scene_path} to PRP file {out_prp_file_path}. See log for details")


def cli_main():
    cli_parser = argparse.ArgumentParser(description='Compiler or decompile GMS file format from Glacier 1 engine')
    cli_parser.add_argument('--gms',      help='Path to GMS file', nargs='?', default=None)
    cli_parser.add_argument('--buf',      help='Path to BUF file', nargs='?', default=None)
    cli_parser.add_argument('--prp',      help='Path to PRP file (compile - destination file, decompile - source file)',
                                          nargs='?', default=None)
    cli_parser.add_argument('--tdb',      help='Path to TypesRegistry.json file')
    cli_parser.add_argument('--json',     help='Path to decompiled scene as JSON (decompile); '
                                               'Path to source scene to compile (compile)', nargs='?', default=None)
    cli_parser.add_argument('mode', help='What shall we do?', type=ToolMode, choices=list(ToolMode))
    cli_args = cli_parser.parse_args()

    cli_mode: ToolMode = cli_args.mode

    if cli_mode == ToolMode.Decompile:
        scene_file: str = cli_args.json
        gms_path: Optional[str] = cli_args.gms
        buf_path: Optional[str] = cli_args.buf
        prp_path: Optional[str] = cli_args.prp
        tdb_path: Optional[str] = cli_args.tdb

        if gms_path is None:
            print("For 'decompile' operation '--gms' option is required")
            return

        if buf_path is None:
            print("For 'decompile' operation '--buf' option is required")
            return

        if prp_path is None:
            print("For 'decompile' operation '--prp' option is required")
            return

        if tdb_path is None:
            print("For 'decompile' operation '--tdb' option is required")
            return

        if scene_file is None:
            print("For 'decompile' option '--json' option is required")
            return

        cli_decompile(gms_path, buf_path, prp_path, tdb_path, scene_file)
    else:
        scene_file: Optional[str] = cli_args.json
        prp_file: Optional[str] = cli_args.prp
        tdb_file: Optional[str] = cli_args.tdb

        if scene_file is None:
            print("For 'compile' option '--json' option is required!")
            return

        if prp_file is None:
            print("For 'compile' option '--prp' option is required!")
            return

        if tdb_file is None:
            print("For 'compile' option '--tdb' option is required!")
            return

        cli_compile(scene_file, prp_file, tdb_file)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    cli_main()
