"""
Insightron Core Module

Provides foundational components:
- Configuration (TOML-based, O(1) lookup)
- Resource Pool (ML workload management)
- Message Bus (inter-component communication)
"""

from insightron.core.config import (
    ConfigManager,
    get_config_manager,
    get_config,
    get_all_config,
)
from insightron.core.resources import (
    ResourcePool,
    get_resource_pool,
    WorkloadType,
    QuotaInfo,
)
from insightron.core.bus import (
    MessageBus,
    get_message_bus,
    EventType,
    Event,
    emit,
    on,
)

__all__ = [
    # Config
    "ConfigManager",
    "get_config_manager",
    "get_config",
    "get_all_config",
    # Resources
    "ResourcePool",
    "get_resource_pool",
    "WorkloadType",
    "QuotaInfo",
    # Bus
    "MessageBus",
    "get_message_bus",
    "EventType",
    "Event",
    "emit",
    "on",
]
