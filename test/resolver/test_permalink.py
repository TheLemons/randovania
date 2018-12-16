import pytest

from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink


def test_encode():
    # Setup
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=LayoutConfiguration.default(),
    )

    # Run
    encoded = link.as_str

    # Assert
    assert encoded == "AAAAfRxALWmCI50gIQDy"


@pytest.mark.parametrize("invalid", [
    "",
    "a",
    "x",
    "zz",
    "AAAAfRxALWmCI50gIQD",
    "AAAAfRxALxmCI50gIQDy"
])
def test_decode_invalid(invalid: str):
    with pytest.raises(ValueError):
        Permalink.from_str(invalid)


@pytest.mark.parametrize("spoiler", [False, True])
@pytest.mark.parametrize("patcher", [
    PatcherConfiguration.default(),
    PatcherConfiguration(
        disable_hud_popup=False,
        menu_mod=True,
    ),
])
@pytest.mark.parametrize("layout", [
    LayoutConfiguration.default(),
    LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel.HARD,
        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
        item_loss=LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.RANDOMIZED,
        pickup_quantities={
            "Missile Expansion": 10,
            "Light Suit": 9,
        },
    ),
])
def test_round_trip(spoiler: bool,
                    patcher: PatcherConfiguration,
                    layout: LayoutConfiguration):
    # Setup
    link = Permalink(
        seed_number=1000,
        spoiler=spoiler,
        patcher_configuration=patcher,
        layout_configuration=layout,
    )

    # Run
    after = Permalink.from_str(link.as_str)

    # Assert
    assert link == after


def test_decode_v0():
    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "AAAAfR5QLERzIpgS4ICCAHw="
    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration(
            disable_hud_popup=True,
            menu_mod=True,
        ),
        layout_configuration=LayoutConfiguration.from_params(
            trick_level=LayoutTrickLevel.HARD,
            sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
            item_loss=LayoutEnabledFlag.ENABLED,
            elevators=LayoutRandomizedFlag.RANDOMIZED,
            pickup_quantities={
                "Missile Expansion": 10,
                "Light Suit": 9,
            },
        ),
    )

    # Run
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected
