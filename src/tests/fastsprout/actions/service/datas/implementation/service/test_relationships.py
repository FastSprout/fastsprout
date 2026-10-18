import pytest

from fastsprout.actions import DataS
from fastsprout.data import DataR

from ...common import League, Team, TeamRecord, loaded_query


class TestRelationships:
    async def test_create_preserves_native_related_entities(
        self, team_records: DataS[TeamRecord]
    ) -> None:
        # given
        entity = TeamRecord(
            name="Batman",
            team=Team(name="Justice League", league=League(name="World")),
        )
        # when
        created = await team_records.create(entity)
        loaded = await team_records.get(loaded_query(TeamRecord, created.id))
        # then
        assert loaded is not None
        assert type(loaded.team) is Team
        assert loaded.team.league is not None
        assert type(loaded.team.league) is League
        assert loaded.team.league.name == "World"

    @pytest.mark.parametrize("partial", [False, True])
    async def test_update_persists_deep_relationship_changes(
        self, team_records: DataS[TeamRecord], partial: bool
    ) -> None:
        # given
        created = await team_records.create(
            TeamRecord(
                name="Batman",
                team=Team(name="Justice League", league=League(name="World")),
            )
        )
        query = loaded_query(TeamRecord, created.id)
        loaded = await team_records.get(query)
        assert loaded is not None
        assert loaded.team is not None
        assert loaded.team.league is not None
        loaded.name = "Robin"
        loaded.team.name = "Outsiders"
        loaded.team.league.name = "International"
        # when
        if partial:
            await team_records.patch(loaded.id, loaded)
        else:
            await team_records.update(loaded)
        found = await team_records.get(query)
        # then
        assert found is not None
        assert found.name == "Robin"
        assert found.team is not None
        assert found.team.name == "Outsiders"
        assert found.team.league is not None
        assert found.team.league.name == "International"

    @pytest.mark.parametrize("clear", [False, True])
    async def test_replace_or_clear_relationship(
        self, team_records: DataS[TeamRecord], clear: bool
    ) -> None:
        # given
        created = await team_records.create(
            TeamRecord(name="Batman", team=Team(name="Justice League"))
        )
        teams = DataS(Team)
        replacement = await teams.create(Team(name="Outsiders"))
        query = loaded_query(TeamRecord, created.id)
        loaded = await team_records.get(query)
        assert loaded is not None
        loaded.team = None if clear else replacement
        # when
        await team_records.update(loaded)
        found = await team_records.get(query)
        # then
        assert found is not None
        if clear:
            assert found.team is None
        else:
            assert found.team is not None
            assert found.team.id == replacement.id
        assert await teams.exists(replacement.id)

    async def test_rollback_reverts_parent_and_related_changes(
        self, team_records: DataS[TeamRecord]
    ) -> None:
        # given
        created = await team_records.create(
            TeamRecord(name="Batman", team=Team(name="Justice League"))
        )
        query = loaded_query(TeamRecord, created.id)
        # when
        with pytest.raises(ValueError, match="abort"):
            async with DataR() as datar:
                loaded = await team_records.get(query, datar=datar)
                assert loaded is not None
                assert loaded.team is not None
                loaded.name = "Robin"
                loaded.team.name = "Outsiders"
                await team_records.update(loaded, datar=datar)
                raise ValueError("abort")
        found = await team_records.get(query)
        # then
        assert found is not None
        assert found.name == "Batman"
        assert found.team is not None
        assert found.team.name == "Justice League"

    async def test_backend_update_does_not_insert_missing_parent(
        self, team_records: DataS[TeamRecord]
    ) -> None:
        # given
        missing = team_records.entity(name="Batman")
        # when / then
        async with DataR() as datar:
            with pytest.raises(LookupError, match="No TeamRecord"):
                await datar.ability(TeamRecord).update(missing)
        assert not await team_records.exists(missing.id)
