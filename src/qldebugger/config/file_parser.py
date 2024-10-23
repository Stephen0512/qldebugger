from abc import ABC, abstractmethod
from typing import Any, BinaryIO, NamedTuple, Optional, Union

import tomli
from pydantic import BaseModel, Field, PositiveInt, field_validator


class ConfigAWS(BaseModel):
    profile: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: Optional[str] = None
    endpoint_url: Optional[str] = None


class ConfigSecret(BaseModel, ABC):
    @abstractmethod
    def get_value(self) -> Union[str, bytes]:
        raise NotImplementedError


class ConfigSecretString(ConfigSecret):
    string: str

    def get_value(self) -> str:
        return self.string


class ConfigSecretBinary(ConfigSecret):
    binary: bytes

    def get_value(self) -> bytes:
        return self.binary


class ConfigTopicSubscriber(BaseModel):
    queue: str
    raw_message_delivery: bool = False
    filter_policy: Optional[str] = None


class ConfigTopic(BaseModel):
    subscribers: list[ConfigTopicSubscriber] = Field(default_factory=list)


class ConfigQueueRedrivePolicy(BaseModel):
    dead_letter_queue: str
    max_receive_count: PositiveInt


class ConfigQueue(BaseModel):
    redrive_policy: Optional[ConfigQueueRedrivePolicy] = None


class NameHandlerTuple(NamedTuple):
    module: str
    function: str


class ConfigLambda(BaseModel):
    handler: NameHandlerTuple
    environment: dict[str, str] = Field(default_factory=dict)

    @field_validator('handler', mode='before')
    @classmethod
    def _split_handler(cls, v: Any) -> tuple[str, str]:
        if not isinstance(v, str):
            raise ValueError('should be a str')
        if '.' not in v:
            raise ValueError('should have a module and function names')
        module, function = v.rsplit('.', maxsplit=1)
        return module, function


class ConfigEventSourceMapping(BaseModel):
    queue: str
    batch_size: int = 10
    maximum_batching_window: int = 0
    function_name: str


class Config(BaseModel):
    aws: ConfigAWS = Field(default_factory=ConfigAWS)
    secrets: dict[str, Union[ConfigSecretString, ConfigSecretBinary]] = Field(default_factory=dict)
    topics: dict[str, ConfigTopic] = Field(default_factory=dict)
    queues: dict[str, ConfigQueue]
    lambdas: dict[str, ConfigLambda]
    event_source_mapping: dict[str, ConfigEventSourceMapping]

    @classmethod
    def from_toml(cls, fp: BinaryIO, /) -> 'Config':
        return cls.model_validate(tomli.load(fp))
