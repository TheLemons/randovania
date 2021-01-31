import pytest

import randovania.generator.item_pool.ammo
import randovania.generator.item_pool.pickup_creator
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry, \
    ResourceLock
from randovania.layout.major_item_state import MajorItemState


@pytest.mark.parametrize("percentage", [False, True])
@pytest.mark.parametrize("has_convert", [False, True])
def test_create_pickup_for(percentage: bool, has_convert: bool, echoes_resource_database):
    # Setup
    item_a = echoes_resource_database.get_item(10)
    item_b = echoes_resource_database.get_item(15)
    item_c = echoes_resource_database.get_item(18)
    ammo_a = echoes_resource_database.get_item(40)
    ammo_b = echoes_resource_database.get_item(42)
    temporary_a = echoes_resource_database.get_item(71)
    temporary_b = echoes_resource_database.get_item(72)

    major_item = MajorItem(
        name="The Item",
        item_category=ItemCategory.MORPH_BALL,
        broad_category=ItemCategory.MORPH_BALL_RELATED,
        model_index=1337,
        progression=(10, 15, 18),
        ammo_index=(40, 42),
        converts_indices=(71, 72) if has_convert else (),
        required=False,
        original_index=None,
        probability_offset=5,
    )
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(10, 20),
    )

    if percentage:
        extra_resources = (
            (ammo_a, 10),
            (ammo_b, 20),
            (echoes_resource_database.item_percentage, 1),
        )
    else:
        extra_resources = (
            (ammo_a, 10),
            (ammo_b, 20),
        )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(major_item, state, percentage,
                                                                             echoes_resource_database,
                                                                             None, False)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model_index=1337,
        progression=(
            (item_a, 1),
            (item_b, 1),
            (item_c, 1),
        ),
        extra_resources=extra_resources,
        convert_resources=(
            ResourceConversion(source=temporary_a, target=ammo_a),
            ResourceConversion(source=temporary_b, target=ammo_b),
        ) if has_convert else (),
        item_category=ItemCategory.MORPH_BALL,
        broad_category=ItemCategory.MORPH_BALL_RELATED,
        probability_offset=5,
        respects_lock=False,
    )


@pytest.mark.parametrize(["ammo_quantity"], [
    (0,),
    (10,),
    (15,),
])
def test_create_missile_launcher(ammo_quantity: int, echoes_item_database, echoes_resource_database):
    # Setup
    missile = echoes_resource_database.get_item(44)
    missile_launcher = echoes_resource_database.get_item(73)
    temporary = echoes_resource_database.get_item(71)

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(
        echoes_item_database.major_items["Missile Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        True
    )

    # Assert
    assert result == PickupEntry(
        name="Missile Launcher",
        progression=(
            (missile_launcher, 1),
        ),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.item_percentage, 1),
        ),
        convert_resources=(
            ResourceConversion(source=temporary, target=missile),
        ),
        model_index=24,
        item_category=ItemCategory.MISSILE,
        broad_category=ItemCategory.MISSILE_RELATED,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        )
    )


@pytest.mark.parametrize("ammo_quantity", [0, 10, 15])
@pytest.mark.parametrize("ammo_requires_major_item", [False, True])
def test_create_seeker_launcher(ammo_quantity: int,
                                ammo_requires_major_item: bool,
                                echoes_item_database,
                                echoes_resource_database,
                                ):
    # Setup
    missile = echoes_resource_database.get_item(44)
    missile_launcher = echoes_resource_database.get_item(73)
    seeker_launcher = echoes_resource_database.get_item(26)
    temporary = echoes_resource_database.get_item(71)

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(
        echoes_item_database.major_items["Seeker Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        ammo_requires_major_item
    )

    # Assert

    assert result == PickupEntry(
        name="Seeker Launcher",
        progression=(
            (seeker_launcher, 1),
        ),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.item_percentage, 1),
        ),
        model_index=25,
        item_category=ItemCategory.MISSILE,
        broad_category=ItemCategory.MISSILE_RELATED,
        respects_lock=ammo_requires_major_item,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
    )


@pytest.mark.parametrize("requires_major_item", [False, True])
def test_create_ammo_expansion(requires_major_item: bool, echoes_resource_database):
    # Setup
    primary_a = echoes_resource_database.get_item(73)
    ammo_a = echoes_resource_database.get_item(40)
    temporary_a = echoes_resource_database.get_item(71)

    ammo = Ammo(
        name="The Item",
        maximum=100,
        items=(40,),
        broad_category=ItemCategory.ETM,
        unlocked_by=73,
        temporary=71,
        models=(10, 20),
    )
    ammo_count = [75, 150]

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_ammo_expansion(
        ammo, ammo_count, requires_major_item, echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model_index=10,
        progression=tuple(),
        extra_resources=(
            (ammo_a, ammo_count[0]),
            (echoes_resource_database.item_percentage, 1),
        ),
        item_category=ItemCategory.EXPANSION,
        broad_category=ItemCategory.ETM,
        probability_offset=0,
        respects_lock=requires_major_item,
        resource_lock=ResourceLock(
            locked_by=primary_a,
            temporary_item=temporary_a,
            item_to_lock=ammo_a,
        ),
    )
