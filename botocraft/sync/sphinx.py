from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from botocraft.sync.service import ServiceGenerator


class ServiceSphinxDocBuilder:
    """
    A Sphinx documentation builder for a single service.

    Do the following things:

      * Gather the managers and models from the service generator.
      * Segregate the models into primary and secondary models
      * Create a Sphinx model page for the service, containing the managers,
        primary models, and secondary models.
      * Write the model page to ``../../doc/source/api/services/<service_name>.rst``
      * Return the path to that file, relative to ``../../doc/source/``

    The service page in the docs should end up looking something like this:

    .. code-block:: rst

        Elastic Container Service (ecs)
        ===============================

        Primary Models
        --------------

        .. autopydantic_model:: botocraft.services.ecs.Cluster

        .. autopydantic_model:: botocraft.services.ecs.Service

        Managers
        --------

        .. autoclass:: botocraft.services.ecs.ClusterManager
            :members:
            :show-inheritance:

        .. autoclass:: botocraft.services.ecs.ServiceManager
            :members:
            :show-inheritance:

        Secondary Models
        ----------------

        .. autopydantic_model:: botocraft.services.ecs.ClusterSetting

        Request/Response Models
        -----------------------

        .. autopydantic_model:: botocraft.services.ecs.ClusterSetting


        ...


    Args:
        generator: The service generator.

    """

    def __init__(self, generator: "ServiceGenerator") -> None:
        #: The service generator.
        self.generator = generator

    @property
    def path(self) -> Path:
        """
        The path to the service documentation file.
        """
        # First get the path to this file
        this_file = Path(__file__).resolve()
        docs_dir = this_file.parents[2] / "doc" / "source" / "api" / "services"
        return docs_dir / f"{self.generator.aws_service_name}.rst"

    @property
    def header(self) -> str:
        """
        The header for the service documentation.
        """
        title = (
            f"{self.generator.service_full_name} ({self.generator.aws_service_name})"
        )
        return f"""
{title}
{'=' * len(title)}
"""

    def autoclass(self, class_name: str, pydantic: bool = True) -> str:
        """
        The Sphinx documentation for a manager.

        Args:
            class_name: The name of the class to document
            pydantic: Whether to use autopydantic_model or autoclass

        """
        if pydantic:
            return f"""

.. autopydantic_model:: botocraft.services.{self.generator.aws_service_name}.{class_name}
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json
"""  # noqa: E501
        return f"""
.. autoclass:: botocraft.services.{self.generator.aws_service_name}.{class_name}
   :members:
   :show-inheritance:
"""

    def classes(self, names: List[str], pydantic: bool = True) -> str:
        """
        The Sphinx documentation for the managers.
        """
        names.sort()
        code = ""
        for name in names:
            code += self.autoclass(name, pydantic=pydantic)
        return f"""{code}
"""

    @property
    def body(self) -> str:
        """
        The body of the documentation. for the service.
        """
        managers = list(self.generator.manager_classes.keys())
        managers_doc = self.classes(managers, pydantic=False)
        # TODO: the following code doesn't take into account alternate names
        # for primary models.
        primary_models = [
            model
            for model in self.generator.model_classes
            if model in self.generator.service_def.primary_models
        ]
        primary_models_doc = self.classes(primary_models)
        secondary_models = []
        for model in self.generator.model_classes:
            if model in primary_models:
                continue
            secondary_models.append(model)
        secondary_models_doc = self.classes(secondary_models)
        response_models = list(self.generator.response_classes.keys())
        response_models_doc = self.classes(response_models)
        return f"""
{self.header}

Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.

{primary_models_doc}

Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.

{managers_doc}


Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.

{secondary_models_doc}

Request/Response Models
-----------------------

Request/response models are models that are used to describe the structure of
the data that is sent to and received from the AWS service. They are used by
the managers to send requests to the service and to parse the responses that
are received.

You will not often use them directly -- typically they are used by the managers
internally to send requests and parse responses -- but they are included here
for completeness, and because occasionally we return them directly to you
because they have some useful additional information.

{response_models_doc}
"""

    def write(self) -> None:
        """
        Write the generated docs to the output file, and format it with black,
        isort, and docformatter.

        Args:
            code: the code to write to the output file.

        """
        # First format the code with black so we fix most of the formatting
        # issues.
        with self.path.open("w", encoding="utf-8") as fd:
            fd.write(self.body)
