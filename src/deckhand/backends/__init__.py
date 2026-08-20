"""DeckHand 后端注册与分发。"""

from deckhand.backends.release_please import ReleasePleaseBackend

# 后端注册表，以后加新的 backend 就在这里加一行
_BACKENDS: dict[str, type] = {
    "release-please": ReleasePleaseBackend,
}


def list_backends() -> list[str]:
    """列出所有可用的后端名称。"""
    return list(_BACKENDS.keys())


def get_backend(name: str) -> "Backend":
    """根据名称获取后端实例。"""
    if name not in _BACKENDS:
        available = ", ".join(list_backends())
        raise ValueError(f"未知后端: {name}，可选: {available}")
    return _BACKENDS[name]()
