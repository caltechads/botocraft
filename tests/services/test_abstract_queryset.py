import re
from datetime import datetime
from typing import Optional

import pytest
from pydantic import Field

from botocraft.services.abstract import (
    Boto3Model,
    PrimaryBoto3ModelQuerySet,
)


class SimpleTestModel(Boto3Model):
    """A simple model for testing the queryset."""

    name: str
    type: str
    active: bool = True
    score: int = 0
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)  # Add metadata field for the tests


@pytest.fixture
def empty_queryset():
    """Fixture providing an empty queryset."""
    return PrimaryBoto3ModelQuerySet([])


@pytest.fixture
def test_models():
    """Fixture providing a list of test models."""
    return [
        SimpleTestModel(name="model-1", type="a", score=10, tags=["tag1", "tag2"]),
        SimpleTestModel(name="model-2", type="b", score=20, tags=["tag2", "tag3"]),
        SimpleTestModel(name="model-3", type="a", score=30, tags=["tag3", "tag4"]),
        SimpleTestModel(name="model-4", type="c", score=40, active=False),
    ]


@pytest.fixture
def test_queryset(test_models):
    """Fixture providing a queryset with test models."""
    return PrimaryBoto3ModelQuerySet(test_models)


class TestPrimaryBoto3ModelQuerySet:
    """Test suite for the PrimaryBoto3ModelQuerySet class."""

    def test_init_with_models(self, test_models):
        """Test initializing with models."""
        queryset = PrimaryBoto3ModelQuerySet(test_models)
        assert len(queryset.results) == 4
        assert queryset.results == test_models

    def test_init_empty(self):
        """Test initializing with no models."""
        queryset = PrimaryBoto3ModelQuerySet([])
        assert len(queryset.results) == 0
        assert queryset.results == []

    def test_init_none(self):
        """Test initializing with None."""
        queryset = PrimaryBoto3ModelQuerySet(None)
        assert len(queryset.results) == 0
        assert queryset.results == []

    def test_first(self, test_queryset, test_models):
        """Test getting the first model."""
        assert test_queryset.first() == test_models[0]

    def test_first_empty(self, empty_queryset):
        """Test getting the first model when empty."""
        assert empty_queryset.first() is None

    def test_len(self, test_queryset):
        """Test len() function."""
        assert len(test_queryset) == 4

    def test_len_empty(self, empty_queryset):
        """Test len() function when empty."""
        assert len(empty_queryset) == 0

    def test_bool(self, test_queryset, empty_queryset):
        """Test boolean evaluation."""
        assert bool(test_queryset) is True
        assert bool(empty_queryset) is False

    def test_exists(self, test_queryset, empty_queryset):
        """Test exists() method."""
        assert test_queryset.exists() is True
        assert empty_queryset.exists() is False

    def test_count(self, test_queryset, empty_queryset):
        """Test count() method."""
        assert test_queryset.count() == 4
        assert empty_queryset.count() == 0

    def test_iteration(self, test_queryset, test_models):
        """Test iteration over the queryset."""
        models = []
        for model in test_queryset:
            models.append(model)  # noqa: PERF402
        assert models == test_models

    def test_filter(self, test_queryset):
        """Test filter() method."""
        # Filter by type
        filtered = test_queryset.filter(type="a")
        assert len(filtered) == 2
        assert all(model.type == "a" for model in filtered)

    def test_filter_dict_value(self, test_queryset):
        """Test filtering by a dictionary value."""
        # Add metadata to test models
        test_queryset.results[0].metadata = {
            "environment": "prod",
            "region": "us-west-2",
        }
        test_queryset.results[1].metadata = {
            "environment": "staging",
            "region": "us-west-2",
        }
        test_queryset.results[2].metadata = {
            "environment": "prod",
            "region": "us-east-1",
        }
        test_queryset.results[3].metadata = {"region": "eu-west-1"}

        # Filter by a specific metadata value
        filtered = test_queryset.filter(metadata__environment="prod")
        assert len(filtered) == 2
        assert [m.name for m in filtered] == ["model-1", "model-3"]

    def test_filter_dict_value2(self, test_queryset):
        """Test filtering by a dictionary value."""
        # Add metadata to test models
        test_queryset.results[0].metadata = {
            "environment": "prod",
            "region": "us-west-2",
        }
        test_queryset.results[1].metadata = {
            "environment": "staging",
            "region": "us-west-2",
        }
        test_queryset.results[2].metadata = {
            "environment": "prod",
            "region": "us-east-1",
        }
        test_queryset.results[3].metadata = {"region": "eu-west-1"}

        # Filter by another metadata value
        filtered = test_queryset.filter(metadata__region="us-west-2")
        assert len(filtered) == 2
        assert [m.name for m in filtered] == ["model-1", "model-2"]

    def test_filter_dict_value_combined(self, test_queryset):
        """Test filtering by a dictionary value."""
        # Add metadata to test models
        test_queryset.results[0].metadata = {
            "environment": "prod",
            "region": "us-west-2",
        }
        test_queryset.results[1].metadata = {
            "environment": "staging",
            "region": "us-west-2",
        }
        test_queryset.results[2].metadata = {
            "environment": "prod",
            "region": "us-east-1",
        }
        test_queryset.results[3].metadata = {"region": "eu-west-1"}

        # Filter by combination of metadata values
        filtered = test_queryset.filter(
            metadata__environment="prod", metadata__region="us-east-1"
        )
        assert len(filtered) == 1
        assert filtered[0].name == "model-3"

    def test_filter_dict_value_for_missing_key(self, test_queryset):
        """Test filtering by a dictionary value."""
        # Add metadata to test models
        test_queryset.results[0].metadata = {
            "environment": "prod",
            "region": "us-west-2",
        }
        test_queryset.results[1].metadata = {
            "environment": "staging",
            "region": "us-west-2",
        }
        test_queryset.results[2].metadata = {
            "environment": "prod",
            "region": "us-east-1",
        }
        test_queryset.results[3].metadata = {"region": "eu-west-1"}

        # Filter by missing metadata key
        filtered = test_queryset.filter(metadata__environment="dev")
        assert len(filtered) == 0

    def test_chained_filters(self, test_queryset):
        """Test chaining multiple filters."""
        filtered = test_queryset.filter(active=True).filter(score__gt=15)
        assert len(filtered) == 2
        assert all(model.active and model.score > 15 for model in filtered)

    def test_order_by_simple_field(self, test_queryset):
        """Test ordering by a simple field."""
        ordered = test_queryset.order_by("name")
        assert ordered.first().name == "model-1"  # Alphabetically first
        assert ordered.results[-1].name == "model-4"  # Alphabetically last

    def test_order_by_numeric_field(self, test_queryset):
        """Test ordering by a numeric field."""
        ordered = test_queryset.order_by("score")
        assert [m.score for m in ordered.results] == [10, 20, 30, 40]

        # Test reverse ordering
        ordered = test_queryset.order_by("-score")
        assert [m.score for m in ordered.results] == [40, 30, 20, 10]

    def test_order_by_nested_field(self, test_queryset):
        """Test ordering by a nested field."""
        # Add nested data to test
        test_queryset.results[0].metadata["priority"] = 2
        test_queryset.results[1].metadata["priority"] = 1
        test_queryset.results[2].metadata["priority"] = 3
        # Ensure the last model has a metadata dict too
        test_queryset.results[3].metadata = {}

        ordered = test_queryset.order_by("metadata__priority")
        priorities = [m.metadata.get("priority") for m in ordered.results]
        # None values should come first, then in ascending order
        assert priorities == [None, 1, 2, 3]

    def test_order_by_list_field(self, test_queryset):
        """Test ordering by a field that might return a list."""
        ordered = test_queryset.order_by("tags")
        # Models with tags should be ordered by first tag
        assert all(hasattr(m, "tags") for m in ordered.results)

    def test_chained_filter_and_order(self, test_queryset):
        """Test chaining filter and order_by methods."""
        result = test_queryset.filter(type="a").order_by(
            "score"
        )  # Changed from t2.micro to a
        assert len(result) == 2
        assert [m.score for m in result.results] == [10, 30]

        # Chain in the opposite order
        result = test_queryset.order_by("score").filter(
            type="a"
        )  # Changed from t2.micro to a
        assert len(result) == 2
        assert [m.score for m in result.results] == [10, 30]

    def test_getitem_single_index(self, test_queryset, test_models):
        """Test getting a single item by index."""
        assert test_queryset[0] == test_models[0]
        assert test_queryset[2] == test_models[2]

        # Test negative index
        assert test_queryset[-1] == test_models[-1]

        # Test index out of range
        with pytest.raises(IndexError):
            test_queryset[10]  # Out of range

    def test_getitem_slice(self, test_queryset, test_models):
        """Test getting a slice of items."""
        # Simple slice
        sliced = test_queryset[1:3]
        assert isinstance(sliced, PrimaryBoto3ModelQuerySet)
        assert len(sliced) == 2
        assert sliced.results == test_models[1:3]

        # Slice with step
        sliced = test_queryset[::2]  # Every other item
        assert len(sliced) == 2
        assert sliced.results == test_models[::2]

        # Negative indices in slice
        sliced = test_queryset[-2:]
        assert len(sliced) == 2
        assert sliced.results == test_models[-2:]

        # Empty slice
        sliced = test_queryset[10:20]
        assert len(sliced) == 0

    def test_chained_slice_then_filter(self, test_queryset):
        """Test chaining slice with a filter after it."""
        # Slice then filter
        result = test_queryset[1:3].filter(active=True)
        assert len(result) == 2
        assert all(model.active for model in result)

    def test_chained_filter_then_slice(self, test_queryset):
        """Test chaining filter with a slice after it."""
        result = test_queryset.filter(active=True)[1:2]
        assert len(result) == 1

    def test_chained_slice_then_order_by(self, test_queryset):
        """Test chaining slice with an order_by after it."""
        result = test_queryset[1:4].order_by("score")
        assert len(result) == 3
        assert [m.score for m in result.results] == [20, 30, 40]

    def test_chained_order_by_then_slice(self, test_queryset):
        """Test chaining order_by with a slice after it."""
        result = test_queryset.order_by("score")[1:3]
        assert len(result) == 2
        assert [m.score for m in result.results] == [20, 30]

    def test_chained_slice_all_ops(self, test_queryset):
        """Test chaining slice with both filter and order_by."""
        result = test_queryset.filter(active=True).order_by("score")[1:]
        assert len(result) == 2
        assert [m.score for m in result.results] == [20, 30]


class RelatedModel(Boto3Model):
    """A related model for testing relationship traversal in querysets."""

    id: str
    name: str
    status: str = "active"
    priority: int = 0

    @property
    def child(self) -> Optional["NestedRelatedModel"]:
        """A relationship to a nested model for testing multi-level traversal."""
        if self.id.startswith("has-child"):
            return NestedRelatedModel(
                id=f"child-{self.id}",
                name=f"Child of {self.name}",
                value=self.priority * 10,
            )
        return None


class NestedRelatedModel(Boto3Model):
    """A nested related model for testing deep relationship traversal."""

    id: str
    name: str
    value: int = 0


class ModelWithRelationships(Boto3Model):
    """A model with relationship properties for testing queryset operations."""

    name: str
    type: str
    active: bool = True
    score: int = 0
    related_id: str | None = None
    nested_related_ids: list[str] = Field(default_factory=list)

    @property
    def related(self) -> RelatedModel | None:
        """A single relation property."""
        if not self.related_id:
            return None
        priority = 0
        if "high" in self.related_id:
            priority = 3
        elif "medium" in self.related_id:
            priority = 2
        elif "low" in self.related_id:
            priority = 1
        return RelatedModel(
            id=self.related_id, name=f"Related to {self.name}", priority=priority
        )

    @property
    def nested_relations(self) -> list[RelatedModel]:
        """A one-to-many relation property."""
        return [
            RelatedModel(
                id=rel_id,
                name=f"Nested {idx} of {self.name}",
                priority=int(rel_id[-1] if rel_id.startswith("has-child") else 0),
            )
            for idx, rel_id in enumerate(self.nested_related_ids)
        ]


@pytest.fixture
def models_with_relationships():
    """Fixture providing test models with relationships."""
    return [
        ModelWithRelationships(
            name="model-1",
            type="a",
            score=10,
            related_id="low-priority",
            nested_related_ids=["nested-1", "has-child-1"],
        ),
        ModelWithRelationships(
            name="model-2",
            type="b",
            score=20,
            related_id="medium-priority",
            nested_related_ids=["nested-2"],
        ),
        ModelWithRelationships(
            name="model-3",
            type="a",
            score=30,
            related_id="high-priority",
            nested_related_ids=["has-child-2"],
        ),
        ModelWithRelationships(
            name="model-4", type="c", score=40, active=False, related_id=None
        ),
    ]


@pytest.fixture
def relationship_queryset(models_with_relationships):
    """Fixture providing a queryset with models having relationships."""
    return PrimaryBoto3ModelQuerySet(models_with_relationships)


class TestRelationshipTraversal:
    """Test suite for relationship traversal in PrimaryBoto3ModelQuerySet."""

    def test_filter_by_relationship_field(self, relationship_queryset):
        """Test filtering by a field on a related object."""
        filtered = relationship_queryset.filter(related__name__contains="model-1")
        assert len(filtered) == 1
        assert filtered.first().name == "model-1"

    def test_filter_by_relationship_priority(self, relationship_queryset):
        """Test filtering by a numeric field on related objects."""
        # Find models with high priority related objects
        filtered = relationship_queryset.filter(related__priority__gt=2)
        assert len(filtered) == 1
        assert all(f.related.priority > 2 for f in filtered)

    def test_filter_by_relationship_priority_is_null(self, relationship_queryset):
        """Test filtering where related priority is None."""
        filtered = relationship_queryset.filter(related__priority__isnull=False)
        assert len(filtered) == 3

    def test_order_by_relationship_field(self, relationship_queryset):
        """Test ordering by a field on a related object."""
        # Order by priority on the related object
        ordered = relationship_queryset.order_by("related__priority")

        # Null values come first, then in ascending order of priority
        models = list(ordered)
        assert models[0].name == "model-4"  # No related (None)
        assert models[1].name == "model-1"  # Low priority
        assert models[2].name == "model-2"  # Medium priority
        assert models[3].name == "model-3"  # Low priority

    def test_order_by_relationship_field_reverse(self, relationship_queryset):
        """Test ordering by a field on a related object in reverse."""
        ordered = relationship_queryset.order_by("-related__priority")
        models = list(ordered)
        assert models[0].name == "model-3"  # High priority
        assert models[3].name == "model-4"  # No related (None)

    def test_filter_on_many_relationship(self, relationship_queryset):
        """Test filtering on a one-to-many relationship."""
        # Find models that have any nested relation with "Nested 0" in the name
        filtered = relationship_queryset.filter(
            nested_relations__name__contains="Nested 0"
        )
        assert len(filtered) == 3  # Models 1, 2, and 3

    def test_filter_on_nested_relationship(self, relationship_queryset):
        """Test filtering on a nested relationship."""
        filtered = relationship_queryset.filter(
            nested_relations__id__startswith="has-child"
        )
        assert len(filtered) == 2
        assert sorted([m.name for m in filtered]) == ["model-1", "model-3"]

    def test_multi_level_traversal(self, relationship_queryset):
        """Test filtering through multiple levels of relationships."""
        # Find models that have a nested relation with a child whose name contains "Child"
        filtered = relationship_queryset.filter(
            nested_relations__child__name__contains="Child"
        )
        assert len(filtered) == 2
        assert sorted([m.name for m in filtered]) == ["model-1", "model-3"]

    def test_multi_level_traversal_order_by(
        self, relationship_queryset, models_with_relationships
    ):
        # Test ordering by a deeply nested field
        ordered = relationship_queryset.order_by("nested_relations__child__value")

        # Find the last model - should be the one with highest child value
        models_with_child = [
            m
            for m in models_with_relationships
            if any(rel_id.startswith("has-child") for rel_id in m.nested_related_ids)
        ]
        highest_priority = max(
            m.related.priority if m.related else 0 for m in models_with_child
        )
        assert ordered[-1].related.priority == highest_priority

    def test_chained_filtering_with_relationships(self, relationship_queryset):
        """Test chaining multiple filters involving relationships."""
        # Filter by type and then by related field
        result = relationship_queryset.filter(type="a").filter(related__priority__gt=0)
        assert len(result) == 2
        assert all(
            m.type == "a" and m.related and m.related.priority > 0 for m in result
        )

        # Filter in reverse order
        result = relationship_queryset.filter(related__priority__gt=0).filter(type="a")
        assert len(result) == 2
        assert all(
            m.type == "a" and m.related and m.related.priority > 0 for m in result
        )

    def test_filter_and_order_with_relationships(self, relationship_queryset):
        """Test filtering and ordering with relationships."""
        # Filter models with type "a" and order by related priority
        result = relationship_queryset.filter(type="a").order_by("related__priority")
        assert len(result) == 2
        assert [m.related.priority for m in result.results] == [1, 3]


class TestValuesAndValuesList:
    """Test suite for values() and values_list() methods."""

    @pytest.fixture
    def test_models(self) -> list[Boto3Model]:
        """Create a list of test models."""

        class SimpleModel(Boto3Model):
            id: str
            name: str
            age: int
            active: bool
            created_at: datetime = Field(default_factory=datetime.now)
            tags: dict = Field(default_factory=dict)

            @property
            def full_name(self):
                return f"Full: {self.name}"

            @property
            def nested_data(self):
                return {"key1": "value1", "key2": self.age * 2}

        return [
            SimpleModel(
                id="1", name="Alice", age=30, active=True, tags={"role": "admin"}
            ),
            SimpleModel(
                id="2", name="Bob", age=25, active=False, tags={"role": "user"}
            ),
            SimpleModel(
                id="3", name="Charlie", age=35, active=True, tags={"role": "user"}
            ),
        ]

    def test_values_no_fields(self, test_models):
        """Test values() with no specified fields returns all fields."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = qs.values()  # No need to call list() anymore

        assert len(values) == 3
        assert isinstance(values[0], dict)
        assert "id" in values[0]
        assert "name" in values[0]
        assert "age" in values[0]
        assert "active" in values[0]
        assert values[0]["id"] == "1"
        assert values[1]["name"] == "Bob"
        assert values[2]["age"] == 35

    def test_values_specific_fields(self, test_models):
        """Test values() with specific fields returns only those fields."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = qs.values("id", "name")  # No need to call list() anymore

        assert len(values) == 3
        assert set(values[0].keys()) == {"id", "name"}
        assert values[0]["id"] == "1"
        assert values[0]["name"] == "Alice"
        assert "age" not in values[0]

    def test_values_with_property(self, test_models):
        """Test values() with a property field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values("id", "full_name"))

        assert len(values) == 3
        assert values[0]["full_name"] == "Full: Alice"
        assert values[1]["full_name"] == "Full: Bob"

    def test_values_with_nested_property(self, test_models):
        """Test values() with a nested property field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values("id", "nested_data__key2"))

        assert len(values) == 3
        assert values[0]["nested_data__key2"] == 60  # 30 * 2
        assert values[1]["nested_data__key2"] == 50  # 25 * 2

    def test_values_with_dict_field(self, test_models):
        """Test values() with a dictionary field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values("id", "tags__role"))

        assert len(values) == 3
        assert values[0]["tags__role"] == "admin"
        assert values[1]["tags__role"] == "user"

    def test_values_with_nonexistent_field(self, test_models):
        """Test values() with a field that doesn't exist."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values("id", "nonexistent"))

        assert len(values) == 3
        assert values[0]["id"] == "1"
        assert values[0]["nonexistent"] is None

    def test_values_empty_queryset(self):
        """Test values() with an empty queryset."""
        qs = PrimaryBoto3ModelQuerySet([])
        values = list(qs.values("id", "name"))

        assert len(values) == 0

    def test_values_list_single_field(self, test_models):
        """Test values_list() with a single field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("name"))

        assert len(values) == 3
        assert values[0] == ("Alice",)
        assert values[1] == ("Bob",)
        assert values[2] == ("Charlie",)

    def test_values_list_multiple_fields(self, test_models):
        """Test values_list() with multiple fields."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("id", "name", "age"))

        assert len(values) == 3
        assert values[0] == ("1", "Alice", 30)
        assert values[1] == ("2", "Bob", 25)
        assert values[2] == ("3", "Charlie", 35)

    def test_values_list_flat(self, test_models):
        """Test values_list() with flat=True."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("name", flat=True))

        assert len(values) == 3
        assert values[0] == "Alice"
        assert values[1] == "Bob"
        assert values[2] == "Charlie"

    def test_values_list_with_property(self, test_models):
        """Test values_list() with a property field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("full_name", flat=True))

        assert len(values) == 3
        assert values[0] == "Full: Alice"
        assert values[1] == "Full: Bob"

    def test_values_list_with_nested_field(self, test_models):
        """Test values_list() with a nested field."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("id", "tags__role"))

        assert len(values) == 3
        assert values[0] == ("1", "admin")
        assert values[1] == ("2", "user")

    def test_values_list_flat_with_multiple_fields_raises_error(self, test_models):
        """Test values_list() with flat=True and multiple fields raises ValueError."""
        qs = PrimaryBoto3ModelQuerySet(test_models)

        with pytest.raises(
            ValueError,
            match=re.escape(
                "flat=True is only valid when values_list() is called with a single field"
            ),
        ):
            list(qs.values_list("id", "name", flat=True))

    def test_values_list_no_fields_raises_error(self, test_models):
        """Test values_list() with no fields raises ValueError."""
        qs = PrimaryBoto3ModelQuerySet(test_models)

        with pytest.raises(
            ValueError,
            match=re.escape("values_list() requires at least one field name"),
        ):
            list(qs.values_list())

    def test_values_list_nonexistent_field(self, test_models):
        """Test values_list() with a field that doesn't exist."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = list(qs.values_list("id", "nonexistent"))

        assert len(values) == 3
        assert values[0] == ("1", None)
        assert values[1] == ("2", None)

    def test_chaining_filter_and_values(self, test_models):
        """Test chaining filter() and values()."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = qs.filter(active=True).values(
            "id", "name"
        )  # No need to call list() anymore

        assert len(values) == 2
        assert values[0]["id"] == "1"
        assert values[0]["name"] == "Alice"
        assert values[1]["id"] == "3"
        assert values[1]["name"] == "Charlie"

    def test_chaining_filter_and_values_list(self, test_models):
        """Test chaining filter() and values_list()."""
        qs = PrimaryBoto3ModelQuerySet(test_models)
        values = qs.filter(age__gt=25).values_list(
            "name", flat=True
        )  # No need to call list() anymore

        assert len(values) == 2
        assert values[0] == "Alice"
        assert values[1] == "Charlie"
