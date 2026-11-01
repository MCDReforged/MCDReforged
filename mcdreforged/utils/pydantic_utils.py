from typing import Dict, Any, Optional

from pydantic import Discriminator


def key_discriminator(key_to_tag: Dict[str, str]) -> Discriminator:
	"""
	Create a discriminator that selects the tag of the first key present in the input value.
	If none of the keys is present, validation fails with a "union_key_not_found" error
	"""
	def func(value: Any) -> Optional[str]:
		for key, tag in key_to_tag.items():
			if (isinstance(value, dict) and key in value) or (not isinstance(value, dict) and hasattr(value, key)):
				return tag
		return None

	return Discriminator(
		func,
		custom_error_type='union_key_not_found',
		custom_error_message='Input should be a mapping containing one of the keys: {keys}',
		custom_error_context={'keys': ', '.join(map(repr, key_to_tag.keys()))},
	)
