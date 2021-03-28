# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from fastapi import FastAPI, status
from httpx import AsyncClient
from tests.utils import asyncio_patch

from gns3server.compute.project import Project

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
async def vm(app: FastAPI, client: AsyncClient, compute_project: Project, ubridge_path: str, on_gns3vm) -> dict:

    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat._start_ubridge"):
        response = await client.post(app.url_path_for("create_nat_node", project_id=compute_project.id),
                                     json={"name": "Nat 1"})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def test_nat_create(app: FastAPI, client: AsyncClient, compute_project: Project, on_gns3vm) -> None:

    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat._start_ubridge"):
        response = await client.post(app.url_path_for("create_nat_node", project_id=compute_project.id),
                                     json={"name": "Nat 1"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Nat 1"
    assert response.json()["project_id"] == compute_project.id


async def test_nat_get(app: FastAPI, client: AsyncClient, compute_project: Project, vm: dict) -> None:

    response = await client.get(app.url_path_for("get_nat_node", project_id=vm["project_id"], node_id=vm["node_id"]))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Nat 1"
    assert response.json()["project_id"] == compute_project.id
    assert response.json()["status"] == "started"


async def test_nat_nio_create_udp(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    params = {
        "type": "nio_udp",
        "lport": 4242,
        "rport": 4343,
        "rhost": "127.0.0.1"
    }

    url = app.url_path_for("create_nat_node_nio",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")

    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.add_nio"):
        response = await client.post(url, json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["type"] == "nio_udp"


async def test_nat_nio_update_udp(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    params = {
        "type": "nio_udp",
        "lport": 4242,
        "rport": 4343,
        "rhost": "127.0.0.1"
    }

    url = app.url_path_for("create_nat_node_nio",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")

    await client.post(url, json=params)
    params["filters"] = {}

    url = app.url_path_for("update_nat_node_nio",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")
    response = await client.put(url, json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["type"] == "nio_udp"


async def test_nat_delete_nio(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    params = {
        "type": "nio_udp",
        "lport": 4242,
        "rport": 4343,
        "rhost": "127.0.0.1"
    }

    url = app.url_path_for("create_nat_node_nio",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")
    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.add_nio"):
        await client.post(url, json=params)

    url = app.url_path_for("delete_nat_node_nio",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")
    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.remove_nio") as mock:
        response = await client.delete(url)
        assert mock.called
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_nat_delete(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    response = await client.delete(app.url_path_for("delete_nat_node",
                                                    project_id=vm["project_id"],
                                                    node_id=vm["node_id"]))

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_nat_update(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    response = await client.put(app.url_path_for("update_nat_node",
                                                 project_id=vm["project_id"],
                                                 node_id=vm["node_id"]), json={"name": "test"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "test"


async def test_nat_start_capture(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    params = {
        "capture_file_name": "test.pcap",
        "data_link_type": "DLT_EN10MB"
    }

    url = app.url_path_for("start_nat_node_capture",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")
    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.start_capture") as mock:
        response = await client.post(url, json=params)
        assert response.status_code == status.HTTP_200_OK
        assert mock.called
        assert "test.pcap" in response.json()["pcap_file_path"]


async def test_nat_stop_capture(app: FastAPI, client: AsyncClient, vm: dict) -> None:

    url = app.url_path_for("stop_nat_node_capture",
                           project_id=vm["project_id"],
                           node_id=vm["node_id"],
                           adapter_number="0",
                           port_number="0")

    with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.stop_capture") as mock:
        response = await client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock.called


# @pytest.mark.asyncio
# async def test_nat_pcap(compute_api, vm, compute_project):
#
#     with asyncio_patch("gns3server.compute.builtin.nodes.nat.Nat.get_nio"):
#         with asyncio_patch("gns3server.compute.builtin.Builtin.stream_pcap_file"):
#             response = await client.get("/projects/{project_id}/nat/nodes/{node_id}/adapters/0/ports/0/pcap".format(project_id=compute_project.id, node_id=vm["node_id"]), raw=True)
#             assert response.status_code == status.HTTP_200_OK