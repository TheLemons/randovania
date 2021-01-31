from dataclasses import dataclass
from typing import Optional, Tuple, Iterator

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceGain, ResourceQuantity, \
    CurrentResources


@dataclass(frozen=True)
class ResourceLock:
    locked_by: ItemResourceInfo
    item_to_lock: ItemResourceInfo
    temporary_item: ItemResourceInfo

    def convert_gain(self, gain: ResourceGain) -> ResourceGain:
        for resource, quantity in gain:
            if self.item_to_lock == resource:
                resource = self.temporary_item
            yield resource, quantity


@dataclass(frozen=True)
class ConditionalResources:
    name: Optional[str]
    item: Optional[ItemResourceInfo]
    resources: ResourceGainTuple


@dataclass(frozen=True)
class ResourceConversion:
    source: ItemResourceInfo
    target: ItemResourceInfo
    clear_source: bool = True
    overwrite_target: bool = False


MAXIMUM_PICKUP_PROGRESSION = 32
MAXIMUM_PICKUP_RESOURCES = 32
MAXIMUM_PICKUP_CONVERSION = 2


@dataclass(frozen=True)
class PickupEntry:
    name: str
    model_index: int
    item_category: ItemCategory
    broad_category: ItemCategory
    progression: ResourceGainTuple
    extra_resources: ResourceGainTuple = tuple()
    resource_lock: Optional[ResourceLock] = None
    respects_lock: bool = True
    convert_resources: Tuple[ResourceConversion, ...] = tuple()
    probability_offset: float = 0
    probability_multiplier: float = 1

    def __post_init__(self):
        if not isinstance(self.progression, tuple):
            raise ValueError("resources should be a tuple, got {}".format(self.progression))

        for i, progression in enumerate(self.progression):
            if not isinstance(progression, tuple):
                raise ValueError(f"{i}-th progression should be a tuple, got {progression}")

            if len(progression) != 2:
                raise ValueError(f"{i}-th progression should have 2 elements, got {len(progression)}")

            if not isinstance(progression[1], int):
                raise ValueError(f"{i}-th progression second field should be a int, got {progression[1]}")

        if len(self.convert_resources) > MAXIMUM_PICKUP_CONVERSION:
            raise ValueError(f"convert_resources should have at most {MAXIMUM_PICKUP_CONVERSION} value")

        for i, conversion in enumerate(self.convert_resources):
            if not conversion.clear_source or conversion.overwrite_target:
                raise ValueError(f"clear_source and overwrite_target should be True and False, "
                                 f"got {conversion.clear_source} and {conversion.overwrite_target} for index {i}")

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    @property
    def conditional_resources(self):
        previous: Optional[ItemResourceInfo] = None
        for progression in self.progression:
            yield ConditionalResources(
                name=progression[0].long_name,
                item=previous,
                resources=(progression,) + self.extra_resources,
            )
            previous = progression[0]

        if not self.progression:
            yield ConditionalResources(
                name=self.name,
                item=None,
                resources=self.extra_resources,
            )

    def conditional_for_resources(self, current_resources: CurrentResources) -> ConditionalResources:
        last_conditional: Optional[ConditionalResources] = None

        for conditional in self.conditional_resources:
            if conditional.item is None or current_resources.get(conditional.item, 0) > 0:
                last_conditional = conditional
            else:
                break

        assert last_conditional is not None
        return last_conditional

    def conversion_resource_gain(self, current_resources: CurrentResources) -> ResourceGain:
        for conversion in self.convert_resources:
            quantity = current_resources.get(conversion.source, 0)
            yield conversion.source, -quantity
            yield conversion.target, quantity

    def resource_gain(self, current_resources: CurrentResources, force_lock: bool = False) -> ResourceGain:
        resources = self.conditional_for_resources(current_resources).resources

        if (force_lock or self.respects_lock) and (self.resource_lock is not None and
                                                   current_resources.get(self.resource_lock.locked_by, 0) == 0):
            yield from self.resource_lock.convert_gain(resources)
        else:
            yield from resources

        # FIXME: this is not converting the temporary missiles that were just given
        yield from self.conversion_resource_gain(current_resources)

    def __str__(self):
        return "Pickup {}".format(self.name)

    @property
    def all_resources(self) -> Iterator[ResourceQuantity]:
        yield from self.progression
        yield from self.extra_resources

    @property
    def is_expansion(self) -> bool:
        return self.item_category == ItemCategory.EXPANSION
