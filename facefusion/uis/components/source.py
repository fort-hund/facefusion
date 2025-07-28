from typing import List, Optional, Tuple

import gradio
import os

from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.filesystem import filter_audio_paths, filter_image_paths, has_audio, has_image
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import File

SOURCE_FILE : Optional[gradio.File] = None
SOURCE_AUDIO : Optional[gradio.Audio] = None
SOURCE_IMAGE : Optional[gradio.Image] = None
SOURCE_IMAGES_CATEGORIZED : List[gradio.Dropdown] = []


def render() -> None:
	global SOURCE_FILE
	global SOURCE_AUDIO
	global SOURCE_IMAGE
	global SOURCE_IMAGES_CATEGORIZED

	has_source_audio = has_audio(state_manager.get_item('source_paths'))
	has_source_image = has_image(state_manager.get_item('source_paths'))
	SOURCE_FILE = gradio.File(
		label = wording.get('uis.source_file'),
		file_count = 'multiple',
		file_types =
		[
			'audio',
			'image'
		],
		value = state_manager.get_item('source_paths') if has_source_audio or has_source_image else None
	)
	source_file_names = [ source_file_value.get('path') for source_file_value in SOURCE_FILE.value ] if SOURCE_FILE.value else None
	source_audio_path = get_first(filter_audio_paths(source_file_names))
	source_image_path = get_first(filter_image_paths(source_file_names))
	SOURCE_AUDIO = gradio.Audio(
		value = source_audio_path if has_source_audio else None,
		visible = has_source_audio,
		show_label = False
	)
	SOURCE_IMAGE = gradio.Image(
		value = source_image_path if has_source_image else None,
		visible = has_source_image,
		show_label = False,
  	elem_id = "forThundSourceImage"
	)
 
	base_files_dir = "/workspace/base"
	base_file_names = os.listdir(base_files_dir)
	base_file_name_category_to_pair_map = {}
	for base_file_name in base_file_names:
		base_file_name_tokenized = base_file_name.split("_")
		base_file_name_category = base_file_name_tokenized[0]
		file_name_trimmed = "_".join(base_file_name_tokenized[1:])
		base_file_name_path_pairs = base_file_name_category_to_pair_map.get(base_file_name_category, [])
		base_file_name_path_pairs.append((file_name_trimmed, f"{base_files_dir}/{base_file_name}"))
		base_file_name_category_to_pair_map[base_file_name_category] = base_file_name_path_pairs
    
	for k, v in sorted(base_file_name_category_to_pair_map.items()):
		img = gradio.Dropdown(
      value = None,
      choices = sorted(v, key= lambda x: x[0].lower()),
      visible = True,
      label = f"{k}",
      show_label = True,
      interactive = True
    )
		SOURCE_IMAGES_CATEGORIZED.append(img)
		register_ui_component(f'source_images_{k}', img)
    
	register_ui_component('source_audio', SOURCE_AUDIO)
	register_ui_component('source_image', SOURCE_IMAGE)


def listen() -> None:
	SOURCE_FILE.change(update, inputs = SOURCE_FILE, outputs = [ SOURCE_AUDIO, SOURCE_IMAGE ])
	for x in SOURCE_IMAGES_CATEGORIZED:
		x.change(on_dropdown_change, inputs = x, outputs = [ SOURCE_AUDIO, SOURCE_IMAGE])


def on_dropdown_change(file_name: File) -> Tuple[gradio.Audio, gradio.Image]:
  return update([file_name])


def update(files : List[File]) -> Tuple[gradio.Audio, gradio.Image]:
	file_names = [ file.name if (file and "name" in file) else file for file in files ] if files else None
	has_source_audio = has_audio(file_names)
	has_source_image = has_image(file_names)
	if has_source_audio or has_source_image:
		source_audio_path = get_first(filter_audio_paths(file_names))
		source_image_path = get_first(filter_image_paths(file_names))
		state_manager.set_item('source_paths', file_names)
		return gradio.Audio(value = source_audio_path, visible = has_source_audio), gradio.Image(value = source_image_path, visible = has_source_image)
	state_manager.clear_item('source_paths')
	return gradio.Audio(value = None, visible = False), gradio.Image(value = None, visible = False)
