{% macro synapse__create_view_as(relation, sql) %}
  CREATE OR ALTER VIEW {{ relation.schema }}.{{ relation.identifier }} AS
    {{ sql }}
{% endmacro %}

{% macro synapse__rename_relation(from_relation, to_relation) %}
  {# Synapse Serverless does not support RENAME — no-op for views #}
{% endmacro %}
