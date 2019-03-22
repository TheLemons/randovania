import dataclasses

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import PickupNode
from randovania.game_description.resources import find_resource_info_with_long_name, PickupIndex, PickupEntry, \
    ConditionalResources
from randovania.layout import game_patches_serializer
from randovania.layout.game_patches_serializer import BitPackPickupEntry
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.major_item_state import MajorItemState
from randovania.resolver.item_pool import pickup_creator


@pytest.fixture(
    params=[
        {},
        {"starting_item": "Morph Ball"},
        {"elevator": [1572998, "Temple Grounds/Transport to Agon Wastes"]},
        {"pickup": ['HUhMANYC', "Screw Attack"]},
    ],
    name="patches_with_data")
def _patches_with_data(request, echoes_game_data, echoes_item_database):
    game = data_reader.decode_data(echoes_game_data)

    data = {
        "starting_location": "Temple Grounds/Landing Site",
        "starting_items": {},
        "elevators": {},
        "locations": {
            world.name: {
                game.world_list.node_name(node): "Nothing"
                for node in world.all_nodes
                if node.is_resource_node and isinstance(node, PickupNode)
            }
            for world in sorted(game.world_list.worlds, key=lambda w: w.name)
        },
        "_locations_internal": "",
    }
    patches = GamePatches.with_game(game)

    if request.param.get("starting_item"):
        item_name = request.param.get("starting_item")
        patches = patches.assign_extra_initial_items([
            (find_resource_info_with_long_name(game.resource_database.item, item_name), 1),
        ])
        data["starting_items"][item_name] = 1

    if request.param.get("elevator"):
        elevator_id, elevator_source = request.param.get("elevator")
        patches = dataclasses.replace(patches, elevator_connection={
            elevator_id: game.starting_location,
        })
        data["elevators"][elevator_source] = "Temple Grounds/Landing Site"

    if request.param.get("pickup"):
        data["_locations_internal"], pickup_name = request.param.get("pickup")
        pickup = pickup_creator.create_major_item(echoes_item_database.major_items[pickup_name],
                                                  MajorItemState(), True, game.resource_database)

        patches = patches.assign_new_pickups([(PickupIndex(5), pickup)])
        data["locations"]["Temple Grounds"]['Transport to Agon Wastes/Pickup (Missile)'] = pickup_name

    return data, patches


def test_encode(patches_with_data, echoes_game_data):
    expected, patches = patches_with_data

    # Run
    encoded = game_patches_serializer.serialize(patches, echoes_game_data)

    # Assert
    for key, value in expected["locations"].items():
        assert encoded["locations"][key] == value
    assert encoded == expected


def test_decode(patches_with_data):
    encoded, expected = patches_with_data

    # Run
    decoded = game_patches_serializer.decode(encoded, LayoutConfiguration.default())

    # Assert
    assert decoded == expected


def test_bit_pack_pickup_entry(echoes_resource_database):
    # Setup
    name = "Some Random Name"
    pickup = PickupEntry(
        name=name,
        model_index=26,
        item_category=ItemCategory.TEMPLE_KEY,
        resources=(
            ConditionalResources(
                "Morph Ball", None,
                (
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"), 2),
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage"), 5),
                ),
            ),
            ConditionalResources(
                "Grapple Beam", find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"),
                (
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Grapple Beam"), 3),
                ),
            )
        )
    )

    # Run
    encoded = bitpacking.pack_value(BitPackPickupEntry(pickup, echoes_resource_database))
    decoder = BitPackDecoder(encoded)
    decoded = BitPackPickupEntry.bit_pack_unpack(decoder, name, echoes_resource_database)

    # Assert
    assert pickup == decoded