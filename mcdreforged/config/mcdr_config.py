"""
MCDR config file stuffs
"""
from typing import Any, Dict, Union, Optional, List, Annotated

from pydantic import BaseModel, Field, ConfigDict, Tag

from mcdreforged.constants import core_constant
from mcdreforged.constants.environment_variables import ENV_DISABLE_TELEMETRY
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.utils.pydantic_utils import key_discriminator

CONFIG_SCHEMA_VERSION = 1


class RconConfig(BaseModel):
	enable: bool = False
	address: Optional[str] = '127.0.0.1'
	port: Optional[int] = 25575
	password: Optional[str] = 'password'


class CustomHandlerExtendEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	name: str
	extends: str
	overrides: Dict[str, Any]


class CustomHandlerDefineEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	name: str
	spec: Dict[str, Any]


class CustomHandlerFileEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	file: str


CustomHandlerEntry = Annotated[
	Annotated[CustomHandlerExtendEntry, Tag('extend')] | Annotated[CustomHandlerDefineEntry, Tag('define')] | Annotated[CustomHandlerFileEntry, Tag('file')],
	key_discriminator({'extends': 'extend', 'spec': 'define', 'file': 'file'}),
]


class MCDReforgedConfig(BaseModel):
	model_config = ConfigDict(
		json_schema_extra={
			'$id': f'https://json.schemastore.org/mcdreforged-config.json',
			'$schema': 'http://json-schema.org/draft-07/schema#'
		},
	)

	# --------- Basic Configuration ---------
	language: str = core_constant.DEFAULT_LANGUAGE

	# --------- Server Configuration ---------
	working_directory: str = 'server'
	start_command: Union[str, List[str]] = 'echo Hello world from MCDReforged'
	handler: str = 'vanilla_handler'
	encoding: Optional[str] = 'utf8'
	decoding: Optional[Union[str, List[str]]] = 'utf8'
	environment: Optional[Union[List[str], Dict[str, str]]] = None
	environment_inherit: bool = True
	rcon: RconConfig = Field(default_factory=RconConfig)

	# --------- Plugin Configuration ---------
	plugin_directories: List[str] = Field(default_factory=lambda: ['plugins'])
	catalogue_meta_cache_ttl: int = 20 * 60  # 20min
	catalogue_meta_fetch_timeout: float = 15
	catalogue_meta_url: Optional[str] = None
	plugin_download_url: Optional[str] = None
	plugin_download_timeout: float = 15
	plugin_pip_install_extra_args: Optional[str] = None

	# --------- Misc Configuration ---------
	check_update: bool = True
	advanced_console: bool = True
	http_proxy: Optional[str] = None
	https_proxy: Optional[str] = None
	telemetry: bool = ENV_DISABLE_TELEMETRY.is_not_true()

	# --------- Advanced Configuration ---------
	disable_console_thread: bool = False
	disable_console_color: bool = False
	custom_handlers: Optional[List[Union[str, CustomHandlerEntry]]] = None
	custom_info_reactors: Optional[List[str]] = None
	watchdog_threshold: int = 10
	handler_detection: bool = True

	# --------- Debug Configuration ---------
	debug: Dict[str, bool] = Field(default_factory=lambda: {str(o.name).lower(): False for o in DebugOption})
	write_server_output_to_log_file: bool = False

	def is_debug_on(self) -> bool:
		return any(self.debug.values())
