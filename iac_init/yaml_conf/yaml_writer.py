# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import json
import os
import pathlib
import shutil

from . import yaml
from loguru import logger
from typing import Any, Dict, List
from jinja2 import ChainableUndefined, Environment, FileSystemLoader  # type: ignore
from iac_init.conf import settings

logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-main.log'), format="{time} {level} {message}", level="INFO")

class YamlWriter:
    def __init__(
        self,
        data_paths: List[str],
    ) -> None:
        logger.info("Loading yaml files from {}".format(data_paths[0]))
        self.data = yaml.load_yaml_files(data_paths)
        self.filters: Dict[str, Any] = {}

    def render_template(
        self, template_path: str, output_path: str, env: Environment, **kwargs: Any
    ) -> None:
        """Render single robot jinja template"""
        logger.info("Render ansible playbook template: {}".format(template_path))
        # create output directory if it does not exist yet
        pathlib.Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

        template = env.get_template(template_path)
        # hack to convert nested ordereddict to dict, to avoid duplicate dict keys, e.g. 'tag'
        # json roundtrip should be safe as everything should be serializable
        data = json.loads(json.dumps(self.data))
        result = template.render(data, **kwargs)

        # remove extra empty lines
        lines = result.splitlines()
        cleaned_lines = []
        for index, line in enumerate(lines):
            if len(line.strip()):
                cleaned_lines.append(line)
            else:
                if index + 1 < len(lines):
                    next_line = lines[index + 1]
                    if len(next_line) and not next_line[0].isspace():
                        cleaned_lines.append(line)
        result = os.linesep.join(cleaned_lines)

        with open(output_path.replace('.j2', ''), "w") as file:
            file.write(result)

    def _fix_duplicate_path(self, *paths: str) -> str:
        """Helper function to detect existing paths with non-matching case. Returns a unique path to work with case-insensitve filesystems."""
        directory = os.path.join(*paths[:-1])
        if os.path.exists(directory):
            entries = os.listdir(directory)
            lower_case_entries = [path.lower() for path in entries]
            if paths[-1].lower() in lower_case_entries and paths[-1] not in entries:
                return os.path.join(*paths[:-1], "_" + paths[-1])
        return os.path.join(*paths)

    def write(self, templates_path: str, output_path: str) -> None:
        env = Environment(
            loader=FileSystemLoader(templates_path),
            undefined=ChainableUndefined,
            lstrip_blocks=True,
            trim_blocks=True,
        )

        for dir, _, files in os.walk(templates_path):
            if files:
                try:
                    for filename in files:
                        if (
                                ".j2" not in filename
                        ):
                            logger.info(
                                "Skip file with unknown file extension (not.j2): {}".format(os.path.join(dir, filename))
                            )
                            out = os.path.join(
                                output_path, os.path.basename(templates_path), os.path.relpath(dir, templates_path)
                            )
                            pathlib.Path(out).mkdir(parents=True, exist_ok=True)
                            shutil.copy(os.path.join(dir, filename), out)
                            continue

                        rel = os.path.relpath(dir, templates_path)
                        t_path = os.path.join(rel, filename)
                        t_path = t_path.replace("\\", "/")
                        o_dir = self._fix_duplicate_path(
                            output_path, os.path.basename(templates_path), rel
                        )

                        self.o_path = os.path.join(o_dir, filename)
                        self.render_template(t_path, self.o_path, env)
                        logger.info("Generate working file success: {}".format(self.o_path))
                except Exception as e:
                    logger.error("Generate working file failed: {}".format(self.o_path))
                    logger.error("Error: {}".format(e))
                    exit()
            else:
                try:
                    rel = os.path.relpath(dir, templates_path)
                    rel = rel.replace("\\", "/")
                    self.o_dir = self._fix_duplicate_path(
                        output_path, os.path.basename(templates_path), rel
                    )
                    pathlib.Path(self.o_dir).mkdir(parents=True, exist_ok=True)
                    logger.info("Generate working directory success: {}".format(self.o_dir))
                except Exception as e:
                    logger.error("Generate working directory failed: {}".format(self.o_dir))
                    logger.error("Error: {}".format(e))
                    exit()
