"""PRG switches for controlling cameras."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PRGBaseEntity
from .const import DOMAIN
from .device import PRGDevice
from .models import Profile


@dataclass(frozen=True, kw_only=True)
class PRGSwitchEntityDescription(SwitchEntityDescription):
    """Describes PRG switch entity."""

    turn_on_fn: Callable[
        [PRGDevice], Callable[[Profile, Any], Coroutine[Any, Any, None]]
    ]
    turn_off_fn: Callable[
        [PRGDevice], Callable[[Profile, Any], Coroutine[Any, Any, None]]
    ]
    turn_on_data: Any
    turn_off_data: Any
    supported_fn: Callable[[PRGDevice], bool]


SWITCHES: tuple[PRGSwitchEntityDescription, ...] = (
    PRGSwitchEntityDescription(
        key="autofocus",
        translation_key="autofocus",
        turn_on_data={"Focus": {"AutoFocusMode": "AUTO"}},
        turn_off_data={"Focus": {"AutoFocusMode": "MANUAL"}},
        turn_on_fn=lambda device: device.async_set_imaging_settings,
        turn_off_fn=lambda device: device.async_set_imaging_settings,
        supported_fn=lambda device: device.capabilities.imaging,
    ),
    PRGSwitchEntityDescription(
        key="ir_lamp",
        translation_key="ir_lamp",
        turn_on_data={"IrCutFilter": "OFF"},
        turn_off_data={"IrCutFilter": "ON"},
        turn_on_fn=lambda device: device.async_set_imaging_settings,
        turn_off_fn=lambda device: device.async_set_imaging_settings,
        supported_fn=lambda device: device.capabilities.imaging,
    ),
    PRGSwitchEntityDescription(
        key="wiper",
        translation_key="wiper",
        turn_on_data="tt:Wiper|On",
        turn_off_data="tt:Wiper|Off",
        turn_on_fn=lambda device: device.async_run_aux_command,
        turn_off_fn=lambda device: device.async_run_aux_command,
        supported_fn=lambda device: device.capabilities.ptz,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a PRG switch platform."""
    device = hass.data[DOMAIN][config_entry.unique_id]

    async_add_entities(
        PRGSwitch(device, description)
        for description in SWITCHES
        if description.supported_fn(device)
    )


class PRGSwitch(PRGBaseEntity, SwitchEntity):
    """An PRG switch."""

    entity_description: PRGSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self, device: PRGDevice, description: PRGSwitchEntityDescription
    ) -> None:
        """Initialize the switch."""
        super().__init__(device)
        self._attr_unique_id = f"{self.mac_or_serial}_{description.key}"
        self.entity_description = description

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on switch."""
        self._attr_is_on = True
        profile = self.device.profiles[0]
        await self.entity_description.turn_on_fn(self.device)(
            profile, self.entity_description.turn_on_data
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off switch."""
        self._attr_is_on = False
        profile = self.device.profiles[0]
        await self.entity_description.turn_off_fn(self.device)(
            profile, self.entity_description.turn_off_data
        )
