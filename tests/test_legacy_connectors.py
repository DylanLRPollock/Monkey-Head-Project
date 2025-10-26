# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Legacy Connectors module (tests)

import asyncio

import pytest

from monkey_head.legacy.connectors import (
    EmulatedLegacyConnector,
    LegacyConnectorFactory,
    SerialLegacyConnector,
)


@pytest.mark.asyncio
async def test_emulated_connector_buffers_messages():
    connector = EmulatedLegacyConnector()
    await connector.connect()
    await connector.send(b'LOAD"*",8,1')
    queued = await connector.command_channel.get()
    assert queued.startswith(b"LOAD")

    async def respond():
        await connector.inject_emulator_response(b"READY")

    asyncio.create_task(respond())
    payload = await connector.receive()
    assert payload == b"READY"
    await connector.close()


@pytest.mark.asyncio
async def test_serial_connector_requires_pyserial(monkeypatch):
    monkeypatch.setattr("monkey_head.legacy.connectors.serial", None)
    connector = SerialLegacyConnector(port="/dev/ttyUSB0")
    with pytest.raises(RuntimeError):
        await connector.connect()


def test_legacy_connector_factory_defaults_to_emulated():
    connector = LegacyConnectorFactory.create({})
    assert isinstance(connector, EmulatedLegacyConnector)

    config = {"mode": "serial", "port": "/dev/ttyUSB0"}
    # When serial support is unavailable the connector still instantiates
    instance = LegacyConnectorFactory.create(config)
    assert isinstance(instance, SerialLegacyConnector)
