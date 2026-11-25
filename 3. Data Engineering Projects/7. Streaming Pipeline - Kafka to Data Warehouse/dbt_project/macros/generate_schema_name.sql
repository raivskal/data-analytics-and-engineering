{#
    Use the custom schema name verbatim instead of dbt's default
    "<target.schema>_<custom>" concatenation, so models land in the schemas the
    loader and the README talk about: staging, marts, snapshots.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
