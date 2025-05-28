from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel, Field

from botocraft.services.abstract import (
    Boto3Model,
    Boto3ModelManagerFilter,
    PrimaryBoto3ModelQuerySet,
)


class Tag(BaseModel):
    Key: str
    Value: str


class NetworkInterface(BaseModel):
    private_ip_address: str
    description: str


class SecurityGroup(BaseModel):
    group_id: str
    group_name: str


class TestModel(Boto3Model):
    name: str
    status: str
    type: str
    count: int
    tags: list[Tag] = Field(default_factory=list)
    is_active: bool = True
    description: str | None = None
    network_interfaces: list[NetworkInterface] = Field(default_factory=list)
    security_groups: list[SecurityGroup] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime | None = None


@pytest.fixture
def test_models():
    """Fixture providing a list of test models for filtering."""
    return [
        TestModel(
            name="web-server-1",
            status="running",
            type="t2.micro",
            count=5,
            tags=[
                Tag(Key="Name", Value="web-server"),
                Tag(Key="Environment", Value="production"),
            ],
            network_interfaces=[
                NetworkInterface(private_ip_address="10.0.0.1", description="Primary")
            ],
            security_groups=[
                SecurityGroup(group_id="sg-123", group_name="web-sg"),
                SecurityGroup(group_id="sg-456", group_name="common-sg"),
            ],
            metadata={"region": "us-west-2", "created_by": "user1"},
            created_at=datetime(2023, 3, 15, 10, 30, 0, tzinfo=timezone.utc),
        ),
        TestModel(
            name="db-server",
            status="stopped",
            type="t2.large",
            count=10,
            tags=[
                Tag(Key="Name", Value="db-server"),
                Tag(Key="Environment", Value="production"),
            ],
            network_interfaces=[
                NetworkInterface(private_ip_address="10.0.0.2", description="Primary")
            ],
            security_groups=[
                SecurityGroup(group_id="sg-789", group_name="db-sg"),
                SecurityGroup(group_id="sg-456", group_name="common-sg"),
            ],
            metadata={"region": "us-west-2", "created_by": "user2"},
            created_at=datetime(2023, 6, 20, 14, 45, 30, tzinfo=timezone.utc),
        ),
        TestModel(
            name="test-server",
            status="running",
            type="t2.micro",
            count=3,
            tags=[
                Tag(Key="Name", Value="test-server"),
                Tag(Key="Environment", Value="staging"),
            ],
            description="Test server",
            metadata={"region": "us-east-1", "created_by": "user1"},
            created_at=datetime(2023, 9, 5, 8, 15, 0, tzinfo=timezone.utc),
        ),
        TestModel(
            name="inactive-server",
            status="terminated",
            type="t2.nano",
            count=0,
            is_active=False,
            created_at=datetime(2022, 12, 10, 23, 59, 59, tzinfo=timezone.utc),
        ),
    ]


class RelatedTestModel(Boto3Model):
    """A related model for testing relationship filtering."""

    id: str
    name: str
    description: str = "Default description"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("UTC"))
    )


class TestModelWithRelation(Boto3Model):
    """A model with relationship properties for testing filters."""

    id: str
    name: str
    related_id: str | None = None
    other_related_ids: list[str] = Field(default_factory=list)

    @property
    def related(self) -> RelatedTestModel | None:
        """Test relationship property that returns a single related model."""
        if not self.related_id:
            return None
        return RelatedTestModel(id=self.related_id, name=f"Related to {self.name}")

    @property
    def other_related(self) -> list[RelatedTestModel]:
        """Test relationship property that returns multiple related models."""
        return [
            RelatedTestModel(id=rel_id, name=f"Other {idx}")
            for idx, rel_id in enumerate(self.other_related_ids)
        ]


@pytest.fixture
def test_models_with_relations():
    """Create test models with relationships."""
    return [
        TestModelWithRelation(
            id="1",
            name="Model One",
            related_id="rel-1",
            other_related_ids=["other-1", "other-2"],
        ),
        TestModelWithRelation(
            id="2", name="Model Two", related_id="rel-2", other_related_ids=["other-3"]
        ),
        TestModelWithRelation(id="3", name="Model Three", related_id=None),
        TestModelWithRelation(
            id="4", name="Model Four", related_id="rel-4", other_related_ids=[]
        ),
    ]


class TestBoto3ModelManagerFilter:
    """Test suite for the Boto3ModelManagerFilter class."""

    def test_exact_match(self, test_models):
        """Test filtering with exact match."""
        filtered = Boto3ModelManagerFilter(test_models, status="running")()
        assert len(filtered) == 2
        assert all(model.status == "running" for model in filtered)

        # Multiple exact matches
        filtered = Boto3ModelManagerFilter(
            test_models, status="running", type="t2.micro"
        )()
        assert len(filtered) == 2
        assert all(
            model.status == "running" and model.type == "t2.micro" for model in filtered
        )

    def test_case_sensitive_matches(self, test_models):
        """Test case-sensitive lookups."""
        # Contains
        filtered = Boto3ModelManagerFilter(test_models, name__contains="server")()
        assert len(filtered) == 4

        # Startswith
        filtered = Boto3ModelManagerFilter(test_models, name__startswith="web")()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Endswith
        filtered = Boto3ModelManagerFilter(test_models, name__endswith="server")()
        assert len(filtered) == 3

    def test_case_insensitive_matches(self, test_models):
        """Test case-insensitive lookups."""
        # iexact
        filtered = Boto3ModelManagerFilter(test_models, status__iexact="RUNNING")()
        assert len(filtered) == 2

        # icontains
        filtered = Boto3ModelManagerFilter(test_models, name__icontains="WEB")()
        assert len(filtered) == 1

        # istartswith
        filtered = Boto3ModelManagerFilter(test_models, name__istartswith="WEB")()
        assert len(filtered) == 1

        # iendswith
        filtered = Boto3ModelManagerFilter(test_models, name__iendswith="SERVER")()
        assert len(filtered) == 3

    def test_comparison_lookups(self, test_models):
        """Test comparison operators."""
        # Greater than
        filtered = Boto3ModelManagerFilter(test_models, count__gt=4)()
        assert len(filtered) == 2
        assert all(model.count > 4 for model in filtered)

        # Greater than or equal
        filtered = Boto3ModelManagerFilter(test_models, count__gte=5)()
        assert len(filtered) == 2
        assert all(model.count >= 5 for model in filtered)

        # Less than
        filtered = Boto3ModelManagerFilter(test_models, count__lt=5)()
        assert len(filtered) == 2
        assert all(model.count < 5 for model in filtered)

        # Less than or equal
        filtered = Boto3ModelManagerFilter(test_models, count__lte=5)()
        assert len(filtered) == 3
        assert all(model.count <= 5 for model in filtered)

    def test_in_lookup(self, test_models):
        """Test 'in' lookup."""
        filtered = Boto3ModelManagerFilter(
            test_models, status__in=["running", "stopped"]
        )()
        assert len(filtered) == 3
        assert all(model.status in ["running", "stopped"] for model in filtered)

    def test_isnull_lookup(self, test_models):
        """Test 'isnull' lookup."""
        # Description is null
        filtered = Boto3ModelManagerFilter(test_models, description__isnull=True)()
        assert len(filtered) == 3
        assert all(model.description is None for model in filtered)

        # Description is not null
        filtered = Boto3ModelManagerFilter(test_models, description__isnull=False)()
        assert len(filtered) == 1
        assert all(model.description is not None for model in filtered)

    def test_boolean_field(self, test_models):
        """Test filtering on boolean fields."""
        filtered = Boto3ModelManagerFilter(test_models, is_active=True)()
        assert len(filtered) == 3
        assert all(model.is_active for model in filtered)

    def test_nested_attribute_filtering(self, test_models):
        """Test filtering on nested attributes."""
        # Filter on nested tag attribute - now automatically searches all items
        filtered = Boto3ModelManagerFilter(test_models, tags__Value="web-server")()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Filter on metadata dictionary
        filtered = Boto3ModelManagerFilter(test_models, metadata__region="us-west-2")()
        assert len(filtered) == 2
        assert all(model.metadata.get("region") == "us-west-2" for model in filtered)

    def test_automatic_list_traversal(self, test_models):
        """Test automatic traversal through lists without need for any keyword."""
        # Find models with common-sg in any security group
        filtered = Boto3ModelManagerFilter(
            test_models, security_groups__group_name="common-sg"
        )()
        assert len(filtered) == 2
        assert sorted([model.name for model in filtered]) == [
            "db-server",
            "web-server-1",
        ]

        # Find models with any tag having Environment=production
        filtered = Boto3ModelManagerFilter(test_models, tags__Value="production")()
        assert len(filtered) == 2
        assert sorted([model.name for model in filtered]) == [
            "db-server",
            "web-server-1",
        ]

        # Test with no matches
        filtered = Boto3ModelManagerFilter(
            test_models, security_groups__group_name="nonexistent"
        )()
        assert len(filtered) == 0

    def test_combining_filters(self, test_models):
        """Test combining multiple filters."""
        filtered = Boto3ModelManagerFilter(
            test_models, status="running", type="t2.micro", metadata__created_by="user1"
        )()
        assert (
            len(filtered) == 2
        )  # Both web-server-1 and test-server match these criteria
        assert all(
            model.status == "running"
            and model.type == "t2.micro"
            and model.metadata.get("created_by") == "user1"
            for model in filtered
        )
        assert sorted([model.name for model in filtered]) == [
            "test-server",
            "web-server-1",
        ]

    def test_empty_results(self, test_models):
        """Test filtering with no matches."""
        filtered = Boto3ModelManagerFilter(test_models, status="nonexistent")()
        assert len(filtered) == 0
        assert not filtered

    def test_invalid_field(self, test_models):
        """Test filtering on a non-existent field."""
        filtered = Boto3ModelManagerFilter(test_models, nonexistent_field="value")()
        assert len(filtered) == 0

    def test_filter_dunder_methods(self, test_models):
        """Test the dunder methods of the filter class."""
        filter_obj = Boto3ModelManagerFilter(test_models, status="running")

        # Test __iter__
        assert len(list(filter_obj)) == 2

        # Test __getitem__
        assert filter_obj[0].status == "running"

        # Test slicing
        assert len(filter_obj[0:1]) == 1

        # Test __bool__
        assert bool(filter_obj) is True

        # Test empty filter
        empty_filter = Boto3ModelManagerFilter(test_models, status="nonexistent")
        assert bool(empty_filter) is False

    def test_dictionary_key_filtering(self, test_models):
        """Test filtering on dictionary keys."""
        # Filter models that have 'region' key in metadata
        filtered = Boto3ModelManagerFilter(test_models, metadata__has_key="region")()
        assert len(filtered) == 3
        assert "inactive-server" not in [model.name for model in filtered]

        # Filter models that have both 'region' and 'created_by' keys - using chained filters
        filtered = Boto3ModelManagerFilter(test_models, metadata__has_key="region")()
        filtered = Boto3ModelManagerFilter(filtered, metadata__has_key="created_by")()
        assert len(filtered) == 3

        # Filter on a key that doesn't exist
        filtered = Boto3ModelManagerFilter(
            test_models, metadata__has_key="nonexistent"
        )()
        assert len(filtered) == 0

    def test_dictionary_value_filtering(self, test_models):
        """Test filtering on dictionary values."""
        # Filter by specific metadata value
        filtered = Boto3ModelManagerFilter(test_models, metadata__region="us-west-2")()
        assert len(filtered) == 2
        assert sorted([model.name for model in filtered]) == [
            "db-server",
            "web-server-1",
        ]

        # Filter by value with case-insensitive matching
        filtered = Boto3ModelManagerFilter(
            test_models, metadata__created_by__iexact="USER1"
        )()
        assert len(filtered) == 2
        assert sorted([model.name for model in filtered]) == [
            "test-server",
            "web-server-1",
        ]

        # Filter by partial value
        filtered = Boto3ModelManagerFilter(
            test_models, metadata__region__contains="west"
        )()
        assert len(filtered) == 2

        # Filter by nonexistent value
        filtered = Boto3ModelManagerFilter(
            test_models, metadata__region="nonexistent"
        )()
        assert len(filtered) == 0

    def test_regex_lookups(self, test_models):
        """Test regex and iregex lookups."""
        # Test regex - case sensitive
        filtered = Boto3ModelManagerFilter(test_models, name__regex=r"web-.*")()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test no matches with case sensitivity
        filtered = Boto3ModelManagerFilter(test_models, name__regex=r"WEB-.*")()
        assert len(filtered) == 0  # No matches because of case sensitivity

        # Test iregex - case insensitive
        filtered = Boto3ModelManagerFilter(test_models, name__iregex=r"WEB-.*")()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test regex with number pattern
        filtered = Boto3ModelManagerFilter(test_models, name__regex=r".*-\d+$")()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test regex with alternation
        filtered = Boto3ModelManagerFilter(
            test_models, status__regex=r"running|stopped"
        )()
        assert len(filtered) == 3
        assert all(model.status in ["running", "stopped"] for model in filtered)

        # Test iregex with alternation and mixed case
        filtered = Boto3ModelManagerFilter(
            test_models, status__iregex=r"RUNNING|Stopped"
        )()
        assert len(filtered) == 3
        assert all(model.status in ["running", "stopped"] for model in filtered)

    def test_datetime_filtering(self, test_models):
        """Test filtering based on datetime fields."""
        # Test date filter
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__date=date(2023, 3, 15)
        )()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test year filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__year=2023)()
        assert len(filtered) == 3
        assert "inactive-server" not in [model.name for model in filtered]

        # Test month filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__month=6)()
        assert len(filtered) == 1
        assert filtered[0].name == "db-server"

        # Test day filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__day=5)()
        assert len(filtered) == 1
        assert filtered[0].name == "test-server"

        # Test quarter filter (Q1: 1-3, Q2: 4-6, Q3: 7-9, Q4: 10-12)
        filtered = Boto3ModelManagerFilter(test_models, created_at__quarter=1)()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        filtered = Boto3ModelManagerFilter(test_models, created_at__quarter=2)()
        assert len(filtered) == 1
        assert filtered[0].name == "db-server"

        # Test time filter
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__time=time(10, 30, 0)
        )()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test hour filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__hour=8)()
        assert len(filtered) == 1
        assert filtered[0].name == "test-server"

        # Test minute filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__minute=45)()
        assert len(filtered) == 1
        assert filtered[0].name == "db-server"

        # Test second filter
        filtered = Boto3ModelManagerFilter(test_models, created_at__second=59)()
        assert len(filtered) == 1
        assert filtered[0].name == "inactive-server"

        # Test week filter (ISO week number)
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__week=36
        )()  # Week of Sept 5, 2023
        assert len(filtered) == 1
        assert filtered[0].name == "test-server"

        # Test week_day filter (1=Sunday, 7=Saturday in Django ORM)
        # March 15, 2023 was a Wednesday (3)
        filtered = Boto3ModelManagerFilter(test_models, created_at__week_day=3)()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

        # Test iso_week_day filter (1=Monday, 7=Sunday in ISO)
        # March 15, 2023 was a Wednesday (3 in ISO as well)
        filtered = Boto3ModelManagerFilter(test_models, created_at__iso_week_day=3)()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

    def test_datetime_comparison_filtering(self, test_models):
        """Test comparison operators with datetime fields."""
        # Test greater than
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__gt=datetime(2023, 5, 1, tzinfo=timezone.utc)
        )()
        assert len(filtered) == 2
        assert sorted([model.name for model in filtered]) == [
            "db-server",
            "test-server",
        ]

        # Test less than
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__lt=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )()
        assert len(filtered) == 1
        assert filtered[0].name == "inactive-server"

        # Test timezone conversion
        # Create a non-UTC datetime for comparison
        est_datetime = datetime(
            2023, 3, 15, 6, 0, 0, tzinfo=timezone(timedelta(hours=-4))
        )  # EST
        filtered = Boto3ModelManagerFilter(
            test_models, created_at__date=est_datetime.date()
        )()
        assert len(filtered) == 1
        assert filtered[0].name == "web-server-1"

    def test_filter_by_related_field(self, test_models_with_relations):
        """Test filtering by a field on a related object."""
        # Filter by a field on a direct relationship
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, related__name="Related to Model One"
        )()
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    def test_filter_by_missing_relation(self, test_models_with_relations):
        """Test filtering where the relationship is None."""
        # Only Model Three has no related object
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, related__isnull=True
        )()
        assert len(filtered) == 1
        assert filtered[0].id == "3"

    def test_filter_by_related_contains(self, test_models_with_relations):
        """Test filtering with contains on a related field."""
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, related__name__contains="Model Two"
        )()
        assert len(filtered) == 1
        assert filtered[0].id == "2"

    def test_filter_by_related_regex(self, test_models_with_relations):
        """Test filtering with regex on a related field."""
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, related__name__regex=r"Related to Model \w+"
        )()
        assert len(filtered) == 3  # Models with relations (not Model Three)

        # Case-insensitive regex
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, related__name__iregex=r"RELATED TO model \w+"
        )()
        assert len(filtered) == 3

    def test_filter_on_many_relation(self, test_models_with_relations):
        """Test filtering on a one-to-many relationship."""
        # Filter models that have any related model with 'Other 0' in name
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, other_related__name="Other 0"
        )()
        assert len(filtered) == 2  # Model One and Model Two
        assert {m.id for m in filtered} == {"1", "2"}

    def test_filter_empty_relation_list(self, test_models_with_relations):
        """Test filtering where the relationship list is empty."""
        # Filtering with an empty list should not match any models
        filtered = Boto3ModelManagerFilter(
            test_models_with_relations, other_related=[]
        )()
        assert len(filtered) == 0

    def test_cache_reuse(self, test_models_with_relations):
        """Test that relationship results are cached during a filter operation."""

        # Create a mock class that tracks property access
        class AccessTracker:
            def __init__(self):
                self.access_count = 0

            def increment(self):
                self.access_count += 1
                return self.access_count

        tracker = AccessTracker()

        # Patch the related property to count accesses
        original_related = TestModelWithRelation.related

        try:

            @property
            def tracked_related(self):
                tracker.increment()
                return original_related.__get__(self, type(self))

            TestModelWithRelation.related = tracked_related

            # Apply multiple filters that access the same relationship
            filter_obj = Boto3ModelManagerFilter(test_models_with_relations)
            filter_obj.filters = {
                "related__name__contains": "Model",
                "related__description__contains": "Default",
            }

            results = filter_obj()  # noqa: F841

            # Each model should only evaluate the property once, not once per filter
            assert tracker.access_count <= len(test_models_with_relations)

        finally:
            # Restore the original property
            TestModelWithRelation.related = original_related


class TestRelationshipValuesAndValuesList:
    """Test retrieving values and values_list with relationships."""

    @pytest.fixture
    def related_test_models(self) -> list[Boto3Model]:
        """Create test models with relationships."""

        class RelatedModel(Boto3Model):
            id: str
            name: str
            count: int = 0

        class ParentModel(Boto3Model):
            id: str
            name: str
            related_id: str | None = None

            @property
            def related(self):
                if not self.related_id:
                    return None
                return RelatedModel(
                    id=self.related_id,
                    name=f"Related to {self.name}",
                    count=len(self.name),
                )

            @property
            def multi_related(self):
                if not self.related_id:
                    return []
                return [
                    RelatedModel(
                        id=f"{self.related_id}-1",
                        name=f"First related to {self.name}",
                        count=1,
                    ),
                    RelatedModel(
                        id=f"{self.related_id}-2",
                        name=f"Second related to {self.name}",
                        count=2,
                    ),
                ]

        return [
            ParentModel(id="1", name="First", related_id="rel-1"),
            ParentModel(id="2", name="Second", related_id="rel-2"),
            ParentModel(id="3", name="Third", related_id=None),
        ]

    def test_values_with_relationship(self, related_test_models):
        """Test values() with a relationship field."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        values = list(qs.values("id", "related__name"))

        assert len(values) == 3
        assert values[0]["id"] == "1"
        assert values[0]["related__name"] == "Related to First"
        assert values[1]["related__name"] == "Related to Second"
        assert values[2]["related__name"] is None

    def test_values_with_nested_relationship_field(self, related_test_models):
        """Test values() with a nested field on a relationship."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        values = list(qs.values("id", "related__count"))

        assert len(values) == 3
        assert values[0]["id"] == "1"
        assert values[0]["related__count"] == 5  # Length of "First"
        assert values[1]["related__count"] == 6  # Length of "Second"
        assert values[2]["related__count"] is None

    def test_values_list_with_relationship(self, related_test_models):
        """Test values_list() with a relationship field."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        values = list(qs.values_list("id", "related__name"))

        assert len(values) == 3
        assert values[0] == ("1", "Related to First")
        assert values[1] == ("2", "Related to Second")
        assert values[2] == ("3", None)

    def test_values_list_flat_with_relationship(self, related_test_models):
        """Test values_list() with flat=True and a relationship field."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        values = list(qs.values_list("related__name", flat=True))

        assert len(values) == 3
        assert values[0] == "Related to First"
        assert values[1] == "Related to Second"
        assert values[2] is None

    def test_values_with_multi_relationship(self, related_test_models):
        """Test values() with a one-to-many relationship field."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        values = list(qs.values("id", "multi_related__name"))

        assert len(values) == 3
        assert values[0]["id"] == "1"
        # Should return a list of names from the multi_related property
        assert isinstance(values[0]["multi_related__name"], list)
        assert len(values[0]["multi_related__name"]) == 2
        assert "First related to First" in values[0]["multi_related__name"]
        assert "Second related to First" in values[0]["multi_related__name"]
        assert values[2]["multi_related__name"] is None

    def test_filter_then_values_with_relationship(self, related_test_models):
        """Test chaining filter() and values() with relationship fields."""
        qs = PrimaryBoto3ModelQuerySet(related_test_models)
        # Filter by a relationship field then get values
        values = list(qs.filter(related__count__gt=5).values("id", "name"))

        assert len(values) == 1
        assert values[0]["id"] == "2"
        assert values[0]["name"] == "Second"
