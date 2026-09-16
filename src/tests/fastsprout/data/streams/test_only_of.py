from fastsprout.data.entity import BaseEntity
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream


class Vehicle(BaseEntity[int]):
    pass


class Car(Vehicle):
    pass


class Truck(Vehicle):
    pass


def make_fleet() -> list[Vehicle]:
    return [Car(id=1), Truck(id=2), Car(id=3), Truck(id=4), Car(id=5)]


async def test_only_of_narrows_to_subtype() -> None:
    stream = SimpleAsyncEntityStream(make_fleet())
    cars = await stream.only_of(Car).to_list()

    assert [c.id for c in cars] == [1, 3, 5]
    assert all(isinstance(c, Car) for c in cars)


async def test_views_after_one_materialization() -> None:
    # one pass over the source; views on the materialized list are free
    fleet = await SimpleAsyncEntityStream(make_fleet()).to_list()

    cars = await SimpleAsyncEntityStream(fleet).only_of(Car).to_list()
    trucks = await SimpleAsyncEntityStream(fleet).only_of(Truck).to_list()

    assert len(cars) == 3
    assert len(trucks) == 2


async def test_only_of_base_type_keeps_everything() -> None:
    stream = SimpleAsyncEntityStream(make_fleet())
    assert len(await stream.only_of(Vehicle).to_list()) == 5
